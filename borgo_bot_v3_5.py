"""
Borgo-Bot v3.5 - Hauptmodul
Integriert alle Komponenten für robustes Bot-System
JETZT ERWEITERT UM: PRODUKTIONSMODUS + SIGNAL-LISTENER
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict
from pathlib import Path

# Eigene Module
from config import (
    BOT_VERSION,
    BOT_NAME,
    BOT_COMMAND_PREFIX,
    PRIMARY_MODEL,
    FEATURES
)
from input_validator import InputValidator, QuickResponder
from keyword_extractor import KeywordExtractor, CategoryMatcher
from context_manager import ContextManager, ContextValidator
from llm_handler import LLMHandler, ResponseFormatter
from fallback_system import FallbackSystem, FallbackReason, ResponseQualityChecker
from monitoring import MonitoringSystem, InteractionLog

# Optional: Signal-Schnittstelle (separates Modul)
try:
    from signal_interface import SignalInterface
except ImportError:
    SignalInterface = None  # Ermöglicht CLI/Test auch ohne Signal-Modul

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('borgo_bot_v3_5.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BorgoBot:
    """
    Borgo-Bot v3.5 - Hauptklasse
    Koordiniert alle Komponenten für robuste Bot-Funktionalität
    """
    
    def __init__(
        self,
        yaml_path: Path = Path("borgo_knowledge_base.yaml"),
        ollama_url: str = "http://localhost:11434",
        signal_interface: "SignalInterface | None" = None,
    ):
        """
        Initialisiert Bot mit allen Komponenten
        
        Args:
            yaml_path: Pfad zur YAML Knowledge Base
            ollama_url: URL zum Ollama Server
            signal_interface: Optionale Signal-Schnittstelle für Livebetrieb
        """
        logger.info(f"🤖 Initializing Borgo-Bot v{BOT_VERSION}...")
        
        # Komponenten initialisieren
        self.input_validator = InputValidator()
        self.quick_responder = QuickResponder()
        self.context_manager = ContextManager(yaml_path)
        self.keyword_extractor = KeywordExtractor(
            self.context_manager.get_available_keywords()
        )
        self.category_matcher = CategoryMatcher()
        self.llm_handler = LLMHandler(ollama_url)
        self.response_formatter = ResponseFormatter()
        self.fallback_system = FallbackSystem()
        self.quality_checker = ResponseQualityChecker()
        self.monitoring = MonitoringSystem()
        self.context_validator = ContextValidator()
        
        # Load previous metrics if available
        self.monitoring.load_metrics()

        # Optionale Signal-Integration
        self.signal = signal_interface
        
        logger.info(f"✅ Borgo-Bot v{BOT_VERSION} initialized successfully")
        self._print_feature_status()
    
    def _print_feature_status(self):
        """Zeigt aktivierte Features"""
        enabled_features = [name for name, enabled in FEATURES.items() if enabled]
        logger.info(f"📋 Active Features ({len(enabled_features)}):")
        for feature in enabled_features:
            logger.info(f"   ✓ {feature}")
    
    async def process_message(
        self,
        message: str,
        user_id: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Verarbeitet eingehende Nachricht
        
        Args:
            message: User-Nachricht
            user_id: Optional User-ID für Tracking
        
        Returns:
            (response, success)
        """
        start_time = datetime.now()
        
        logger.info(f"📨 Processing message: '{message[:50]}...'")
        
        # Initialisiere Log Entry
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
            # === PHASE 1: INPUT VALIDATION ===
            if FEATURES['input_validation']:
                cleaned_message, error = self.input_validator.validate(message)
                
                if error:
                    logger.warning(f"❌ Input validation failed: {error}")
                    log_entry.fallback_used = True
                    log_entry.fallback_reason = 'invalid_input'
                    response = error
                    self._finalize_log_entry(log_entry, response, start_time)
                    return response, False
                
                # Quick Response Check
                quick_response = self.quick_responder.get_quick_response(cleaned_message)
                if quick_response:
                    logger.info("⚡ Quick response triggered")
                    log_entry.success = True
                    self._finalize_log_entry(log_entry, quick_response, start_time)
                    return quick_response, True
                
                message = cleaned_message
            
            # === PHASE 2: KEYWORD EXTRACTION ===
            if FEATURES['keyword_confidence_scoring']:
                extraction = self.keyword_extractor.extract(message)
                keywords = self.keyword_extractor.get_best_keywords(extraction, max_keywords=3)
                
                log_entry.keywords_found = keywords
                log_entry.keywords_confidence = extraction['confidence_level']
                
                logger.info(f"🔍 Keywords: {keywords} (confidence: {extraction['confidence_level']})")
            else:
                # Fallback: Simple Keyword Extraction (alte Methode)
                keywords = []
            
            # === PHASE 3: CONTEXT BUILDING ===
            if keywords and FEATURES['context_isolation']:
                context, context_meta = self.context_manager.build_context(
                    keywords, message
                )
                
                log_entry.context_entries = context_meta['total_entries']
                log_entry.context_words = context_meta['total_words']
                
                # Context Validation
                is_valid, issues = self.context_validator.validate(context, context_meta)
                if not is_valid:
                    logger.warning(f"⚠️ Context validation issues: {issues}")
            
            elif not keywords:
                # Keine Keywords -> Fallback Context oder Category-basiert
                category = self.category_matcher.find_category(message)
                context = self.context_manager.get_fallback_context(category)
                logger.info(f"📁 Using fallback context (category: {category})")
            else:
                context = None
            
            # === PHASE 4: LLM GENERATION ===
            if context and FEATURES['multi_model_fallback']:
                response, llm_meta = await self.llm_handler.generate_response(
                    message, context
                )
                
                log_entry.model_used = llm_meta.get('final_model')
                log_entry.validation_issues = llm_meta.get('validation_issues', [])
                
                if response:
                    # Response Quality Check
                    if self.quality_checker.is_helpful(response, message):
                        # Format Response
                        if FEATURES['response_validation']:
                            response = self.response_formatter.format(response)
                        
                        log_entry.success = True
                        log_entry.response_length = len(response)
                        self._finalize_log_entry(log_entry, response, start_time)
                        
                        logger.info(f"✅ Generated response ({len(response)} chars)")
                        return response, True
                    else:
                        logger.warning("⚠️ Response not helpful enough, using fallback")
                        response = None  # Trigger Fallback
            
            # === PHASE 5: FALLBACK ===
            # Wenn wir hier ankommen: Fallback nötig
            log_entry.fallback_used = True
            
            # Bestimme Fallback-Grund
            if not keywords:
                reason = FallbackReason.NO_KEYWORDS
            elif not context:
                reason = FallbackReason.AMBIGUOUS
            elif log_entry.validation_issues:
                reason = FallbackReason.VALIDATION_FAILED
            else:
                reason = FallbackReason.LLM_ERROR
            
            log_entry.fallback_reason = reason.value
            
            response = self.fallback_system.get_fallback_response(
                reason, message
            )
            
            log_entry.response_length = len(response)
            self._finalize_log_entry(log_entry, response, start_time)
            
            logger.warning(f"⚠️ Using fallback: {reason.value}")
            return response, False
        
        except Exception as e:
            # Unerwarteter Fehler
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)
            
            log_entry.fallback_used = True
            log_entry.fallback_reason = 'system_error'
            
            response = self.fallback_system.get_fallback_response(
                FallbackReason.UNKNOWN,
                message,
                {'error': str(e)}
            )
            
            self._finalize_log_entry(log_entry, response, start_time)
            return response, False
    
    def _finalize_log_entry(
        self,
        log_entry: InteractionLog,
        response: str,
        start_time: datetime
    ):
        """Finalisiert Log Entry und logged zu Monitoring"""
        duration = (datetime.now() - start_time).total_seconds() * 1000
        log_entry.response_time_ms = duration
        log_entry.response_length = len(response)
        
        if FEATURES['detailed_logging']:
            self.monitoring.log_interaction(log_entry)
    
    def get_stats(self) -> Dict:
        """Sammelt Statistiken von allen Komponenten"""
        return {
            'bot_version': BOT_VERSION,
            'bot_name': BOT_NAME,
            'input_validator': self.input_validator.get_stats(),
            'keyword_extractor': self.keyword_extractor.get_stats(),
            'context_manager': self.context_manager.get_stats(),
            'llm_handler': self.llm_handler.get_stats(),
            'fallback_system': self.fallback_system.get_stats(),
            'monitoring': self.monitoring.get_metrics(),
        }
    
    def generate_report(self) -> str:
        """Generiert umfassenden Status-Report"""
        lines = [
            "=" * 80,
            f"BORGO-BOT v{BOT_VERSION} STATUS REPORT",
            "=" * 80,
            "",
            self.monitoring.generate_summary_report(),
            "",
            "## COMPONENT STATISTICS ##",
            ""
        ]
        
        stats = self.get_stats()
        for component, component_stats in stats.items():
            if component not in ['bot_version', 'bot_name']:
                lines.append(f"\n{component.upper().replace('_', ' ')}:")
                if isinstance(component_stats, dict):
                    for key, value in component_stats.items():
                        if isinstance(value, (int, float)):
                            lines.append(f"  {key}: {value}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def reload_knowledge_base(self) -> bool:
        """Lädt Knowledge Base neu"""
        success = self.context_manager.reload_knowledge_base()
        if success:
            # Update Keyword Extractor mit neuen Keywords
            self.keyword_extractor = KeywordExtractor(
                self.context_manager.get_available_keywords()
            )
            logger.info("✅ Knowledge base reloaded")
        return success

    # ====================================================================================
    # SIGNAL LISTENER – PRODUKTIONSMODUS
    # ====================================================================================

    async def run_signal_listener(self):
        """
        Wartet auf Nachrichten aus der Signal-Schnittstelle und beantwortet sie.
        Erwartet, dass self.signal ein Objekt mit:
          - async def listen(): Async-Iterator von {"text": str, "sender": str, "group_id": str}
          - async def send(text: str, group_id: str | None = None)
        bereitstellt.
        """
        if self.signal is None:
            logger.error("❌ Kein SignalInterface konfiguriert – Livebetrieb nicht möglich.")
            return
        
        logger.info("📡 Starting Signal listener…")
        
        async for msg in self.signal.listen():
            text = msg.get("text") or ""
            sender = msg.get("sender")
            group_id = msg.get("group_id")
            
            if not text:
                continue
            
            # Nur auf Kommandos mit BOT_COMMAND_PREFIX reagieren
            if not text.lower().startswith(BOT_COMMAND_PREFIX):
                continue
            
            logger.info(f"💬 Incoming from {sender} in {group_id}: {text}")
            
            response, success = await self.process_message(text, sender)
            
            try:
                await self.signal.send(response, group_id=group_id)
                logger.info(f"📤 Sent response ({'success' if success else 'fallback'})")
            except Exception as e:
                logger.error(f"❌ Fehler beim Senden über SignalInterface: {e}", exc_info=True)


# ========================================
# CLI INTERFACE
# ========================================

async def interactive_cli():
    """Interaktive Kommandozeile für Tests"""
    bot = BorgoBot()
    
    print("=" * 80)
    print(f"🤖 {BOT_NAME} v{BOT_VERSION} - Interactive CLI")
    print("=" * 80)
    print()
    print("Commands:")
    print("  !quit     - Exit")
    print("  !stats    - Show statistics")
    print("  !report   - Generate full report")
    print("  !reload   - Reload knowledge base")
    print()
    print("Type your questions (prefix with '!bot' optional)")
    print("=" * 80)
    print()
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if not user_input:
                continue
            
            # Spezial-Commands (erkenne am Anfang)
            if user_input.startswith("!quit"):
                print("\n👋 Goodbye!")
                break
            
            elif user_input.startswith("!stats"):
                stats = bot.get_stats()
                print("\n📊 STATISTICS:")
                print(f"Monitoring: {stats['monitoring']}")
                continue
            
            elif user_input.startswith("!report"):
                report = bot.generate_report()
                print("\n" + report)
                continue
            
            elif user_input.startswith("!reload"):
                success = bot.reload_knowledge_base()
                if success:
                    print("✅ Knowledge base reloaded")
                else:
                    print("❌ Failed to reload knowledge base")
                continue
            
            # Normale Message Processing
            if not user_input.startswith(BOT_COMMAND_PREFIX):
                user_input = f"{BOT_COMMAND_PREFIX} {user_input}"
            
            response, success = await bot.process_message(user_input)
            
            # Response mit Status
            status_icon = "✅" if success else "⚠️"
            print(f"\n{status_icon} {BOT_NAME}: {response}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        
        except Exception as e:
            print(f"\n❌ Error: {e}")


# ========================================
# MAIN
# ========================================

async def main():
    """Hauptfunktion
    Modi:
      --cli   -> Interaktive CLI
      --test  -> Lokaler Testlauf mit Beispiel-Queries
      (ohne)  -> PRODUKTIONSMODUS: Signal Listener
    """
    import sys
    
    # CLI-Modus erzwingen
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        await interactive_cli()
        return
    
    # Testmodus explizit
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        bot = BorgoBot()
        
        print("=" * 80)
        print(f"🧪 Testing {BOT_NAME} v{BOT_VERSION}")
        print("=" * 80)
        
        test_queries = [
            "Wie viel Mehl für 24 Personen Pizza?",
            "Ich habe eine Schlange gesehen",
            "Sind Hunde erlaubt?",
            "???",  # Sollte Fallback triggern
            "Blablabla nonsense",  # Sollte no_keywords triggern
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: '{query}'")
            response, success = await bot.process_message(f"{BOT_COMMAND_PREFIX} {query}")
            
            status = "✅ SUCCESS" if success else "⚠️ FALLBACK"
            print(f"   {status}")
            print(f"   Response: {response[:100]}...")
            print("   " + "-" * 76)
        
        # Final Report
        print("\n\n" + bot.generate_report())
        return
    
    # PRODUKTIONSMODUS: Signal Listener
    if SignalInterface is None:
        logger.error("❌ SignalInterface konnte nicht importiert werden – beende.")
        return
    
    # Instanz mit SignalInterface erstellen
    signal_if = SignalInterface()
    bot = BorgoBot(signal_interface=signal_if)
    
    logger.info("🚀 Starte Borgo-Bot v3.5 im PRODUKTIONSMODUS (Signal Listener aktiv)")
    await bot.run_signal_listener()


from signal_interface import SignalInterface

async def signal_loop():
    bot = BorgoBot()
    si = SignalInterface()

    async def handler(text: str, sender: str, group_id: str):
        # Nur Nachrichten verarbeiten, die mit !bot beginnen
        if not text.lower().startswith("!bot"):
            return

        # Bot-Antwort generieren
        response, success = await bot.process_message(text)

        # Antwort in die Gruppe schicken
        await si.send(response, group_id)

    await si.run_listener(handler)


if __name__ == "__main__":
    import sys

    # CLI-Modus
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        asyncio.run(interactive_cli())

    # Produktionsmodus → Signal-Listener
    else:
        asyncio.run(signal_loop())