"""
Borgo-Bot v3.5 - Fallback System
Phase 5: Robuste Fehlerbehandlung und sichere Notfall-Antworten
"""

import logging
from typing import Optional, Dict, List
from enum import Enum

from config import FALLBACK_RESPONSES

logger = logging.getLogger(__name__)


class FallbackReason(Enum):
    """Gründe für Fallback-Antworten"""
    NO_KEYWORDS = "no_keywords"
    LLM_ERROR = "llm_error"
    AMBIGUOUS = "ambiguous"
    OUT_OF_SCOPE = "out_of_scope"
    VALIDATION_FAILED = "validation_failed"
    TOO_MANY_RETRIES = "too_many_retries"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class FallbackSystem:
    """
    Verwaltet Fallback-Antworten und Fehlerbehandlung
    Stellt sicher dass User immer hilfreiche Antworten bekommt
    """
    
    def __init__(self):
        self.stats = {
            'total_fallbacks': 0,
            'by_reason': {reason.value: 0 for reason in FallbackReason},
        }
        
        # Topic-spezifische Hilfe
        self.topic_help = {
            'wlan': """📶 WLAN / Internet:
• Netzwerk: "Borgo Batone WiFi"
• Passwort: [siehe Benvenuti-Guide]
• Bei Problemen: Router neustarten (Technikraum)
• Kontakt: Onsite-Gruppe""",
            
            'pizza': """🍕 Pizzaofen:
• Standort: Casa Gabriello
• Videos: Check YouTube-Channel
• Für 24 Personen: 3 kg Mehl, 3 Würfel Hefe
• Wichtig: Feuer 1h brennen lassen
• Kontakt: Onsite-Gruppe""",
            
            'hunde': """🐕 Hunde im Borgo:
• ✅ Erlaubt mit Voranmeldung
• Onsite-Gruppe informieren
• Ruhezeiten beachten (nach 22 Uhr)
• Zimmer nach Aufenthalt reinigen
• Kontakt: Onsite-Gruppe""",
            
            'schlangen': """🐍 Schlangen / Sicherheit:
• ⚠️ Vipern sind GIFTIG
• Bei Biss: Sofort Krankenhaus Lucca
• Schutz: Geschlossene Schuhe
• Foto machen, Onsite-Gruppe informieren
• NOTFALL: 118 (Rettung)""",
            
            'notfall': """🚨 NOTFALL:
• Rettung: 118
• Feuerwehr: 115
• Polizei: 112 / 113
• Krankenhaus Lucca: +39 0583 9701
• Onsite-Gruppe: [siehe Benvenuti]
• Benvenuti-Guide hat alle Details!""",
        }
    
    def get_fallback_response(
        self,
        reason: FallbackReason,
        query: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Gibt passende Fallback-Antwort basierend auf Grund
        
        Args:
            reason: Grund für Fallback
            query: Original User-Query (optional)
            metadata: Zusätzliche Metadaten (optional)
        
        Returns:
            Fallback-Antwort als String
        """
        self.stats['total_fallbacks'] += 1
        self.stats['by_reason'][reason.value] += 1
        
        logger.warning(f"Fallback triggered: {reason.value}")
        
        # Basis-Response aus Config
        base_response = FALLBACK_RESPONSES.get(
            reason.value,
            FALLBACK_RESPONSES['unknown']
        )
        
        # Versuche Topic-spezifische Hilfe hinzuzufügen
        if query:
            topic_help = self._detect_topic_and_get_help(query)
            if topic_help:
                base_response = f"{base_response}\n\n{topic_help}"
        
        # Füge Kontext-Info hinzu wenn verfügbar
        if metadata and metadata.get('context_info'):
            base_response += f"\n\n💡 {metadata['context_info']}"
        
        return base_response
    
    def _detect_topic_and_get_help(self, query: str) -> Optional[str]:
        """
        Erkennt Topic in Query und gibt passende Hilfe
        
        Returns:
            Topic-spezifische Hilfe oder None
        """
        query_lower = query.lower()
        
        # Prüfe Topics
        topic_keywords = {
            'wlan': ['wlan', 'wifi', 'internet', 'w-lan', 'passwort'],
            'pizza': ['pizza', 'ofen', 'pizzaofen', 'backen', 'mehl'],
            'hunde': ['hund', 'hunde', 'dog', 'haustier', 'vierbeiner'],
            'schlangen': ['schlange', 'schlangen', 'viper', 'giftig', 'biss'],
            'notfall': ['notfall', 'emergency', 'hilfe', 'sos', 'dringend'],
        }
        
        # Finde beste Matches
        matches = []
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    matches.append(topic)
                    break
        
        # Gib erste Match zurück
        if matches:
            topic = matches[0]
            logger.info(f"Topic detected for fallback: {topic}")
            return self.topic_help.get(topic)
        
        return None
    
    def suggest_rephrase(self, query: str) -> str:
        """
        Schlägt bessere Formulierung vor
        
        Args:
            query: Problematische Query
        
        Returns:
            Vorschlag-Text
        """
        suggestions = []
        
        # Zu kurz?
        if len(query.split()) < 3:
            suggestions.append(
                "Deine Frage ist sehr kurz. Versuche:\n"
                "❌ 'Pizza'\n"
                "✅ 'Wie funktioniert der Pizzaofen?'"
            )
        
        # Nur Fragezeichen?
        if '?' in query and len(query.strip('? ')) < 3:
            suggestions.append(
                "Stelle eine vollständige Frage:\n"
                "❌ '???'\n"
                "✅ 'Wie komme ich zum Borgo?'"
            )
        
        # Zu vage?
        vague_words = ['info', 'sachen', 'zeug', 'ding', 'das']
        if any(word in query.lower() for word in vague_words):
            suggestions.append(
                "Sei spezifischer:\n"
                "❌ 'Info über Sachen'\n"
                "✅ 'Wie funktioniert die Waschmaschine?'"
            )
        
        if suggestions:
            return "💡 **Tipp für bessere Antworten:**\n\n" + "\n\n".join(suggestions)
        
        return ""
    
    def escalate_to_human(
        self,
        query: str,
        reason: str,
        attempts: int = 0
    ) -> str:
        """
        Eskaliert zu menschlichem Support
        
        Args:
            query: User-Query
            reason: Grund für Eskalation
            attempts: Anzahl gescheiterter Versuche
        
        Returns:
            Eskalations-Nachricht
        """
        logger.warning(f"Escalating to human support: {reason} (attempts: {attempts})")
        
        escalation = f"""🙋 **Ich brauche menschliche Hilfe**

Deine Frage: _{query}_

Nach {attempts} Versuchen konnte ich keine zufriedenstellende Antwort finden.

**Nächste Schritte:**
1. 📞 Kontaktiere die Onsite-Gruppe direkt
2. 📖 Schaue im Benvenuti-Guide nach
3. 💬 Frage in der Borgo-Community-Gruppe

**Grund:** {reason}

Tut mir leid für die Unannehmlichkeiten! Ich lerne ständig dazu. 🤖
"""
        
        self.stats['total_fallbacks'] += 1
        self.stats['by_reason']['escalated'] = self.stats['by_reason'].get('escalated', 0) + 1
        
        return escalation
    
    def get_stats(self) -> Dict:
        """Gibt Fallback-Statistiken zurück"""
        if self.stats['total_fallbacks'] == 0:
            return self.stats
        
        # Berechne Prozente
        total = self.stats['total_fallbacks']
        stats_with_percent = {
            'total_fallbacks': total,
            'by_reason': {}
        }
        
        for reason, count in self.stats['by_reason'].items():
            percent = round((count / total) * 100, 2) if count > 0 else 0
            stats_with_percent['by_reason'][reason] = {
                'count': count,
                'percent': percent
            }
        
        return stats_with_percent


class ResponseQualityChecker:
    """
    Prüft ob eine Response ausreichend hilfreich ist
    Hilft zu entscheiden ob Fallback nötig ist
    """
    
    @staticmethod
    def is_helpful(response: str, query: str) -> bool:
        """
        Prüft ob Response wahrscheinlich hilfreich ist
        
        Returns:
            True wenn hilfreich, False wenn Fallback besser wäre
        """
        # Zu kurz = wahrscheinlich nicht hilfreich
        if len(response) < 20:
            return False
        
        # Enthält "weiß ich nicht" = nicht hilfreich
        unhelpful_phrases = [
            'weiß ich nicht',
            'kann ich nicht sagen',
            'keine information',
            'nicht verfügbar',
            'nicht bekannt',
        ]
        
        response_lower = response.lower()
        for phrase in unhelpful_phrases:
            if phrase in response_lower:
                return False
        
        # Enthält Fragezeichen = unsicher
        if response.count('?') > 2:
            return False
        
        # Sieht gut aus
        return True
    
    @staticmethod
    def extract_key_info(response: str) -> List[str]:
        """
        Extrahiert Key-Informationen aus Response
        Hilfreich für Logging und Debugging
        """
        key_info = []
        
        # Zahlen
        numbers = re.findall(r'\d+(?:\.\d+)?\s*(?:kg|g|ml|l|m|cm|€|h|min)?', response)
        if numbers:
            key_info.append(f"Numbers: {numbers}")
        
        # URLs
        urls = re.findall(r'https?://[^\s]+', response)
        if urls:
            key_info.append(f"URLs: {urls}")
        
        # Wichtige Begriffe
        important_words = ['notfall', 'wichtig', 'achtung', 'verboten', 'erlaubt']
        found_words = [word for word in important_words if word in response.lower()]
        if found_words:
            key_info.append(f"Keywords: {found_words}")
        
        return key_info


# ========================================
# TESTS
# ========================================

def test_fallback_system():
    """Test-Suite für Fallback System"""
    
    system = FallbackSystem()
    checker = ResponseQualityChecker()
    
    print("=" * 70)
    print("FALLBACK SYSTEM TESTS")
    print("=" * 70)
    
    # Test 1: Verschiedene Fallback-Gründe
    test_cases = [
        (FallbackReason.NO_KEYWORDS, "Wie geht es dir?", None),
        (FallbackReason.LLM_ERROR, "Pizza Info", None),
        (FallbackReason.AMBIGUOUS, "???", None),
        (FallbackReason.VALIDATION_FAILED, "Wie viel Mehl für Pizza?", None),
    ]
    
    print("\n### Test: Fallback-Responses ###\n")
    
    for reason, query, metadata in test_cases:
        print(f"Reason: {reason.value}")
        print(f"Query: '{query}'")
        
        response = system.get_fallback_response(reason, query, metadata)
        
        print(f"Response:\n{response[:200]}...")
        print("-" * 70)
    
    # Test 2: Topic-Detection
    print("\n### Test: Topic-Detection ###\n")
    
    topic_queries = [
        "Wie funktioniert das WLAN?",
        "Info über Pizzaofen",
        "Sind Hunde erlaubt?",
        "Ich sah eine Schlange",
        "Notfall!!!",
    ]
    
    for query in topic_queries:
        print(f"Query: '{query}'")
        response = system.get_fallback_response(
            FallbackReason.NO_KEYWORDS,
            query
        )
        has_topic_help = any(
            topic in response 
            for topic in ['📶', '🍕', '🐕', '🐍', '🚨']
        )
        print(f"Topic-Help detected: {has_topic_help}")
        print("-" * 70)
    
    # Test 3: Response Quality Check
    print("\n### Test: Response Quality ###\n")
    
    test_responses = [
        ("Für 24 Personen brauchst du 3 kg Mehl.", True),
        ("Das weiß ich leider nicht.", False),
        ("?? Ich bin unsicher ???", False),
        ("Ok", False),
    ]
    
    for response, expected_helpful in test_responses:
        is_helpful = checker.is_helpful(response, "test query")
        status = "✅" if is_helpful == expected_helpful else "❌"
        print(f"{status} Response: '{response[:50]}'")
        print(f"   Helpful: {is_helpful} (expected: {expected_helpful})")
    
    # Test 4: Rephrase-Vorschläge
    print("\n### Test: Rephrase-Suggestions ###\n")
    
    bad_queries = [
        "pizza",
        "???",
        "Info über Sachen",
    ]
    
    for query in bad_queries:
        suggestion = system.suggest_rephrase(query)
        print(f"Query: '{query}'")
        if suggestion:
            print(f"Suggestion:\n{suggestion[:150]}...")
        else:
            print("No suggestion")
        print("-" * 70)
    
    # Statistiken
    print("\n" + "=" * 70)
    print("STATISTIKEN")
    print("=" * 70)
    stats = system.get_stats()
    print(f"Total Fallbacks: {stats['total_fallbacks']}")
    print("\nBy Reason:")
    for reason, data in stats['by_reason'].items():
        if data['count'] > 0:
            print(f"  {reason}: {data['count']} ({data['percent']}%)")
    print("=" * 70)


if __name__ == "__main__":
    import re  # For ResponseQualityChecker
    test_fallback_system()
