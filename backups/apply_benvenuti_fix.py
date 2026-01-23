#!/usr/bin/env python3
"""
Borgo-Bot v0.96 - Benvenuti Link Fix Installer
Automatisches Update der Knowledge Base mit korrektem Piazza-Link
"""

import yaml
import shutil
from datetime import datetime
from pathlib import Path

# Konfiguration
YAML_DB_PATH = Path("borgo_knowledge_base.yaml")
BACKUP_DIR = Path("backups")

# Der Fix
BENVENUTI_FIX = {
    'benvenuti_guide': {
        'category': 'basics',
        'keywords': [
            'benvenuti',
            'guide',
            'anleitung',
            'handbuch',
            'dokumentation',
            'gästeinformation',
            'guest guide',
            'willkommen',
            'infos',
            'informationen'
        ],
        'synonyms': [
            'benvenuti guide',
            'guest guide',
            'gästehandbuch',
            'borgo handbuch',
            'willkommens guide',
            'info dokument',
            'borgo guide',
            'benvenuti pdf',
            'gästeinfo'
        ],
        'confidence': 'high',
        'answer': (
            'Das Benvenuti-Guide findest du auf der Piazza:\n'
            'https://piazza.borgo-batone.com/node/819?language_content_entity=en\n\n'
            'Ich empfehle dir, es vor der Anreise durchzulesen!'
        ),
        'notes': (
            'WICHTIG: Nicht mehr auf "Buchungsbestätigung" verweisen! '
            'Der Link ist immer auf der Piazza verfügbar.'
        )
    }
}


def create_backup(yaml_path: Path) -> Path:
    """Erstellt Backup der aktuellen YAML-Datei"""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f"borgo_kb_backup_{timestamp}.yaml"
    shutil.copy2(yaml_path, backup_path)
    print(f"✅ Backup erstellt: {backup_path}")
    return backup_path


def load_yaml(yaml_path: Path) -> dict:
    """Lädt YAML Knowledge Base"""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml(yaml_path: Path, data: dict):
    """Speichert YAML Knowledge Base"""
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, 
                  allow_unicode=True, sort_keys=False)


def apply_fix(data: dict) -> dict:
    """Wendet Benvenuti-Link-Fix an"""
    # Suche nach existierenden benvenuti Einträgen
    old_entries = []
    for key in list(data.keys()):
        if 'benvenuti' in key.lower():
            old_entries.append(key)
            print(f"⚠️  Alter Eintrag gefunden: {key}")
    
    # Entferne alte Einträge
    for key in old_entries:
        del data[key]
        print(f"🗑️  Gelöscht: {key}")
    
    # Füge neuen Fix hinzu
    data.update(BENVENUTI_FIX)
    print(f"✅ Neuer Eintrag hinzugefügt: benvenuti_guide")
    
    return data


def validate_fix(data: dict) -> bool:
    """Validiert, ob Fix korrekt angewendet wurde"""
    if 'benvenuti_guide' not in data:
        print("❌ Validierung fehlgeschlagen: benvenuti_guide nicht gefunden")
        return False
    
    entry = data['benvenuti_guide']
    correct_link = 'https://piazza.borgo-batone.com/node/819?language_content_entity=en'
    
    if correct_link not in entry['answer']:
        print("❌ Validierung fehlgeschlagen: Korrekter Link nicht in Antwort")
        return False
    
    if 'buchungsbestätigung' in entry['answer'].lower():
        print("❌ Validierung fehlgeschlagen: Alte Buchungsbestätigung noch vorhanden")
        return False
    
    print("✅ Validierung erfolgreich!")
    return True


def main():
    print("=" * 60)
    print("Borgo-Bot v0.96 - Benvenuti Link Fix Installer")
    print("=" * 60)
    print()
    
    # Prüfe ob YAML existiert
    if not YAML_DB_PATH.exists():
        print(f"❌ Fehler: {YAML_DB_PATH} nicht gefunden!")
        print("   Bitte Pfad in Script anpassen.")
        return 1
    
    print(f"📁 Knowledge Base: {YAML_DB_PATH}")
    print()
    
    # Backup erstellen
    backup_path = create_backup(YAML_DB_PATH)
    print()
    
    # YAML laden
    print("📖 Lade Knowledge Base...")
    data = load_yaml(YAML_DB_PATH)
    print(f"✅ {len(data)} Einträge geladen")
    print()
    
    # Fix anwenden
    print("🔧 Wende Fix an...")
    data = apply_fix(data)
    print()
    
    # Validieren
    print("🔍 Validiere Fix...")
    if not validate_fix(data):
        print()
        print("❌ Fix-Installation fehlgeschlagen!")
        print(f"   Backup wiederherstellen: cp {backup_path} {YAML_DB_PATH}")
        return 1
    print()
    
    # Speichern
    print("💾 Speichere Knowledge Base...")
    save_yaml(YAML_DB_PATH, data)
    print("✅ Gespeichert!")
    print()
    
    # Zusammenfassung
    print("=" * 60)
    print("✅ INSTALLATION ERFOLGREICH!")
    print("=" * 60)
    print()
    print("Nächste Schritte:")
    print("1. Bot neu starten")
    print("2. Testen mit: 'Wo finde ich das Benvenuti?'")
    print("3. Erwartete Antwort sollte Piazza-Link enthalten:")
    print("   https://piazza.borgo-batone.com/node/819?language_content_entity=en")
    print()
    print(f"Bei Problemen: Backup unter {backup_path}")
    print()
    
    return 0


if __name__ == "__main__":
    exit(main())
