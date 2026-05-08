"""
Borgo-Bot v3.5 - LLM Handler
Phase 4: Multi-Model-Fallback und Response-Validierung
"""

import re
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import aiohttp

from config_multi_bot import (
    LLM_MODELS,
    PRIMARY_MODEL,
    MAX_LLM_RETRIES,
    LLM_TIMEOUT_SECONDS,
    HALLUCINATION_PATTERNS,
    CONTEXT_MIXING_RULES,
    MIN_RESPONSE_LENGTH,
    MAX_RESPONSE_LENGTH,
    QUALITY_CHECKS
)

logger = logging.getLogger(__name__)


class LLMHandler:
    """
    Verwaltet LLM-Anfragen mit Fallback und Validierung
    Erkennt Halluzinationen und Context-Mixing
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        # Models als Instance-Variable (können von außen überschrieben werden)
        self.models = LLM_MODELS
        self.primary_model = PRIMARY_MODEL
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retries_used': 0,
            'hallucinations_detected': 0,
            'context_mixing_detected': 0,
            'model_usage': {model: 0 for model in self.models},
        }
    
    async def generate_response(
        self,
        query: str,
        context: str,
        max_retries: int = MAX_LLM_RETRIES
    ) -> Tuple[Optional[str], Dict]:
        """
        Generiert LLM-Response mit Fallback und Validierung
        
        Args:
            query: User-Query
            context: Vorbereiteter Context
            max_retries: Max Retry-Versuche
        
        Returns:
            (response, metadata)
        """
        self.stats['total_requests'] += 1
        
        start_time = datetime.now()
        metadata = {
            'attempts': [],
            'final_model': None,
            'validation_issues': [],
            'processing_time_ms': 0,
        }
        
        # Versuche Modelle der Reihe nach
        for attempt, model in enumerate(self.models[:max_retries + 1]):
            try:
                logger.info(f"🤖 Attempt {attempt + 1}: Using model '{model}'")
                
                # LLM-Call
                response = await self._call_ollama(query, context, model)
                
                # Validierung
                is_valid, issues = self._validate_response(response, query)
                
                attempt_data = {
                    'model': model,
                    'success': is_valid,
                    'issues': issues,
                    'response_length': len(response) if response else 0,
                }
                metadata['attempts'].append(attempt_data)
                
                if is_valid:
                    # Erfolg!
                    self.stats['successful_requests'] += 1
                    self.stats['model_usage'][model] = self.stats['model_usage'].get(model, 0) + 1
                    metadata['final_model'] = model
                    
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    metadata['processing_time_ms'] = round(duration, 2)
                    
                    logger.info(f"✅ Valid response from '{model}' ({duration:.0f}ms)")
                    return response, metadata
                else:
                    # Validierung fehlgeschlagen
                    logger.warning(f"❌ Invalid response from '{model}': {issues}")
                    self.stats['retries_used'] += 1
                    
                    # Zähle spezifische Issues
                    for issue in issues:
                        if 'hallucination' in issue.lower():
                            self.stats['hallucinations_detected'] += 1
                        if 'context_mixing' in issue.lower():
                            self.stats['context_mixing_detected'] += 1
            
            except Exception as e:
                logger.error(f"❌ Model '{model}' failed: {e}", exc_info=True)
                metadata['attempts'].append({
                    'model': model,
                    'success': False,
                    'error': str(e),
                })
                continue
        
        # Alle Modelle gescheitert
        self.stats['failed_requests'] += 1
        metadata['validation_issues'] = ['All models failed or produced invalid responses']
        
        duration = (datetime.now() - start_time).total_seconds() * 1000
        metadata['processing_time_ms'] = round(duration, 2)
        
        logger.error(f"❌ All models failed after {len(metadata['attempts'])} attempts")
        return None, metadata
    
    async def _call_ollama(
        self,
        query: str,
        context: str,
        model: str
    ) -> str:
        """
        Ruft Ollama API auf
        
        Returns:
            LLM-Response als String
        """
        prompt = self._build_prompt(query, context, model)
        
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.3,  # Niedrig für präzise Antworten
                'top_p': 0.9,
                'top_k': 40,
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=LLM_TIMEOUT_SECONDS)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data.get('response', '').strip()
                        
                        logger.info(f"LLM response length: {len(response)} chars")
                        logger.debug(f"🔍 LLM RESPONSE: {response[:500]}")
                        return response
                    else:
                        error_text = await resp.text()
                        raise Exception(f"Ollama API error {resp.status}: {error_text}")
        
        except asyncio.TimeoutError:
            raise Exception(f"Timeout after {LLM_TIMEOUT_SECONDS}s")
        except Exception as e:
            raise Exception(f"Ollama call failed: {e}")
    
    def _build_prompt(self, query: str, context: str, model: str = None) -> str:
        """Baut LLM-Prompt aus Query und Context"""
        
        # Für qwen-Modelle: Explizit Deutsch verlangen!
        language_instruction = ""
        if model and 'qwen' in model.lower():
            language_instruction = "WICHTIG: Antworte ausschließlich auf Deutsch!\n\n"
        
        prompt_parts = [
            language_instruction,
            # REGELN ZUERST (als Meta-Instruktion)
            "Du bist Borgo-Bot, der hilfreiche Borgo Batone Gäste-Assistent.",
            "",
            "KRITISCHE REGEL - WORD-FOR-WORD REPRODUCTION:",
            "• Kopiere Texte aus der Knowledge Base EXAKT - Wort für Wort",
            "• KEINE Paraphrasierung, KEINE Umformulierung, KEINE eigenen Worte",
            "• Übernimm Listen, Nummerierungen, Links GENAU wie vorgegeben",
            "• Wenn Informationen fehlen: Sage 'Dazu habe ich keine Informationen'",
            "• Erfinde NIEMALS Details, Zahlen, Einheiten oder Formulierungen",
            "",
            "---",
            "",
            "# KNOWLEDGE BASE",
            "",
            context,
            "",
            "---",
            "",
            "# FRAGE",
            query,
            "",
            "# ANTWORT",
            "(Gib NUR die relevanten Informationen aus der Knowledge Base, NICHT die Anweisungen oben)",
            "",
        ]
        
        # Entferne leere Strings am Anfang wenn language_instruction leer ist
        if not language_instruction:
            prompt_parts = prompt_parts[1:]
        
        return "\n".join(prompt_parts)
    
    def _validate_response(
        self,
        response: str,
        query: str
    ) -> Tuple[bool, List[str]]:
        """
        Validiert LLM-Response auf Qualität
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        if not response:
            issues.append("Empty response")
            return False, issues
        
        # Check 1: Länge
        if QUALITY_CHECKS.get('too_short'):
            if len(response) < MIN_RESPONSE_LENGTH:
                issues.append(f"Too short ({len(response)} chars)")
        
        if QUALITY_CHECKS.get('too_long'):
            if len(response) > MAX_RESPONSE_LENGTH:
                issues.append(f"Too long ({len(response)} chars)")
        
        # Check 2: Halluzinationen
        if QUALITY_CHECKS.get('hallucination'):
            hallucination_found = self._check_hallucinations(response)
            if hallucination_found:
                issues.append(f"Hallucination detected: {hallucination_found}")
        
        # Check 3: Context-Mixing
        if QUALITY_CHECKS.get('context_mixing'):
            mixing_found = self._check_context_mixing(response, query)
            if mixing_found:
                issues.append(f"Context mixing: {mixing_found}")
        
        # Check 4: Unvollständige Antwort
        if QUALITY_CHECKS.get('incomplete'):
            if self._is_incomplete(response):
                issues.append("Incomplete response")
        
        # Check 5: System Prompt Leakage (NEU!)
        if self._has_prompt_leakage(response):
            issues.append("System prompt leaked in response")
        
        is_valid = len(issues) == 0
        
        return is_valid, issues
    
    def _has_prompt_leakage(self, response: str) -> bool:
        """
        Prüft ob System-Instruktionen in Response durchgesickert sind
        
        Returns:
            True wenn Prompt-Leakage erkannt wurde
        """
        leakage_patterns = [
            r'KRITISCHE REGELN',
            r'ANWEISUNGEN.*befolge',
            r'gib.*NICHT.*in deiner Antwort wieder',
            r'Du bist.*Assistent.*befolge',
            r'KNOWLEDGE BASE',
            r'# FRAGE',
            r'# ANTWORT',
        ]
        
        for pattern in leakage_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                logger.warning(f"⚠️ Prompt leakage detected: '{pattern}'")
                return True
        
        return False
    
    def _check_hallucinations(self, response: str) -> Optional[str]:
        """
        Prüft auf bekannte Halluzinations-Muster
        
        Returns:
            Beschreibung der Halluzination oder None
        """
        for pattern, description in HALLUCINATION_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                logger.warning(f"Hallucination pattern found: {description}")
                return description
        
        return None
    
    def _check_context_mixing(
        self,
        response: str,
        query: str
    ) -> Optional[str]:
        """
        Prüft auf Context-Mixing (z.B. Pizza + Rasenmäher)
        
        Returns:
            Beschreibung des Mixings oder None
        """
        response_lower = response.lower()
        query_lower = query.lower()
        
        for topic, forbidden_words in CONTEXT_MIXING_RULES.items():
            # Wenn Query zu diesem Topic gehört
            if topic in query_lower:
                # Prüfe ob forbidden words in Response sind
                for forbidden in forbidden_words:
                    if forbidden in response_lower:
                        mixing = f"Topic '{topic}' mixed with '{forbidden}'"
                        logger.warning(f"Context mixing detected: {mixing}")
                        return mixing
        
        return None
    
    def _is_incomplete(self, response: str) -> bool:
        """
        Prüft ob Antwort unvollständig wirkt
        """
        incomplete_patterns = [
            r'\.\.\.$',  # Endet mit "..."
            r'\b(und|oder|bzw|etc)\s*$',  # Endet mit Bindewort
            r'\baber\s*$',  # Endet mit "aber"
        ]
        
        for pattern in incomplete_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return True
        
        return False
    
    def get_stats(self) -> Dict:
        """Gibt LLM-Handler Statistiken zurück"""
        total = self.stats['total_requests']
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'success_rate_percent': round(
                (self.stats['successful_requests'] / total) * 100, 2
            ),
            'failure_rate_percent': round(
                (self.stats['failed_requests'] / total) * 100, 2
            ),
            'avg_retries': round(
                self.stats['retries_used'] / total, 2
            ),
        }


class ResponseFormatter:
    """
    Formatiert und verbessert LLM-Responses
    Cleanup und Konsistenz
    """
    
    @staticmethod
    def format(response: str) -> str:
        """Formatiert Response für bessere Lesbarkeit"""
        
        # Entferne führende/trailing Whitespace
        response = response.strip()
        
        # Normalisiere Leerzeichen
        response = re.sub(r'\s+', ' ', response)
        
        # Stelle sicher dass Sätze mit Großbuchstaben starten
        response = ResponseFormatter._capitalize_sentences(response)
        
        # Füge Leerzeichen nach Satzzeichen hinzu falls fehlend
        response = re.sub(r'([.!?])([A-ZÄÖÜ])', r'\1 \2', response)
        
        return response
    
    @staticmethod
    def _capitalize_sentences(text: str) -> str:
        """Kapitalisiert Satzanfänge"""
        sentences = re.split(r'([.!?]\s+)', text)
        
        result = []
        for i, part in enumerate(sentences):
            if i % 2 == 0 and part:  # Nur Sätze, nicht Trenner
                # Ersten Buchstaben großschreiben
                part = part[0].upper() + part[1:] if len(part) > 1 else part.upper()
            result.append(part)
        
        return ''.join(result)
    
    @staticmethod
    def add_emoji(response: str, sentiment: str = 'neutral') -> str:
        """Fügt passende Emojis hinzu (optional)"""
        emoji_map = {
            'positive': '😊',
            'helpful': '👍',
            'warning': '⚠️',
            'safety': '🚨',
            'question': '❓',
        }
        
        if sentiment in emoji_map:
            return f"{response} {emoji_map[sentiment]}"
        
        return response


# ========================================
# TESTS
# ========================================

async def test_llm_handler():
    """Test-Suite für LLM Handler"""
    
    handler = LLMHandler()
    formatter = ResponseFormatter()
    
    # Mock-Context für Tests
    test_context = """
# BORGO BATONE KNOWLEDGE BASE

Du bist Borgo-Bot, der Borgo-Batone Gäste-Assistent.

## PIZZA

Für 24 Personen Pizza brauchst du 3 kg Mehl, 3 Würfel Hefe, 
3 große Flaschen Passata und 1,5 kg Mozzarella.

# WICHTIGE REGELN
1. Antworte NUR mit Informationen aus obigen Einträgen
2. Erfinde KEINE Zahlen oder Einheiten
    """
    
    test_queries = [
        "Wie viel Mehl für 24 Personen Pizza?",
        "Sind Hunde erlaubt?",  # Nicht im Context
    ]
    
    print("=" * 70)
    print("LLM HANDLER TESTS")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        
        try:
            # Generiere Response
            response, metadata = await handler.generate_response(
                query, test_context, max_retries=1
            )
            
            if response:
                # Formatiere
                formatted = formatter.format(response)
                
                print(f"\n✅ Response ({len(formatted)} chars):")
                print(f"   {formatted[:200]}...")
                print(f"\n   Model: {metadata['final_model']}")
                print(f"   Time: {metadata['processing_time_ms']}ms")
                print(f"   Attempts: {len(metadata['attempts'])}")
            else:
                print(f"\n❌ Failed to generate response")
                print(f"   Issues: {metadata['validation_issues']}")
                for attempt in metadata['attempts']:
                    print(f"   Attempt: {attempt}")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    # Statistiken
    print("\n" + "=" * 70)
    print("STATISTIKEN")
    print("=" * 70)
    stats = handler.get_stats()
    for key, value in stats.items():
        if key != 'model_usage':
            print(f"  {key}: {value}")
    
    print("\n  Model Usage:")
    for model, count in stats['model_usage'].items():
        print(f"    {model}: {count}")
    
    print("=" * 70)


if __name__ == "__main__":
    # Asyncio Event Loop für Tests
    asyncio.run(test_llm_handler())
