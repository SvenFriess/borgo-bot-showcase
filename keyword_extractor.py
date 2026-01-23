"""
Borgo-Bot v3.5 - Enhanced Keyword Extractor
Phase 2: Intelligente Keyword-Extraktion mit Confidence-Scoring
"""

import re
import logging
from typing import List, Dict, Set, Tuple, Optional
from difflib import SequenceMatcher
from collections import defaultdict

from config_multi_bot import (
    KEYWORD_CONFIDENCE,
    FUZZY_MATCH_THRESHOLD,
    MIN_KEYWORDS_REQUIRED
)

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """
    Extrahiert Keywords aus User-Fragen mit Confidence-Scoring
    Verwendet Fuzzy-Matching für ähnliche Begriffe
    """
    
    def __init__(self, yaml_keywords: Set[str]):
        """
        Args:
            yaml_keywords: Set aller verfügbaren Keywords aus YAML-DB
        """
        self.yaml_keywords = set(k.lower() for k in yaml_keywords)
        self.stats = {
            'extractions': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'no_keywords': 0,
        }
        
        # Synonym-Mapping für besseres Matching
        self.synonyms = self._build_synonym_map()
    
    def _build_synonym_map(self) -> Dict[str, Set[str]]:
        """
        Erstellt Synonym-Mapping für häufige Begriffe
        Hilft bei verschiedenen Formulierungen
        """
        return {
            'wlan': {'wifi', 'internet', 'w-lan', 'netzwerk', 'wlan-passwort', 'wifi-passwort'},
            'pizza': {'pizzaofen', 'pizza-ofen', 'ofen', 'backen'},
            'pizzaofen': {'pizza', 'ofen', 'backen'},
            'hunde': {'hund', 'dogs', 'dog', 'haustier', 'haustiere', 'vierbeiner', 'tier', 'tiere'},
            'schlangen': {'schlange', 'viper', 'vipern', 'reptil', 'reptilien'},
            'müll': {'abfall', 'recycling', 'mülltrennung', 'entsorgung', 'trash', 'garbage'},
            'notfall': {'notfälle', 'emergency', 'hilfe', 'sos', 'dringend', 'notruf'},
            'wasser': {'warmwasser', 'kaltwasser', 'trinkwasser', 'dusche'},
            'heizung': {'heizen', 'temperatur', 'warm', 'kalt', 'thermostat'},
            'strom': {'elektrizität', 'energie', 'sicherung', 'stromausfall'},
            'checkout': {'check-out', 'abreise', 'departure', 'auschecken'},
            'anreise': {'check-in', 'checkin', 'arrival', 'ankommen', 'ankunft'},
            'pool': {'schwimmbad', 'swimming', 'baden', 'schwimmen'},
        }
    
    def extract(self, query: str) -> Dict[str, any]:
        """
        Hauptmethode: Extrahiert Keywords mit Confidence
        
        Returns:
            Dict mit 'high', 'medium', 'low' confidence Keywords
            und Metadaten
        """
        self.stats['extractions'] += 1
        
        query_lower = query.lower()
        
        # 1. Direkte Matches (High Confidence)
        high = self._find_direct_matches(query_lower)
        
        # 2. Synonym-Matches (High->Medium Confidence)
        medium = self._find_synonym_matches(query_lower, exclude=high)
        
        # 3. Fuzzy-Matches (Medium->Low Confidence)
        low = self._find_fuzzy_matches(query_lower, exclude=high.union(medium))
        
        # Statistiken updaten
        if high:
            self.stats['high_confidence'] += 1
        if medium:
            self.stats['medium_confidence'] += 1
        if low:
            self.stats['low_confidence'] += 1
        if not (high or medium or low):
            self.stats['no_keywords'] += 1
        
        result = {
            'high': sorted(high),
            'medium': sorted(medium),
            'low': sorted(low),
            'all': sorted(high.union(medium).union(low)),
            'confidence_level': self._determine_overall_confidence(high, medium, low),
            'query': query
        }
        
        logger.info(f"🔍 Keywords extracted: High={len(high)}, Med={len(medium)}, Low={len(low)}")
        logger.debug(f"   Keywords: {result['all']}")
        
        return result
    
    def _find_direct_matches(self, query: str) -> Set[str]:
        """Findet exakte Keyword-Matches in der Query"""
        matches = set()
        
        for keyword in self.yaml_keywords:
            # Wort-Grenzen beachten für präzises Matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query):
                matches.add(keyword)
        
        return matches
    
    def _find_synonym_matches(self, query: str, exclude: Set[str]) -> Set[str]:
        """
        Findet Keywords über Synonyme
        Wenn "wifi" in Query, finde "wlan" keyword
        """
        matches = set()
        
        for base_keyword, synonyms in self.synonyms.items():
            # Skip wenn base_keyword schon gefunden
            if base_keyword in exclude:
                continue
            
            # Prüfe ob base_keyword in YAML existiert
            if base_keyword not in self.yaml_keywords:
                continue
            
            # Prüfe Synonyme
            for synonym in synonyms:
                pattern = r'\b' + re.escape(synonym) + r'\b'
                if re.search(pattern, query):
                    matches.add(base_keyword)
                    logger.debug(f"Synonym match: '{synonym}' -> '{base_keyword}'")
                    break
        
        return matches
    
    def _find_fuzzy_matches(self, query: str, exclude: Set[str]) -> Set[str]:
        """
        Findet ähnliche Keywords via Fuzzy-Matching
        Hilft bei Tippfehlern und Variationen
        """
        matches = set()
        query_words = set(re.findall(r'\b\w{4,}\b', query))  # Mindestens 4 Buchstaben
        
        for query_word in query_words:
            best_match = None
            best_score = 0
            
            for keyword in self.yaml_keywords:
                if keyword in exclude:
                    continue
                
                # Berechne Ähnlichkeit
                score = SequenceMatcher(None, query_word, keyword).ratio()
                
                if score > best_score and score >= FUZZY_MATCH_THRESHOLD:
                    best_score = score
                    best_match = keyword
            
            if best_match:
                matches.add(best_match)
                logger.debug(f"Fuzzy match: '{query_word}' -> '{best_match}' (score: {best_score:.2f})")
        
        return matches
    
    def _determine_overall_confidence(
        self, 
        high: Set[str], 
        medium: Set[str], 
        low: Set[str]
    ) -> str:
        """
        Bestimmt Overall-Confidence-Level basierend auf gefundenen Keywords
        """
        if high:
            return 'high'
        elif medium:
            return 'medium'
        elif low:
            return 'low'
        else:
            return 'none'
    
    def get_best_keywords(
        self, 
        extraction_result: Dict, 
        max_keywords: int = 3
    ) -> List[str]:
        """
        Gibt die besten N Keywords zurück
        Priorisiert High > Medium > Low
        
        Args:
            extraction_result: Output von extract()
            max_keywords: Maximale Anzahl zurückzugebender Keywords
        
        Returns:
            Liste der besten Keywords
        """
        keywords = []
        
        # High Confidence zuerst
        keywords.extend(extraction_result['high'])
        
        # Falls nicht genug, Medium dazu
        if len(keywords) < max_keywords:
            remaining = max_keywords - len(keywords)
            keywords.extend(extraction_result['medium'][:remaining])
        
        # Falls immer noch nicht genug, Low dazu
        if len(keywords) < max_keywords:
            remaining = max_keywords - len(keywords)
            keywords.extend(extraction_result['low'][:remaining])
        
        return keywords[:max_keywords]
    
    def get_stats(self) -> Dict:
        """Gibt Extraktions-Statistiken zurück"""
        if self.stats['extractions'] == 0:
            return self.stats
        
        total = self.stats['extractions']
        return {
            **self.stats,
            'high_rate_percent': round((self.stats['high_confidence'] / total) * 100, 2),
            'medium_rate_percent': round((self.stats['medium_confidence'] / total) * 100, 2),
            'low_rate_percent': round((self.stats['low_confidence'] / total) * 100, 2),
            'no_keywords_rate_percent': round((self.stats['no_keywords'] / total) * 100, 2),
        }


class CategoryMatcher:
    """
    Fallback: Matched Query zu YAML-Kategorien
    Wird verwendet wenn keine Keywords gefunden
    """
    
    def __init__(self):
        # Kategorie -> typische Begriffe Mapping
        self.category_patterns = {
            'facilities': ['ofen', 'pizza', 'küche', 'waschmaschine', 'pool'],
            'safety': ['notfall', 'feuer', 'schlange', 'viper', 'gefahr', 'krankenhaus'],
            'basics': ['wlan', 'wifi', 'internet', 'passwort', 'ankunft', 'check'],
            'rules': ['erlaubt', 'verboten', 'regel', 'verhalten', 'hund', 'lärm'],
            'contact': ['onsite', 'gruppe', 'kontakt', 'telefon', 'hilfe'],
            'faq': ['wie', 'was', 'wann', 'wo', 'warum'],
        }
    
    def find_category(self, query: str) -> Optional[str]:
        """
        Findet beste Kategorie für Query
        
        Returns:
            Kategorie-Name oder None
        """
        query_lower = query.lower()
        scores = defaultdict(int)
        
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    scores[category] += 1
        
        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])
            logger.info(f"Category matched: '{best_category[0]}' (score: {best_category[1]})")
            return best_category[0]
        
        return None


# ========================================
# TESTS
# ========================================

def test_extractor():
    """Test-Suite für Keyword-Extraktor"""
    
    # Mock YAML-Keywords
    yaml_keywords = {
        'wlan', 'pizza', 'pizzaofen', 'hunde', 'schlangen', 
        'müll', 'notfall', 'anreise', 'check-in', 'pool',
        'waschmaschine', 'heizung', 'strom', 'wasser'
    }
    
    extractor = KeywordExtractor(yaml_keywords)
    matcher = CategoryMatcher()
    
    test_queries = [
        "Wie funktioniert der Pizzaofen?",
        "Sind Hunde erlaubt?",
        "Ich habe eine Schlange gesehen",
        "Wie viel Mehl für Pizza?",
        "WiFi Passwort?",  # Synonym-Test
        "Gibt es einen Pool?",
        "Notfall - Feuer!",
        "Wann ist Check-in?",
        "Wie funktioniert die Heitzung?",  # Fuzzy-Test (Tippfehler)
        "Blablabla nonsense",  # Kein Match
    ]
    
    print("=" * 70)
    print("KEYWORD EXTRACTOR TESTS")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        
        # Extraktion
        result = extractor.extract(query)
        
        print(f"   Confidence: {result['confidence_level'].upper()}")
        if result['high']:
            print(f"   ✅ High: {result['high']}")
        if result['medium']:
            print(f"   🔶 Medium: {result['medium']}")
        if result['low']:
            print(f"   ⚠️  Low: {result['low']}")
        
        # Beste Keywords
        best = extractor.get_best_keywords(result, max_keywords=2)
        print(f"   🎯 Best: {best}")
        
        # Category-Fallback wenn keine Keywords
        if not result['all']:
            category = matcher.find_category(query)
            print(f"   📁 Category Fallback: {category}")
    
    # Statistiken
    print("\n" + "=" * 70)
    print("STATISTIKEN")
    print("=" * 70)
    stats = extractor.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("=" * 70)


if __name__ == "__main__":
    test_extractor()
