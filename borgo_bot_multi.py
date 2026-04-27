"""
Borgo-Bot v3.6 - Multi-Bot Architektur
DREI logisch getrennte Bots in EINER Instanz
Strikte Isolation basierend auf Signal group_id
"""

import asyncio
import logging
from collections import defaultdict
from pathlib import Path
from time import monotonic
from typing import Optional

# Multi-Bot Config
from config_multi_bot import (
    BOT_VERSION,
    BOT_COMMAND_PREFIX,
    GROUP_IDS,
    ALLOWED_GROUP_IDS,
    DEV_BOT_CONFIG,
    TEST_BOT_CONFIG,
    COMMUNITY_TEST_BOT_CONFIG,
    get_bot_config,
    get_bot_name_for_group,
    is_allowed_group,
    LOG_FILE,
)

from signal_interface import SignalInterface
from kb_manager import KBManager
from message_deduplication import MessageDeduplicator

# ── Approval System ───────────────────────────────────────────────────────────
from approval_handler import is_approval_command, handle_approval_command

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Begrenzt Anfragen pro Absender (sliding window)."""

    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._timestamps: dict = defaultdict(list)

    def is_allowed(self, sender: str) -> bool:
        now = monotonic()
        ts = self._timestamps[sender]
        # Alte Einträge außerhalb des Fensters entfernen
        self._timestamps[sender] = [t for t in ts if now - t < self.window]
        if len(self._timestamps[sender]) >= self.max_requests:
            return False
        self._timestamps[sender].append(now)
        return True


class BorgoBotInstance:
    """
    Einzelne Bot-Instanz mit spezifischer Konfiguration
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.name = config['name']
        
        logger.info(f"🤖 Initializing {self.name}...")
        
        from input_validator import InputValidator, QuickResponder
        from keyword_extractor import KeywordExtractor, CategoryMatcher
        from context_manager import ContextManager, ContextValidator
        from llm_handler import LLMHandler, ResponseFormatter
        from fallback_system import FallbackSystem, ResponseQualityChecker
        from monitoring import MonitoringSystem
        
        self.input_validator = InputValidator()
        self.quick_responder = QuickResponder()
        self.context_manager = ContextManager(Path(config['yaml_path']))
        self.keyword_extractor = KeywordExtractor(
            self.context_manager.get_available_keywords()
        )
        self.category_matcher = CategoryMatcher()
        
        self.llm_handler = LLMHandler(
            ollama_url=config['ollama_url']
        )
        self.llm_handler.models = config['llm_models']
        self.llm_handler.primary_model = config['primary_model']
        
        self.response_formatter = ResponseFormatter()
        self.fallback_system = FallbackSystem()
        self.quality_checker = ResponseQualityChecker()
        self.monitoring = MonitoringSystem()
        self.context_validator = ContextValidator()
        
        self.features = config['features']
        
        logger.info(f"✅ {self.name} initialized")
    
    async def process_message(self, message: str, user_id: Optional[str] = None):
        from datetime import datetime
        from monitoring import InteractionLog
        from fallback_system import FallbackReason
        
        start_time = datetime.now()
        logger.info(f"📨 [{self.name}] Processing: '{message[:50]}...'")
        
        log_entry = InteractionLog(
            timestamp=start_time.isoformat(),
            query=message,
            query_length=len(message),
            keywords_found=[],
            keywords_confidence='none',
            context_entries=0,
            context_words=0,
            model_used=None,
            response_length=0,
            response_time_ms=0,
            validation_issues=[],
            fallback_used=False,
            fallback_reason=None,
            success=False
        )
        
        try:
            # PHASE 1: Input Validation
            if self.features['input_validation']:
                cleaned_message, error = self.input_validator.validate(message)
                
                if error:
                    logger.warning(f"❌ Input validation failed: {error}")
                    log_entry.fallback_used = True
                    log_entry.fallback_reason = 'invalid_input'
                    self._finalize_log(log_entry, error, start_time)
                    return error, False
                
                quick_response = self.quick_responder.get_quick_response(cleaned_message)
                if quick_response:
                    logger.info("⚡ Quick response triggered")
                    log_entry.success = True
                    self._finalize_log(log_entry, quick_response, start_time)
                    return quick_response, True
                
                message = cleaned_message
            
            # PHASE 1.5: Meta-Query Check
            from config_multi_bot import is_meta_query, FALLBACK_RESPONSES
            if is_meta_query(message):
                logger.info(f"🎭 Meta-query detected: {message[:50]}")
                response = FALLBACK_RESPONSES['meta_query']
                log_entry.success = True
                log_entry.fallback_used = True
                log_entry.fallback_reason = 'meta_query'
                self._finalize_log(log_entry, response, start_time)
                return response, True
            
            # PHASE 2: Keyword Extraction
            if self.features['keyword_confidence_scoring']:
                extraction = self.keyword_extractor.extract(message)
                keywords = self.keyword_extractor.get_best_keywords(extraction, max_keywords=3)
                
                log_entry.keywords_found = keywords
                log_entry.keywords_confidence = extraction['confidence_level']
                
                logger.info(f"🔍 Keywords: {keywords} (confidence: {extraction['confidence_level']})")
            else:
                keywords = []
            
            # PHASE 3: Context Building
            if keywords and self.features['context_isolation']:
                context, context_meta = self.context_manager.build_context(keywords, message)
                log_entry.context_entries = context_meta['total_entries']
                log_entry.context_words = context_meta['total_words']
            elif not keywords:
                category = self.category_matcher.find_category(message)
                context = self.context_manager.get_fallback_context(category)
                logger.info(f"📁 Using fallback context (category: {category})")
            else:
                context = None
            
            # PHASE 4: LLM Generation
            if context and self.features['multi_model_fallback']:
                response, llm_meta = await self.llm_handler.generate_response(message, context)
                
                log_entry.model_used = llm_meta.get('final_model')
                log_entry.validation_issues = llm_meta.get('validation_issues', [])
                
                if response:
                    if self.quality_checker.is_helpful(response, message):
                        if self.features['response_validation']:
                            response = self.response_formatter.format(response)
                        
                        log_entry.success = True
                        log_entry.response_length = len(response)
                        self._finalize_log(log_entry, response, start_time)
                        
                        logger.info(f"✅ Generated response ({len(response)} chars)")
                        return response, True
                    else:
                        logger.warning("⚠️ Response not helpful enough")
                        response = None
            
            # PHASE 5: Fallback
            log_entry.fallback_used = True
            
            if not keywords:
                reason = FallbackReason.NO_KEYWORDS
            elif not context:
                reason = FallbackReason.AMBIGUOUS
            elif log_entry.validation_issues:
                reason = FallbackReason.VALIDATION_FAILED
            else:
                reason = FallbackReason.LLM_ERROR
            
            log_entry.fallback_reason = reason.value
            response = self.fallback_system.get_fallback_response(reason, message)
            
            log_entry.response_length = len(response)
            self._finalize_log(log_entry, response, start_time)
            
            logger.warning(f"⚠️ Using fallback: {reason.value}")
            return response, False
        
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            
            log_entry.fallback_used = True
            log_entry.fallback_reason = 'system_error'
            
            response = self.fallback_system.get_fallback_response(
                FallbackReason.UNKNOWN, message, {'error': str(e)}
            )
            
            self._finalize_log(log_entry, response, start_time)
            return response, False
    
    def _finalize_log(self, log_entry, response: str, start_time):
        from datetime import datetime
        
        duration = (datetime.now() - start_time).total_seconds() * 1000
        log_entry.response_time_ms = duration
        log_entry.response_length = len(response)
        
        if self.features.get('detailed_logging', True):
            self.monitoring.log_interaction(log_entry)


async def multi_bot_signal_loop():
    """
    Hauptschleife mit DREI getrennten Bot-Instanzen
    Routet Messages basierend auf group_id
    """
    logger.info("=" * 80)
    logger.info(f"🚀 Starting Borgo-Bot v{BOT_VERSION} MULTI-BOT System")
    logger.info("=" * 80)

    unique_ids = set(GROUP_IDS.values())
    placeholder_ids = {v for v in GROUP_IDS.values() if 'EINTRAGEN' in v}
    if len(unique_ids) < len(GROUP_IDS):
        logger.error("❌ KONFIGURATIONSFEHLER: Mehrere Bots haben dieselbe group_id!")
        raise SystemExit(1)
    if placeholder_ids:
        logger.error("❌ KONFIGURATIONSFEHLER: Platzhalter-IDs gefunden — bitte ersetzen:")
        for key, val in GROUP_IDS.items():
            if 'EINTRAGEN' in val:
                logger.error(f"   GROUP_IDS['{key}'] = '{val}'")
        raise SystemExit(1)

    kb_manager = KBManager(Path(DEV_BOT_CONFIG['yaml_path']))
    logger.info("✅ KBManager initialisiert")

    si = SignalInterface(group_id=None)
    deduplicator = MessageDeduplicator(ttl_seconds=300)
    rate_limiter = RateLimiter(max_requests=5, window_seconds=60)
    
    logger.info("\n🤖 Initializing Bot Instances...")
    
    dev_bot = BorgoBotInstance(DEV_BOT_CONFIG)
    test_bot = BorgoBotInstance(TEST_BOT_CONFIG)
    community_test_bot = BorgoBotInstance(COMMUNITY_TEST_BOT_CONFIG)
    
    logger.info("\n📋 Bot → Group Mapping:")
    logger.info(f"   {dev_bot.name:20} → DEV Group")
    logger.info(f"   {test_bot.name:20} → TEST Group")
    logger.info(f"   {community_test_bot.name:20} → Community-Test Group")
    
    logger.info("\n✅ All bots initialized. Listening for messages...")
    logger.info("=" * 80 + "\n")
    
    async def handler(text: str, sender: str, group_id: str):
        """
        Message Handler mit striktem Group-Routing
        """
        # ── Approval-Befehle (Admin-DM, keine Gruppe) ────────────────────────
        if not group_id and is_approval_command(text, sender):
            logger.info(f"🔐 Approval-Befehl von Admin: {text[:40]}")
            response = handle_approval_command(text, sender)
            await si.send(response, recipient=sender)
            return

        # !kb Kommandos (nur in DEV-Gruppe)
        if text.strip().lower().startswith("!kb"):
            if group_id == GROUP_IDS['dev']:
                logger.info(f"📚 KB-Kommando von {sender[:10]}...: {text[:60]}")
                response = kb_manager.handle(text)
                await si.send(response, group_id=group_id)
            else:
                logger.info(f"⛔ !kb nur in DEV erlaubt, ignoriere aus Gruppe {group_id[:20]}...")
            return

        # Nur auf !bot Kommandos reagieren
        if not text.lower().startswith(BOT_COMMAND_PREFIX):
            return
        
        # STRIKTE VALIDIERUNG: Nur erlaubte Gruppen
        if not is_allowed_group(group_id):
            logger.warning(f"⛔ Message from unauthorized group: {str(group_id)[:20]}... - IGNORING")
            return
        
        # Deduplizierung
        if deduplicator.is_duplicate(text, sender):
            logger.info(f"⏭️  Skipping duplicate message from {sender}")
            return

        # Rate-Limiting
        if not rate_limiter.is_allowed(sender):
            logger.warning(f"⛔ Rate limit exceeded for {sender[:15]}... — message dropped")
            return
        
        # ROUTING basierend auf group_id
        bot_name = get_bot_name_for_group(group_id)
        logger.info(f"💬 [{bot_name}] Incoming from {sender[:10]}... in group {group_id[:20]}...")
        
        if group_id == GROUP_IDS['dev']:
            bot = dev_bot
        elif group_id == GROUP_IDS['test']:
            bot = test_bot
        elif group_id == GROUP_IDS['community_test']:
            bot = community_test_bot
        else:
            logger.error(f"❌ Unknown group_id: {group_id} - This should never happen!")
            return
        
        try:
            response, success = await bot.process_message(text, sender)
            await si.send(response, group_id=group_id)
            
            status = "✅ SUCCESS" if success else "⚠️ FALLBACK"
            logger.info(f"📤 [{bot_name}] Sent response ({status}) to group {group_id[:20]}...")
            
        except Exception as e:
            logger.error(f"❌ [{bot_name}] Error processing message: {e}", exc_info=True)
    
    await si.run_listener(handler)


if __name__ == "__main__":
    import sys
    asyncio.run(multi_bot_signal_loop())
