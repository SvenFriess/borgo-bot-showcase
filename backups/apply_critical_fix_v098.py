#!/usr/bin/env python3
"""
Borgo-Bot v0.98 - CRITICAL FIX
Liest 'answer' statt 'content' aus YAML Knowledge Base

Dies ist DER kritische Fix der das ganze System repariert!
"""

import shutil
from pathlib import Path
from datetime import datetime

BACKUP_DIR = Path("backups")

def create_backup(filepath: Path) -> Path:
    """Erstellt Backup einer Datei"""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f"{filepath.stem}_backup_{timestamp}{filepath.suffix}"
    shutil.copy2(filepath, backup_path)
    print(f"  ✅ Backup: {backup_path}")
    return backup_path


def apply_fix():
    """Wendet den kritischen YAML-Field-Fix an"""
    
    filepath = Path("context_manager.py")
    
    if not filepath.exists():
        print(f"❌ Datei nicht gefunden: {filepath}")
        return False
    
    print(f"\n📝 Patching: {filepath}")
    
    # Backup erstellen
    backup = create_backup(filepath)
    
    # Datei einlesen
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Finde und ändere die betroffenen Zeilen
    changes_made = 0
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Zeile 132: content=data.get('content', '')
        if line_num == 132 and "content=data.get('content'" in line:
            old_line = line
            lines[i] = line.replace("data.get('content'", "data.get('answer'")
            print(f"  ✅ Zeile 132: 'content' → 'answer'")
            changes_made += 1
        
        # Zeile 133: word_count=len(data.get('content', '').split())
        elif line_num == 133 and "data.get('content'" in line:
            old_line = line
            lines[i] = line.replace("data.get('content'", "data.get('answer'")
            print(f"  ✅ Zeile 133: 'content' → 'answer'")
            changes_made += 1
    
    if changes_made > 0:
        # Speichern
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"  💾 Gespeichert: {changes_made} Änderungen")
        return True
    else:
        print(f"  ⚠️  Keine Änderungen gefunden (evtl. schon gepatcht?)")
        return False


def validate_fix():
    """Validiert ob Fix korrekt angewendet wurde"""
    filepath = Path("context_manager.py")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Prüfe ob 'answer' jetzt verwendet wird
    if "content=data.get('answer'" in content:
        print("  ✅ Zeile 132 korrekt gepatcht")
    else:
        print("  ❌ Zeile 132 NICHT korrekt gepatcht")
        return False
    
    if "len(data.get('answer'" in content:
        print("  ✅ Zeile 133 korrekt gepatcht")
    else:
        print("  ❌ Zeile 133 NICHT korrekt gepatcht")
        return False
    
    # Prüfe ob alte 'content' Referenzen noch existieren (in diesem Context)
    lines_with_content = []
    for i, line in enumerate(content.split('\n'), 1):
        if i >= 125 and i <= 140:  # Nur im relevanten Bereich
            if "data.get('content'" in line:
                lines_with_content.append(i)
    
    if lines_with_content:
        print(f"  ⚠️  Noch 'content' Referenzen in Zeilen: {lines_with_content}")
        return False
    
    return True


def main():
    print("=" * 70)
    print("Borgo-Bot v0.98 - CRITICAL FIX Installer")
    print("=" * 70)
    print("\nProblem: Bot liest 'content' statt 'answer' aus YAML")
    print("Lösung: Ändert Zeilen 132 & 133 in context_manager.py")
    print()
    
    # Fix anwenden
    success = apply_fix()
    
    if not success:
        print("\n❌ Fix konnte nicht angewendet werden!")
        return 1
    
    print()
    
    # Validieren
    print("🔍 Validiere Fix...")
    if validate_fix():
        print()
        print("=" * 70)
        print("✅ INSTALLATION ERFOLGREICH!")
        print("=" * 70)
        print()
        print("Der Bot liest jetzt 'answer' aus der YAML!")
        print()
        print("Nächste Schritte:")
        print("1. Bot neu starten: ./start_community_bot.sh")
        print("2. Testen: '!Bot Wo finde ich das Benvenuti?'")
        print("3. Erwartung: Vollständiger Text aus YAML, nicht nur Kategorie")
        print()
        print("Erwartete Antwort:")
        print("---")
        print("Das Benvenuti-Guide findest du auf der Piazza:")
        print("https://piazza.borgo-batone.com/node/819?language_content_entity=en")
        print()
        print("Ich empfehle dir, es vor der Anreise durchzulesen!")
        print("---")
        print()
        return 0
    else:
        print()
        print("❌ Validierung fehlgeschlagen!")
        print("Bitte Backup wiederherstellen und manuell prüfen.")
        return 1


if __name__ == "__main__":
    exit(main())
