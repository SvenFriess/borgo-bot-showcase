#!/usr/bin/env python3
"""
Borgo-Bot v0.97 - System-Prompt Fix
Erzwingt WORD-FOR-WORD Reproduction statt Paraphrasierung
"""

import shutil
from pathlib import Path
from datetime import datetime

# Backup-Verzeichnis
BACKUP_DIR = Path("backups")

# Dateien zum Patchen
FILES_TO_PATCH = {
    'llm_handler.py': [
        {
            'old': '''    def _build_prompt(self, query: str, context: str, model: str = None) -> str:
        """Baut LLM-Prompt aus Query und Context"""
        
        # Für qwen-Modelle: Explizit Deutsch verlangen!
        language_instruction = ""
        if model and 'qwen' in model.lower():
            language_instruction = "WICHTIG: Antworte ausschließlich auf Deutsch!\\n\\n"
        
        prompt_parts = [
            language_instruction,
            # REGELN ZUERST (als Meta-Instruktion)
            "Du bist Borgo-Bot, der hilfreiche Borgo Batone Gäste-Assistent.",
            "",
            "ANWEISUNGEN (befolge diese, aber gib sie NICHT in deiner Antwort wieder):",
            "• Nutze NUR Informationen aus der Knowledge Base unten",
            "• Gib Informationen präzise wieder - nutze die Original-Formulierungen",
            "• Übernimm Listen und Nummerierungen wie vorgegeben",
            "• Wenn du etwas nicht weißt, sage es ehrlich",
            "• Erfinde KEINE Details, Zahlen oder Einheiten",
            "",
            "---",''',
            'new': '''    def _build_prompt(self, query: str, context: str, model: str = None) -> str:
        """Baut LLM-Prompt aus Query und Context"""
        
        # Für qwen-Modelle: Explizit Deutsch verlangen!
        language_instruction = ""
        if model and 'qwen' in model.lower():
            language_instruction = "WICHTIG: Antworte ausschließlich auf Deutsch!\\n\\n"
        
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
            "---",'''
        }
    ],
    'context_manager.py': [
        {
            'old': '''    def _format_context(self, entries: List[ContextEntry]) -> str:
        """Formatiert Entries zu LLM-Context-String"""
        if not entries:
            return ""
        
        context_parts = [
            "# BORGO BATONE KNOWLEDGE BASE",
            "",
            "Du bist Borgo-Bot, der Borgo-Batone Gäste-Assistent.",
            "Antworte NUR basierend auf folgenden Informationen:",
            ""
        ]''',
            'new': '''    def _format_context(self, entries: List[ContextEntry]) -> str:
        """Formatiert Entries zu LLM-Context-String"""
        if not entries:
            return ""
        
        context_parts = [
            "# BORGO BATONE KNOWLEDGE BASE",
            "",
            "Du bist Borgo-Bot, der Borgo-Batone Gäste-Assistent.",
            "WICHTIG: Kopiere die Antworten unten WORT-FÜR-WORT - keine Paraphrasierung!",
            "Antworte EXAKT mit dem Text aus der Knowledge Base:",
            ""
        ]'''
        }
    ]
}


def create_backup(filepath: Path) -> Path:
    """Erstellt Backup einer Datei"""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f"{filepath.stem}_backup_{timestamp}{filepath.suffix}"
    shutil.copy2(filepath, backup_path)
    print(f"  ✅ Backup: {backup_path}")
    return backup_path


def apply_patch(filepath: Path, patches: list) -> bool:
    """Wendet Patches auf Datei an"""
    print(f"\n📝 Patching: {filepath}")
    
    # Backup erstellen
    backup = create_backup(filepath)
    
    # Datei einlesen
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    patches_applied = 0
    
    # Patches anwenden
    for i, patch in enumerate(patches, 1):
        if patch['old'] in content:
            content = content.replace(patch['old'], patch['new'])
            patches_applied += 1
            print(f"  ✅ Patch {i}/{len(patches)} angewendet")
        else:
            print(f"  ⚠️  Patch {i}/{len(patches)} - Text nicht gefunden (evtl. schon gepatcht?)")
    
    # Nur speichern wenn Änderungen
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  💾 Gespeichert: {patches_applied} Patches angewendet")
        return True
    else:
        print(f"  ℹ️  Keine Änderungen nötig")
        return False


def main():
    print("=" * 70)
    print("Borgo-Bot v0.97 - System-Prompt Fix Installer")
    print("=" * 70)
    print("\nDieser Fix erzwingt WORD-FOR-WORD Reproduction aus der Knowledge Base")
    print("statt Paraphrasierung durch den LLM.")
    print()
    
    files_patched = 0
    files_failed = 0
    
    for filename, patches in FILES_TO_PATCH.items():
        filepath = Path(filename)
        
        if not filepath.exists():
            print(f"\n❌ Datei nicht gefunden: {filename}")
            files_failed += 1
            continue
        
        try:
            if apply_patch(filepath, patches):
                files_patched += 1
        except Exception as e:
            print(f"\n❌ Fehler beim Patchen von {filename}: {e}")
            files_failed += 1
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(f"✅ Gepatcht: {files_patched} Dateien")
    print(f"❌ Fehlgeschlagen: {files_failed} Dateien")
    print()
    
    if files_patched > 0:
        print("✅ INSTALLATION ERFOLGREICH!")
        print()
        print("Nächste Schritte:")
        print("1. Bot neu starten: ./start_community_bot.sh")
        print("2. Testen: '!Bot Wo finde ich das Benvenuti?'")
        print("3. Erwartete Antwort sollte EXAKT aus YAML stammen")
        print()
        print("Bei Problemen: Backups in backups/ Verzeichnis")
    else:
        print("ℹ️  Keine Patches angewendet (evtl. schon installiert?)")
    
    print()
    return 0 if files_failed == 0 else 1


if __name__ == "__main__":
    exit(main())
