#!/usr/bin/env python3
"""
Borgo-Bot v0.96 - Benvenuti Link Fix Test Suite
Systematische Validierung des Fixes
"""

import re
import sys
from typing import List, Tuple

# Test-Queries und erwartete Ergebnisse
TEST_CASES = [
    # (query, must_contain, must_not_contain, description)
    (
        "Wo finde ich das Benvenuti?",
        ["piazza.borgo-batone.com", "node/819"],
        ["buchungsbestätigung", "wird verschickt", "booking"],
        "Direkte Frage nach Benvenuti"
    ),
    (
        "Wo ist der Guest Guide?",
        ["piazza.borgo-batone.com", "node/819"],
        ["buchungsbestätigung", "wird verschickt"],
        "Englischer Begriff 'Guest Guide'"
    ),
    (
        "Benvenuti Guide Link?",
        ["piazza.borgo-batone.com", "node/819"],
        ["buchungsbestätigung"],
        "Explizite Link-Anfrage"
    ),
    (
        "Gästehandbuch?",
        ["piazza.borgo-batone.com", "node/819"],
        ["buchungsbestätigung"],
        "Deutsches Synonym"
    ),
    (
        "Wo finde ich Infos für Gäste?",
        ["piazza.borgo-batone.com", "node/819"],
        ["buchungsbestätigung"],
        "Indirekte Frage"
    ),
    (
        "Link zum Borgo Guide?",
        ["piazza.borgo-batone.com", "node/819"],
        ["buchungsbestätigung"],
        "Alternative Formulierung"
    ),
]

# Korrekte Link-URL
CORRECT_LINK = "https://piazza.borgo-batone.com/node/819?language_content_entity=en"

# Verbotene Begriffe (sollten NICHT in Antworten vorkommen)
FORBIDDEN_TERMS = [
    "buchungsbestätigung",
    "wird verschickt",
    "bei buchung",
    "booking confirmation",
    "in deiner buchung",
]


class BenvenutiFixTester:
    """Test-Suite für Benvenuti-Link Fix"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results: List[Tuple[str, bool, str]] = []
    
    def validate_response(self, query: str, response: str, 
                         must_contain: List[str], 
                         must_not_contain: List[str],
                         description: str) -> bool:
        """Validiert eine Bot-Antwort"""
        response_lower = response.lower()
        
        # Prüfe ob alle erforderlichen Begriffe enthalten sind
        missing = []
        for term in must_contain:
            if term.lower() not in response_lower:
                missing.append(term)
        
        # Prüfe ob verbotene Begriffe enthalten sind
        forbidden = []
        for term in must_not_contain:
            if term.lower() in response_lower:
                forbidden.append(term)
        
        # Zusätzlich: Prüfe ob korrekter Link vollständig enthalten ist
        has_correct_link = CORRECT_LINK in response
        
        # Bestimme Test-Ergebnis
        passed = (
            len(missing) == 0 and 
            len(forbidden) == 0 and 
            has_correct_link
        )
        
        # Erstelle Feedback
        feedback = []
        if missing:
            feedback.append(f"❌ Fehlende Begriffe: {', '.join(missing)}")
        if forbidden:
            feedback.append(f"❌ Verbotene Begriffe: {', '.join(forbidden)}")
        if not has_correct_link:
            feedback.append(f"❌ Korrekter Link fehlt: {CORRECT_LINK}")
        
        if passed:
            feedback.append("✅ Alle Checks bestanden")
        
        feedback_str = " | ".join(feedback)
        
        # Speichere Ergebnis
        self.results.append((query, passed, feedback_str))
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        return passed
    
    def run_tests(self, bot_responses: dict) -> bool:
        """Führt alle Tests aus"""
        print("=" * 70)
        print("Borgo-Bot v0.96 - Benvenuti Link Fix Test Suite")
        print("=" * 70)
        print()
        
        for query, must_contain, must_not_contain, description in TEST_CASES:
            print(f"📝 Test: {description}")
            print(f"   Query: \"{query}\"")
            
            if query not in bot_responses:
                print(f"   ⚠️  ÜBERSPRUNGEN: Keine Bot-Antwort vorhanden")
                print()
                continue
            
            response = bot_responses[query]
            passed = self.validate_response(
                query, response, must_contain, must_not_contain, description
            )
            
            if passed:
                print(f"   ✅ BESTANDEN")
            else:
                print(f"   ❌ FEHLGESCHLAGEN")
                print(f"   Response: {response[:100]}...")
            
            print()
        
        # Zusammenfassung
        print("=" * 70)
        print("TEST ZUSAMMENFASSUNG")
        print("=" * 70)
        print(f"Bestanden: {self.passed}/{self.passed + self.failed}")
        print(f"Fehlgeschlagen: {self.failed}/{self.passed + self.failed}")
        print()
        
        # Detaillierte Ergebnisse
        if self.failed > 0:
            print("FEHLGESCHLAGENE TESTS:")
            for query, passed, feedback in self.results:
                if not passed:
                    print(f"❌ \"{query}\"")
                    print(f"   {feedback}")
            print()
        
        # Gesamtergebnis
        all_passed = self.failed == 0
        if all_passed:
            print("✅ ALLE TESTS BESTANDEN! Fix ist korrekt installiert.")
        else:
            print("❌ EINIGE TESTS FEHLGESCHLAGEN! Fix prüfen.")
        print()
        
        return all_passed


def simulate_bot_response(query: str) -> str:
    """
    Simuliert Bot-Antwort für Testing
    HINWEIS: In Production durch echte Bot-Integration ersetzen
    """
    # Hier würde normalerweise der echte Bot gefragt werden
    # Für dieses Test-Script: manuelle Simulation
    return (
        "Das Benvenuti-Guide findest du auf der Piazza:\n"
        "https://piazza.borgo-batone.com/node/819?language_content_entity=en\n\n"
        "Ich empfehle dir, es vor der Anreise durchzulesen!"
    )


def main():
    """Haupt-Test-Funktion"""
    print("HINWEIS: Dieses Script simuliert Bot-Antworten.")
    print("Für echte Tests: Bot-Integration einbauen oder manuell testen.")
    print()
    
    # Sammle Bot-Antworten
    # In Production: hier echten Bot abfragen
    bot_responses = {}
    for query, _, _, _ in TEST_CASES:
        bot_responses[query] = simulate_bot_response(query)
    
    # Führe Tests aus
    tester = BenvenutiFixTester()
    all_passed = tester.run_tests(bot_responses)
    
    # Exit-Code
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
