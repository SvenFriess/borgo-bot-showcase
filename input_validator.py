"""
Borgo-Bot v3.5 - Input Validator
Phase 1: Robuste Input-Validierung und Sanitization
"""

import re
import logging
from typing import Tuple, Optional, List, Dict
from config_multi_bot import (
    MIN_INPUT_LENGTH,
    MAX_INPUT_LENGTH,
    PROBLEMATIC_PATTERNS,
    BOT_COMMAND_PREFIX
)

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Validiert und bereinigt User-Eingaben
    Verhindert Spam, leere Anfragen und Probleminputs
    """
    
    def __init__(self):
        self.problematic_patterns = [re.compile(p) for p in PROBLEMATIC_PATTERNS]
        self.stats = {
            'total_validations': 0,
            'rejected_inputs': 0,
            'sanitized_inputs': 0,
        }
    
    def validate(self, message: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Hauptvalidierung der User-Eingabe
        
        Returns:
            Tuple[sanitized_message, error_message]
            - Wenn OK: (bereinigte_nachricht, None)
            - Wenn Fehler: (None, fehlermeldung)
        """
        self.stats['total_validations'] += 1
        
        # 1. Entferne Bot-Prefix
        cleaned = self._remove_bot_prefix(message)
        
        # 2. Whitespace normalisieren
        cleaned = self._normalize_whitespace(cleaned)
        
        # 3. Längen-Checks
        length_error = self._check_length(cleaned)
        if length_error:
            self.stats['rejected_inputs'] += 1
            return None, length_error
        
        # 4. Pattern-Checks (Spam, etc.)
        pattern_error = self._check_problematic_patterns(cleaned)
        if pattern_error:
            self.stats['rejected_inputs'] += 1
            return None, pattern_error
        
        # 5. Content-Checks
        content_error = self._check_content(cleaned)
        if content_error:
            self.stats['rejected_inputs'] += 1
            return None, content_error
        
        # 6. Sanitization
        sanitized = self._sanitize(cleaned)
        
        if sanitized != cleaned:
            self.stats['sanitized_inputs'] += 1
            logger.debug(f"Input sanitized: '{cleaned}' -> '{sanitized}'")
        
        logger.info(f"✅ Input validated: '{sanitized[:50]}...'")
        return sanitized, None
    
    def _remove_bot_prefix(self, message: str) -> str:
        """Entfernt Bot-Befehl-Prefix"""
        # Case-insensitive Entfernung
        pattern = re.compile(re.escape(BOT_COMMAND_PREFIX), re.IGNORECASE)
        cleaned = pattern.sub('', message, count=1).strip()
        return cleaned
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalisiert Leerzeichen und Zeilenumbrüche"""
        # Multiple Leerzeichen -> einzelnes Leerzeichen
        text = re.sub(r'\s+', ' ', text)
        # Leading/trailing whitespace entfernen
        text = text.strip()
        return text
    
    def _check_length(self, text: str) -> Optional[str]:
        """Prüft Eingabelänge"""
        length = len(text)
        
        if length < MIN_INPUT_LENGTH:
            return f"Deine Frage ist zu kurz (mindestens {MIN_INPUT_LENGTH} Zeichen). Bitte stelle eine vollständige Frage."
        
        if length > MAX_INPUT_LENGTH:
            return f"Deine Frage ist zu lang (maximal {MAX_INPUT_LENGTH} Zeichen). Bitte kürze sie."
        
        return None
    
    def _check_problematic_patterns(self, text: str) -> Optional[str]:
        """Prüft auf bekannte Problem-Patterns"""
        for i, pattern in enumerate(self.problematic_patterns):
            if pattern.search(text):
                logger.warning(f"Problematic pattern detected: {PROBLEMATIC_PATTERNS[i]}")
                return "Deine Eingabe enthält ungültige Zeichen oder Muster. Bitte stelle eine normale Frage mit Worten."
        
        return None
    
    def _check_content(self, text: str) -> Optional[str]:
        """Prüft Inhalt auf Mindestanforderungen"""
        
        # Mindestens ein Buchstabe
        if not re.search(r'[a-zA-ZäöüÄÖÜß]', text):
            return "Ich verstehe nur Fragen mit Worten. Bitte formuliere deine Frage mit Text."
        
        # Mindestens ein Wort (3+ Buchstaben)
        words = re.findall(r'[a-zA-ZäöüÄÖÜß]{3,}', text)
        if len(words) < 1:
            return "Bitte stelle eine vollständige Frage mit mindestens einem richtigen Wort."
        
        # Nur Zahlen? (ohne Kontext)
        if re.match(r'^[\d\s.,-]+$', text):
            return "Ich sehe nur Zahlen. Bitte stelle eine Frage in Worten, z.B. 'Wie viele Personen passen in Casa Gabriello?'"
        
        return None
    
    def _sanitize(self, text: str) -> str:
        """
        Bereinigt Input für sicheres Processing
        Entfernt potentiell gefährliche Zeichen
        """
        # Extrem lange Wiederholungen kürzen (z.B. "??????????" -> "???")
        text = re.sub(r'([!?.,:;])\1{3,}', r'\1\1\1', text)
        
        # Null-Width und unsichtbare Unicode-Zeichen entfernen
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
        
        # Control-Characters entfernen (außer Newline/Tab)
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text.strip()
    
    def get_stats(self) -> Dict:
        """Gibt Validierungs-Statistiken zurück"""
        rejection_rate = 0
        if self.stats['total_validations'] > 0:
            rejection_rate = (self.stats['rejected_inputs'] / self.stats['total_validations']) * 100
        
        return {
            **self.stats,
            'rejection_rate_percent': round(rejection_rate, 2),
            'acceptance_rate_percent': round(100 - rejection_rate, 2),
        }
    
    def reset_stats(self):
        """Setzt Statistiken zurück"""
        self.stats = {
            'total_validations': 0,
            'rejected_inputs': 0,
            'sanitized_inputs': 0,
        }


class QuickResponder:
    """
    Erkennt simple Anfragen die direkt beantwortet werden können
    ohne LLM zu verwenden (Performance-Optimierung)
    """
    
    QUICK_RESPONSES = {
        # Grüße
        r'\b(hallo|hi|hey|guten\s*(tag|morgen|abend))\b': 
            "Hallo! 👋 Wie kann ich dir helfen?",
        
        # Danke
        r'\b(danke|thanks|grazie|merci)\b': 
            "Gern geschehen! Kann ich noch etwas für dich tun?",
        
        # Hilfe
        r'\b(hilfe|help|aiuto)\b': 
            """Ich helfe dir gerne! Stelle mir Fragen zu:
• WLAN und Internet
• Pizzaofen
• Müll und Recycling
• Hunde im Borgo
• Schlangen und Sicherheit
• Notfälle

Beispiel: "Wie funktioniert der Pizzaofen?" """,
        
        # Status
        r'\b(ping|status|alive|version)\b':
            f"🤖 Borgo-Bot online! Version 0.99 | Bereit für deine Fragen.",
    }
    
    def __init__(self):
        self.patterns = {
            re.compile(pattern, re.IGNORECASE): response 
            for pattern, response in self.QUICK_RESPONSES.items()
        }
    
    def get_quick_response(self, message: str) -> Optional[str]:
        """
        Prüft ob Nachricht eine Quick-Response auslöst
        
        Returns:
            Direkte Antwort oder None (dann LLM nutzen)
        """
        message_lower = message.lower().strip()
        
        # Sehr kurze Nachrichten prüfen
        if len(message_lower) < 15:
            for pattern, response in self.patterns.items():
                if pattern.search(message_lower):
                    logger.info(f"Quick response triggered for: '{message[:30]}...'")
                    return response
        
        return None


# ========================================
# TESTS & BEISPIELE
# ========================================

def test_validator():
    """Test-Suite für den Input-Validator"""
    validator = InputValidator()
    responder = QuickResponder()
    
    test_cases = [
        # (input, should_pass, description)
        ("!bot Wie viel Mehl für Pizza?", True, "Normale Frage"),
        ("!bot   ", False, "Nur Leerzeichen"),
        ("!bot ????", False, "Nur Satzzeichen"),
        ("!bot a", False, "Zu kurz"),
        ("!bot " + "x" * 600, False, "Zu lang"),
        ("!bot 12345", False, "Nur Zahlen"),
        ("!bot Hallo", True, "Quick Response"),
        ("!bot !!!!!!!!!!!!!!!!!!!!!!!", False, "Spam"),
        ("!bot Wie funktioniert der Pizzaofen?", True, "Gute Frage"),
    ]
    
    print("=" * 60)
    print("INPUT VALIDATOR TESTS")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_input, should_pass, description in test_cases:
        result, error = validator.validate(test_input)
        
        # Quick Response Check
        quick_resp = None
        if result:
            quick_resp = responder.get_quick_response(result)
        
        is_pass = (result is not None) == should_pass
        
        status = "✅ PASS" if is_pass else "❌ FAIL"
        
        print(f"\n{status} | {description}")
        print(f"  Input: '{test_input[:50]}'")
        print(f"  Result: {result[:50] if result else 'REJECTED'}")
        if error:
            print(f"  Error: {error[:80]}")
        if quick_resp:
            print(f"  Quick: {quick_resp[:50]}")
        
        if is_pass:
            passed += 1
        else:
            failed += 1
    
    # Statistiken
    print("\n" + "=" * 60)
    print("STATISTIKEN")
    print("=" * 60)
    stats = validator.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\n🎯 Tests: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    test_validator()
