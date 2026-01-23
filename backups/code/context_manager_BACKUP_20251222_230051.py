"""
Borgo-Bot v3.5 - Context Manager
Phase 3: Strikte Context-Isolierung und Size-Management
"""

import yaml
import logging
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from config import (
    MAX_CONTEXT_WORDS,
    MAX_CONTEXT_ENTRIES,
    YAML_DB_PATH,
    CONTEXT_MIXING_RULES
)

logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """Repräsentiert einen einzelnen Context-Eintrag"""
    keyword: str
    category: str
    content: str
    word_count: int
    metadata: Dict


class ContextManager:
    """
    Verwaltet Context für LLM-Anfragen
    Verhindert Context-Mixing und Halluzinationen
    """
    
    def __init__(self, yaml_path: Path = YAML_DB_PATH):
        self.yaml_path = yaml_path
        self.knowledge_base = self._load_yaml()
        self.synonym_map = self._build_synonym_map()  # NEU: Synonym-Mapping
        self.stats = {
            'contexts_built': 0,
            'entries_loaded': 0,
            'truncations': 0,
            'mixing_prevented': 0,
        }
    
    def _load_yaml(self) -> Dict:
        """Lädt YAML Knowledge Base"""
        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                logger.info(f"✅ YAML loaded: {len(data)} entries")
                return data
        except Exception as e:
            logger.error(f"❌ Failed to load YAML: {e}")
            return {}
    
    def _build_synonym_map(self) -> Dict[str, str]:
        """Baut Mapping: Synonym → Entry-Name"""
        synonym_map = {}
        
        for entry_name, entry_data in self.knowledge_base.items():
            # Entry-Name selbst mapped zu sich selbst
            synonym_map[entry_name.lower()] = entry_name
            
            # Alle Synonyme mappen zum Entry-Namen
            if 'synonyms' in entry_data:
                for synonym in entry_data['synonyms']:
                    synonym_map[synonym.lower()] = entry_name
        
        logger.debug(f"Built synonym map with {len(synonym_map)} mappings")
        return synonym_map
    
    def get_available_keywords(self) -> Set[str]:
        """Gibt alle verfügbaren Keywords zurück (Entry-Namen + Synonyme)"""
        all_keywords = set()
        
        for entry_name, entry_data in self.knowledge_base.items():
            # Entry-Name selbst
            all_keywords.add(entry_name)
            
            # Alle Synonyme
            if 'synonyms' in entry_data:
                all_keywords.update(entry_data['synonyms'])
        
        return all_keywords


    def build_context(
        self, 
        keywords: List[str], 
        query: str,
        max_entries: int = MAX_CONTEXT_ENTRIES
    ) -> Tuple[str, Dict]:
        """
        Baut Context aus Keywords
        
        Args:
            keywords: Liste von Keywords (priorisiert)
            query: Original User-Query
            max_entries: Max Anzahl Entries zu laden
        
        Returns:
            (context_string, metadata)
        """
        self.stats['contexts_built'] += 1
        
        # 1. Lade Entries für Keywords
        entries = self._load_entries(keywords, max_entries)
        
        # 2. Prüfe auf Context-Mixing
        entries = self._prevent_context_mixing(entries, query)
        
        # 3. Begrenze auf Word-Count
        entries = self._truncate_by_word_count(entries)
        
        # 4. Formatiere Context
        context_string = self._format_context(entries)
        
        # Metadata
        metadata = {
            'total_entries': len(entries),
            'total_words': sum(e.word_count for e in entries),
            'keywords_used': [e.keyword for e in entries],
            'categories': list(set(e.category for e in entries)),
        }
        
        logger.info(f"📦 Context built: {len(entries)} entries, {metadata['total_words']} words")
        
        return context_string, metadata
    
    def _load_entries(
        self, 
        keywords: List[str], 
        max_entries: int
    ) -> List[ContextEntry]:
        """Lädt YAML-Entries für Keywords"""
        entries = []
        seen_entries = set()  # Vermeide Duplikate
        
        for keyword in keywords[:max_entries]:
            # GEÄNDERT: Mapped Synonym zu Entry-Name
            entry_name = self.synonym_map.get(keyword.lower(), keyword)
            
            # Vermeide Duplikate (z.B. wenn "pool" und "pools" beide gefunden werden)
            if entry_name in seen_entries:
                continue
            
            if entry_name in self.knowledge_base:
                data = self.knowledge_base[entry_name]
                
                entry = ContextEntry(
                    keyword=entry_name,  # GEÄNDERT: Nutze Entry-Name statt Keyword
                    category=data.get('category', 'unknown'),
                    content=data.get('content', ''),
                    word_count=len(data.get('content', '').split()),
                    metadata={
                        'synonyms': data.get('synonyms', []),
                        'priority': data.get('priority', 'normal'),
                    }
                )
                
                entries.append(entry)
                seen_entries.add(entry_name)
                self.stats['entries_loaded'] += 1
                
                logger.debug(f"Loaded entry: {entry_name} (from keyword: {keyword}, {entry.word_count} words)")
        
        return entries
    
    def _prevent_context_mixing(
        self, 
        entries: List[ContextEntry], 
        query: str
    ) -> List[ContextEntry]:
        """
        Verhindert Context-Mixing (z.B. Pizza + Rasenmäher)
        Entfernt inkonsistente Entries
        """
        if not entries:
            return entries
        
        query_lower = query.lower()
        
        # Prüfe für jedes Topic ob Verbotswörter in anderen Entries sind
        filtered_entries = []
        
        for entry in entries:
            should_keep = True
            
            # Prüfe ob dieses Entry ein bekanntes Topic ist
            if entry.keyword in CONTEXT_MIXING_RULES:
                forbidden_words = CONTEXT_MIXING_RULES[entry.keyword]
                
                # Prüfe andere Entries auf Verbotswörter
                for other_entry in entries:
                    if other_entry.keyword == entry.keyword:
                        continue
                    
                    # Prüfe ob forbidden words in content sind
                    other_content_lower = other_entry.content.lower()
                    for forbidden in forbidden_words:
                        if forbidden in other_content_lower:
                            logger.warning(
                                f"Context mixing detected: '{entry.keyword}' conflicts with "
                                f"'{other_entry.keyword}' (contains '{forbidden}')"
                            )
                            should_keep = False
                            self.stats['mixing_prevented'] += 1
                            break
                    
                    if not should_keep:
                        break
            
            if should_keep:
                filtered_entries.append(entry)
        
        return filtered_entries
    
    def _truncate_by_word_count(
        self, 
        entries: List[ContextEntry]
    ) -> List[ContextEntry]:
        """
        Begrenzt Entries auf MAX_CONTEXT_WORDS
        Verhindert Context-Overload
        """
        total_words = 0
        truncated_entries = []
        
        for entry in entries:
            if total_words + entry.word_count <= MAX_CONTEXT_WORDS:
                truncated_entries.append(entry)
                total_words += entry.word_count
            else:
                # Kann nicht mehr hinzugefügt werden
                logger.warning(
                    f"Truncating context: '{entry.keyword}' would exceed limit "
                    f"({total_words + entry.word_count} > {MAX_CONTEXT_WORDS})"
                )
                self.stats['truncations'] += 1
                break
        
        return truncated_entries
    
    def _format_context(self, entries: List[ContextEntry]) -> str:
        """
        Formatiert Entries zu LLM-Context-String
        Klare Strukturierung für LLM
        """
        if not entries:
            return ""
        
        context_parts = [
            "# BORGO BATONE KNOWLEDGE BASE",
            "",
            "Du bist Borgi, der Borgo-Batone Gäste-Assistent.",
            "Antworte NUR basierend auf folgenden Informationen:",
            ""
        ]
        
        for i, entry in enumerate(entries, 1):
            context_parts.extend([
                f"## {i}. {entry.keyword.upper()} (Kategorie: {entry.category})",
                "",
                entry.content,
                "",
                "---",
                ""
            ])
        
        context_parts.extend([
            "# WICHTIGE REGELN",
            "1. Antworte NUR mit Informationen aus obigen Einträgen",
            "2. Wenn du etwas nicht weißt, sage es ehrlich",
            "3. Erfinde KEINE Zahlen, Einheiten oder Details",
            "4. Bleibe beim Thema - keine Themenvermischung",
            "5. Sei präzise und korrekt",
        ])
        
        return "\n".join(context_parts)
    
    def get_fallback_context(self, category: Optional[str] = None) -> str:
        """
        Gibt Fallback-Context wenn keine Keywords gefunden
        
        Args:
            category: Optional Kategorie für gezielten Fallback
        """
        logger.info(f"Using fallback context (category: {category})")
        
        fallback = [
            "# BORGO BATONE - ALLGEMEINE INFORMATIONEN",
            "",
            "Borgo Batone ist ein historisches Dorf in der Toskana.",
            "Es ist ein gemeinschaftliches Projekt mit 100 Mitgliedern.",
            "",
            "Ich kann dir helfen bei Fragen zu:",
            "• WLAN und Internet",
            "• Pizzaofen Benutzung",
            "• Müll und Recycling",
            "• Haustiere (besonders Hunde)",
            "• Sicherheit (Schlangen, Notfälle)",
            "• Kontakt zur Onsite-Gruppe",
            "",
            "Für deine spezifische Frage habe ich leider keine Details.",
            "Bitte kontaktiere die Onsite-Gruppe oder schaue im Benvenuti-Guide nach."
        ]
        
        return "\n".join(fallback)
    
    def reload_knowledge_base(self) -> bool:
        """Lädt Knowledge Base neu (für Updates)"""
        try:
            self.knowledge_base = self._load_yaml()
            self.synonym_map = self._build_synonym_map()  # NEU: Map neu aufbauen
            logger.info("✅ Knowledge base reloaded")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to reload knowledge base: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Gibt Context-Manager Statistiken zurück"""
        return {
            **self.stats,
            'total_entries_in_db': len(self.knowledge_base),
            'total_synonym_mappings': len(self.synonym_map),  # NEU
            'avg_entries_per_context': (
                self.stats['entries_loaded'] / self.stats['contexts_built']
                if self.stats['contexts_built'] > 0 else 0
            )
        }


class ContextValidator:
    """
    Validiert generierten Context auf Qualität
    Erkennt potentielle Probleme
    """
    
    @staticmethod
    def validate(context: str, metadata: Dict) -> Tuple[bool, List[str]]:
        """
        Validiert Context
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check 1: Nicht leer
        if not context or len(context.strip()) < 50:
            issues.append("Context zu kurz oder leer")
        
        # Check 2: Nicht zu groß
        word_count = len(context.split())
        if word_count > MAX_CONTEXT_WORDS * 1.2:  # 20% Toleranz
            issues.append(f"Context zu groß: {word_count} Wörter")
        
        # Check 3: Keine doppelten Keywords
        keywords = metadata.get('keywords_used', [])
        if len(keywords) != len(set(keywords)):
            issues.append("Doppelte Keywords im Context")
        
        # Check 4: Konsistente Kategorien
        categories = metadata.get('categories', [])
        if len(categories) > 2:
            issues.append(f"Zu viele Kategorien gemischt: {categories}")
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            logger.warning(f"Context validation failed: {issues}")
        
        return is_valid, issues


# ========================================
# TESTS
# ========================================

def test_context_manager():
    """Test-Suite für Context Manager"""
    
    # Erstelle Test-YAML
    test_yaml_path = Path("/home/claude/borgo_bot_v3_5/test_knowledge.yaml")
    
    test_data = {
        'pizza': {
            'category': 'facilities',
            'content': 'Der Pizzaofen steht bei Casa Gabriello. Für 24 Personen brauchst du 3 kg Mehl.',
            'priority': 'high'
        },
        'pizzaofen': {
            'category': 'facilities',
            'content': 'Feuer 1 Stunde brennen lassen. Temperatur ca. 250°C. Pizza 9 Minuten backen.',
            'priority': 'high'
        },
        'hunde': {
            'category': 'rules',
            'content': 'Hunde sind erlaubt. Onsite-Gruppe vorher informieren. Nach 22 Uhr Ruhezeiten beachten.',
            'priority': 'medium'
        },
        'schlangen': {
            'category': 'safety',
            'content': 'Vipern sind giftig. Bei Biss sofort ins Krankenhaus Lucca. Geschlossene Schuhe tragen.',
            'priority': 'high'
        },
    }
    
    with open(test_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(test_data, f, allow_unicode=True)
    
    # Test Context Manager
    manager = ContextManager(test_yaml_path)
    validator = ContextValidator()
    
    print("=" * 70)
    print("CONTEXT MANAGER TESTS")
    print("=" * 70)
    
    test_cases = [
        (['pizza', 'pizzaofen'], "Wie funktioniert der Pizzaofen?"),
        (['hunde'], "Sind Hunde erlaubt?"),
        (['schlangen'], "Ich sah eine Schlange"),
        (['pizza', 'hunde', 'schlangen'], "Alles über Borgo"),  # Zu viele
        ([], "Keine Keywords"),  # Fallback
    ]
    
    for keywords, query in test_cases:
        print(f"\n📝 Query: '{query}'")
        print(f"   Keywords: {keywords}")
        
        if keywords:
            context, metadata = manager.build_context(keywords, query)
            
            print(f"\n   Metadata:")
            for key, value in metadata.items():
                print(f"      {key}: {value}")
            
            # Validierung
            is_valid, issues = validator.validate(context, metadata)
            status = "✅ VALID" if is_valid else "❌ INVALID"
            print(f"\n   {status}")
            if issues:
                for issue in issues:
                    print(f"      ⚠️  {issue}")
            
            # Context Preview
            print(f"\n   Context Preview (erste 300 Zeichen):")
            print("   " + "-" * 66)
            preview = context[:300].replace('\n', '\n   ')
            print(f"   {preview}...")
        else:
            # Fallback
            context = manager.get_fallback_context()
            print(f"\n   📁 Using Fallback Context")
            preview = context[:200].replace('\n', '\n   ')
            print(f"   {preview}...")
    
    # Statistiken
    print("\n" + "=" * 70)
    print("STATISTIKEN")
    print("=" * 70)
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("=" * 70)
    
    # Cleanup
    test_yaml_path.unlink()


if __name__ == "__main__":
    test_context_manager()
