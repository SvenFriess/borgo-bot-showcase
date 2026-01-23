#!/usr/bin/env python3
"""
Borgo-Bot v0.99 - Hotfix für fehlendes 'unknown' Fallback
Verhindert KeyError crash im Fallback-System
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
    """Fügt fehlenden 'unknown' Fallback hinzu"""
    
    # Prüfe beide möglichen Orte für FALLBACK_RESPONSES
    files_to_check = [
        Path("fallback_system.py"),
        Path("config_multi_bot.py"),
        Path("config.py")
    ]
    
    fixed_files = []
    
    for filepath in files_to_check:
        if not filepath.exists():
            continue
        
        print(f"\n📝 Checking: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Prüfe ob FALLBACK_RESPONSES definiert ist
        if 'FALLBACK_RESPONSES' not in content:
            print(f"  ℹ️  Keine FALLBACK_RESPONSES in {filepath}")
            continue
        
        # Prüfe ob 'unknown' schon existiert
        if "'unknown':" in content or '"unknown":' in content:
            print(f"  ✅ 'unknown' Fallback bereits vorhanden")
            continue
        
        # Backup erstellen
        backup = create_backup(filepath)
        
        # Füge 'unknown' Fallback hinzu
        # Suche nach dem Ende von FALLBACK_RESPONSES
        if "FALLBACK_RESPONSES = {" in content:
            # Finde die letzte schließende Klammer des FALLBACK_RESPONSES Dict
            lines = content.split('\n')
            fallback_start = None
            fallback_end = None
            brace_count = 0
            
            for i, line in enumerate(lines):
                if 'FALLBACK_RESPONSES = {' in line:
                    fallback_start = i
                    brace_count = 1
                elif fallback_start is not None:
                    brace_count += line.count('{') - line.count('}')
                    if brace_count == 0:
                        fallback_end = i
                        break
            
            if fallback_start and fallback_end:
                # Füge 'unknown' Fallback vor der letzten Klammer ein
                unknown_fallback = '''    
    'unknown': """Entschuldigung, ich hatte ein unerwartetes Problem beim Verarbeiten deiner Frage.

Bitte versuche:
1. Deine Frage etwas anders zu formulieren
2. Die Onsite-Gruppe zu kontaktieren

Danke für dein Verständnis! 🙏""",'''
                
                lines.insert(fallback_end, unknown_fallback)
                
                content = '\n'.join(lines)
                
                # Speichern
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"  ✅ 'unknown' Fallback hinzugefügt")
                fixed_files.append(filepath)
    
    return fixed_files


def main():
    print("=" * 70)
    print("Borgo-Bot v0.99 - Fallback Hotfix")
    print("=" * 70)
    print("\nProblem: KeyError 'unknown' im Fallback-System")
    print("Lösung: Fügt fehlenden 'unknown' Fallback hinzu")
    print()
    
    fixed = apply_fix()
    
    print()
    print("=" * 70)
    
    if fixed:
        print("✅ HOTFIX ERFOLGREICH!")
        print("=" * 70)
        print()
        print(f"Geänderte Dateien: {len(fixed)}")
        for f in fixed:
            print(f"  • {f}")
        print()
        print("Nächste Schritte:")
        print("1. Bot neu starten: ./start_community_bot.sh")
        print("2. Erneut testen: '!Bot Wie viel Mehl für Pizza?'")
        print("3. Der Bot sollte jetzt einen Fallback geben statt zu crashen")
        print()
    else:
        print("ℹ️  KEIN FIX NÖTIG")
        print("=" * 70)
        print()
        print("Entweder:")
        print("• 'unknown' Fallback ist bereits vorhanden")
        print("• FALLBACK_RESPONSES nicht gefunden")
        print()
        print("Bitte manuell prüfen!")
        print()
    
    return 0


if __name__ == "__main__":
    exit(main())
