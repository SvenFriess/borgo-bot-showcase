#!/usr/bin/env python3
"""
Borgo-Bot v0.99 - COMPREHENSIVE FIX
1. Ändert ALLE 'content:' zu 'answer:' in YAML
2. Entfernt doppelte FALLBACK_RESPONSES Definition
"""

import shutil
import re
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


def fix_yaml():
    """Ändert alle 'content:' zu 'answer:' in YAML"""
    filepath = Path("borgo_knowledge_base.yaml")
    
    if not filepath.exists():
        print(f"❌ {filepath} nicht gefunden!")
        return False
    
    print(f"\n📝 Fixing YAML: {filepath}")
    backup = create_backup(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Zähle content: Vorkommen
    content_count = content.count('\n  content:')
    print(f"  📊 Gefunden: {content_count} 'content:' Felder")
    
    # Ersetze alle '  content:' mit '  answer:'
    # WICHTIG: Nur auf der richtigen Einrückungsebene!
    new_content = content.replace('\n  content:', '\n  answer:')
    
    # Prüfe ob Änderungen gemacht wurden
    new_count = new_content.count('\n  answer:')
    changed = content_count
    
    if changed > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  ✅ Geändert: {changed} Felder von 'content:' zu 'answer:'")
        return True
    else:
        print(f"  ℹ️  Keine Änderungen nötig")
        return False


def fix_fallback_responses():
    """Entfernt doppelte FALLBACK_RESPONSES Definition"""
    filepath = Path("config_multi_bot.py")
    
    if not filepath.exists():
        print(f"❌ {filepath} nicht gefunden!")
        return False
    
    print(f"\n📝 Fixing Fallback: {filepath}")
    backup = create_backup(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Finde beide FALLBACK_RESPONSES Definitionen
    first_def = None
    second_def = None
    
    for i, line in enumerate(lines, 1):
        if 'FALLBACK_RESPONSES = {' in line:
            if first_def is None:
                first_def = i
                print(f"  📍 Erste Definition: Zeile {i}")
            else:
                second_def = i
                print(f"  📍 Zweite Definition: Zeile {i}")
                break
    
    if not second_def:
        print(f"  ℹ️  Nur eine FALLBACK_RESPONSES Definition gefunden")
        return False
    
    # Finde Ende der zweiten Definition
    second_end = None
    brace_count = 0
    for i in range(second_def - 1, len(lines)):
        line = lines[i]
        brace_count += line.count('{') - line.count('}')
        if brace_count == 0 and i > second_def - 1:
            second_end = i + 1
            break
    
    if second_end:
        # Lösche zweite Definition
        print(f"  🗑️  Lösche Zeilen {second_def} bis {second_end}")
        del lines[second_def - 1:second_end]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"  ✅ Zweite FALLBACK_RESPONSES Definition entfernt")
        return True
    else:
        print(f"  ⚠️  Konnte Ende der zweiten Definition nicht finden")
        return False


def validate_fixes():
    """Validiert alle Fixes"""
    print("\n🔍 Validierung...")
    
    issues = []
    
    # Validiere YAML
    yaml_path = Path("borgo_knowledge_base.yaml")
    if yaml_path.exists():
        with open(yaml_path, 'r') as f:
            yaml_content = f.read()
        
        content_count = yaml_content.count('\n  content:')
        answer_count = yaml_content.count('\n  answer:')
        
        print(f"  📊 YAML: {answer_count} 'answer:' Felder, {content_count} 'content:' Felder")
        
        if content_count > 0:
            issues.append(f"YAML hat noch {content_count} 'content:' Felder")
        
        if answer_count < 50:
            issues.append(f"YAML hat nur {answer_count} 'answer:' Felder (erwartet: ~56)")
    
    # Validiere Config
    config_path = Path("config_multi_bot.py")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        fallback_count = config_content.count('FALLBACK_RESPONSES = {')
        print(f"  📊 Config: {fallback_count} FALLBACK_RESPONSES Definitionen")
        
        if fallback_count > 1:
            issues.append(f"Config hat noch {fallback_count} FALLBACK_RESPONSES Definitionen")
    
    return issues


def main():
    print("=" * 70)
    print("Borgo-Bot v0.99 - COMPREHENSIVE FIX")
    print("=" * 70)
    print("\nProbleme:")
    print("1. 55 YAML-Einträge haben 'content:' statt 'answer:'")
    print("2. Doppelte FALLBACK_RESPONSES Definition in config")
    print()
    
    yaml_fixed = fix_yaml()
    config_fixed = fix_fallback_responses()
    
    issues = validate_fixes()
    
    print()
    print("=" * 70)
    
    if not issues:
        print("✅ ALLE FIXES ERFOLGREICH!")
        print("=" * 70)
        print()
        print("Änderungen:")
        if yaml_fixed:
            print("  ✅ YAML: 'content:' → 'answer:'")
        if config_fixed:
            print("  ✅ Config: Doppelte FALLBACK_RESPONSES entfernt")
        print()
        print("Nächste Schritte:")
        print("1. Bot neu starten: ./start_community_bot.sh")
        print("2. Testen: '!Bot Wie viel Mehl für Pizza?'")
        print("3. Context sollte jetzt > 100 Wörter haben")
        print("4. Bot sollte nicht mehr crashen")
        print()
        return 0
    else:
        print("⚠️  VALIDIERUNG MIT PROBLEMEN")
        print("=" * 70)
        print()
        print("Gefundene Probleme:")
        for issue in issues:
            print(f"  ❌ {issue}")
        print()
        print("Bitte Backups prüfen und manuell fixen!")
        print()
        return 1


if __name__ == "__main__":
    exit(main())
