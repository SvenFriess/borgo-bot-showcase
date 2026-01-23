"""
Borgo-Bot v3.5 - Zentrale Konfiguration
Robuste Bot-Architektur mit Fehlerbehandlung
"""

import re
from pathlib import Path

# ========================================
# GRUNDLEGENDE EINSTELLUNGEN
# ========================================

BOT_VERSION = "3.5"
BOT_NAME = "Borgi 🤖"
BOT_COMMAND_PREFIX = "!bot"

# ========================================
# LLM KONFIGURATION
# ========================================

# Modell-Hierarchie für Fallback
LLM_MODELS = [
    'mistral:7b-instruct',  # Primär
    'granite3.1:2b',         # Fallback 1
    'llama3.2:3b'            # Fallback 2
]

PRIMARY_MODEL = LLM_MODELS[0]
MAX_LLM_RETRIES = 2
LLM_TIMEOUT_SECONDS = 30

# Context-Limits (ERHÖHT für vollständigere Antworten)
MAX_CONTEXT_WORDS = 1200  # War: 800
MAX_CONTEXT_ENTRIES = 4

# ========================================
# INPUT VALIDIERUNG
# ========================================

MIN_INPUT_LENGTH = 3
MAX_INPUT_LENGTH = 500

# Problematische Patterns erkennen
PROBLEMATIC_PATTERNS = [
    r'^\s*$',                    # Nur Leerzeichen
    r'^[!?.,;:\-_/\\]+$',       # Nur Satzzeichen
    r'^(.)\1{20,}',              # 20+ gleiche Zeichen (Spam)
    r'^[0-9]{50,}',              # 50+ Ziffern hintereinander
]

# ========================================
# KEYWORD EXTRAKTION
# ========================================

# Confidence-Schwellenwerte
KEYWORD_CONFIDENCE = {
    'high': 0.95,      # Exakte Treffer
    'medium': 0.75,    # Ähnliche Begriffe
    'low': 0.50        # Schwache Signale
}

# Fuzzy-Match Einstellungen
FUZZY_MATCH_THRESHOLD = 0.80
MIN_KEYWORDS_REQUIRED = 0  # 0 = auch ohne Keywords versuchen

# ========================================
# HALLUZINATIONS-ERKENNUNG
# ========================================

# Bekannte Halluzinations-Muster
HALLUCINATION_PATTERNS = [
    # Falsche Einheiten
    (r'\d+\s*Viertel\s*Tonne', 'Viertel Tonne'),
    (r'\d+\.\d{3,}\s*kg', 'Zu präzise Gewichtsangabe'),
    (r'\d+\s*Gallone[n]?', 'Gallonen (falsche Einheit)'),
    
    # Erfundene Begriffe
    (r'Säureabfalltüchel', 'Erfundener Begriff'),
    (r'Schlangenwurm', 'Erfundenes Tier'),
    (r'Pflanzenmanager', 'Erfundene Rolle'),
    
    # Kontext-Vermischungen
    (r'Rasenmäher.*Pizza', 'Pizza/Rasenmäher verwechselt'),
    (r'Startleine.*Pizzaofen', 'Pizzaofen/Motor verwechselt'),
    
    # HINWEIS: Uhrzeiten-Pattern wurde ENTFERNT!
    # Pool-Öffnungszeiten sind korrekt und sollten nicht als Halluzination gewertet werden
]

# Themen-spezifische Verbotswörter
CONTEXT_MIXING_RULES = {
    'pizza': ['rasenmäher', 'benzin', 'startleine', 'motor'],
    'hunde': ['säureabfalltüchel', 'spülen im hinterhof'],
    'schlangen': ['schlangenwurm', 'absetzen', 'spülen'],
}

# ========================================
# RESPONSE VALIDIERUNG
# ========================================

MIN_RESPONSE_LENGTH = 10
MAX_RESPONSE_LENGTH = 2000

# Qualitäts-Checks
QUALITY_CHECKS = {
    'too_short': MIN_RESPONSE_LENGTH,
    'too_long': MAX_RESPONSE_LENGTH,
    'hallucination': True,
    'context_mixing': True,
    'incomplete': True,
}

# ========================================
# FALLBACK SYSTEM
# ========================================

FALLBACK_RESPONSES = {
    'no_keywords': """Dazu habe ich leider keine Informationen im Benvenuti-Guide. 

Ich kann dir bei folgenden Themen helfen:
• WLAN und Internet
• Pizzaofen Benutzung
• Müll und Recycling
• Hunde im Borgo
• Schlangen und Sicherheit
• Notfälle und Kontakte

Stelle eine konkrete Frage zu einem dieser Themen!""",
    
    'llm_error': """Entschuldigung, ich hatte ein technisches Problem beim Verarbeiten deiner Frage.

Bitte versuche:
1. Deine Frage etwas anders zu formulieren
2. Eine konkretere Frage zu stellen
3. Die Onsite-Gruppe zu kontaktieren

Danke für dein Verständnis! 🙏""",
    
    'ambiguous': """Deine Frage ist mir nicht ganz klar. Bitte formuliere sie konkreter.

Beispiel:
❌ "Info"
✅ "Wie funktioniert der Pizzaofen?"

❌ "Tiere?"
✅ "Sind Hunde im Borgo erlaubt?"

Ich helfe dir gerne weiter! 😊""",
    
    'out_of_scope': """Diese Frage gehört nicht zu meinen Themen. Ich bin spezialisiert auf:

📱 Borgo-Einrichtungen (Pizzaofen, WLAN, etc.)
🏠 Gäste-Services (Anreise, Check-in, Hausregeln)
🚨 Notfälle und Sicherheit

Für andere Themen kontaktiere bitte die Borgo-Community direkt.""",

    'validation_failed': """Ich konnte leider keine sichere Antwort auf deine Frage formulieren.

Bitte kontaktiere die Onsite-Gruppe für verlässliche Informationen.

Du kannst auch im Benvenuti-Guide nachschauen: [Link zur Dokumentation]""",

    'too_many_retries': """Nach mehreren Versuchen konnte ich keine zufriedenstellende Antwort generieren.

Das tut mir leid! Bitte:
• Kontaktiere die Onsite-Gruppe direkt
• Schaue im Benvenuti-Guide nach
• Versuche es später nochmal

Ich lerne ständig dazu! 🤖""",
}

# ========================================
# MONITORING & LOGGING
# ========================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = "borgo_bot_v3_5.log"
LOG_ROTATION_MB = 10
LOG_RETENTION_DAYS = 30

# Performance-Tracking
TRACK_METRICS = {
    'query_processing_time': True,
    'llm_response_time': True,
    'keyword_extraction_time': True,
    'validation_time': True,
    'signal_send_time': True,
}

# Alert-Schwellenwerte
ALERT_THRESHOLDS = {
    'slow_response_seconds': 10,
    'high_error_rate_percent': 20,
    'hallucination_count_per_hour': 5,
}

# ========================================
# YAML KNOWLEDGE BASE
# ========================================

YAML_DB_PATH = Path("borgo_knowledge_base.yaml")
YAML_CATEGORIES = [
    'basics',
    'facilities',
    'safety',
    'rules',
    'contact',
    'emergency',
    'faq',
    'seasonal',
    'technical',
    'general'
]

# ========================================
# SIGNAL INTEGRATION
# ========================================

SIGNAL_CLI_PATH = "/path/to/signal-cli"
SIGNAL_ACCOUNT = "+49XXXXXXXXXX"
MAX_MESSAGE_LENGTH = 4096  # Signal-Limit

# Worker-Konfiguration
NUM_WORKERS = 3
QUEUE_TIMEOUT_SECONDS = 60

# ========================================
# DEVELOPMENT & TESTING
# ========================================

DEBUG_MODE = False
TEST_MODE = False
DRY_RUN = False  # Keine echten Signal-Nachrichten

# Test-Nachrichten für Validierung
TEST_QUERIES = [
    "Wie viel Mehl für 24 Personen Pizza?",
    "Ich habe eine Schlange gesehen",
    "Sind Hunde erlaubt?",
    "Wie funktioniert der Pizzaofen?",
    "WLAN Passwort?",
]

# ========================================
# FEATURES FLAGS
# ========================================

FEATURES = {
    'input_validation': True,
    'keyword_confidence_scoring': True,
    'context_isolation': True,
    'hallucination_detection': True,
    'multi_model_fallback': True,
    'fuzzy_keyword_matching': True,
    'response_validation': True,
    'detailed_logging': True,
}

# ========================================
# HILFSFUNKTIONEN
# ========================================

def get_feature_status():
    """Gibt Status aller Features zurück"""
    enabled = [k for k, v in FEATURES.items() if v]
    disabled = [k for k, v in FEATURES.items() if not v]
    return {
        'enabled': enabled,
        'disabled': disabled,
        'total': len(FEATURES)
    }

def validate_config():
    """Validiert Konfiguration"""
    errors = []
    
    # Prüfe Modell-Liste
    if not LLM_MODELS:
        errors.append("LLM_MODELS darf nicht leer sein")
    
    # Prüfe YAML-Pfad
    if not YAML_DB_PATH.exists():
        errors.append(f"YAML-Datei nicht gefunden: {YAML_DB_PATH}")
    
    # Prüfe Schwellenwerte
    if MIN_INPUT_LENGTH < 1:
        errors.append("MIN_INPUT_LENGTH muss >= 1 sein")
    
    return errors

if __name__ == "__main__":
    print(f"Borgo-Bot v{BOT_VERSION} Configuration")
    print("=" * 50)
    
    # Feature-Status
    status = get_feature_status()
    print(f"\n✅ Aktivierte Features: {len(status['enabled'])}/{status['total']}")
    for feature in status['enabled']:
        print(f"   • {feature}")
    
    # Validierung
    print("\n🔍 Konfiguration validieren...")
    errors = validate_config()
    if errors:
        print("❌ Fehler gefunden:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("✅ Konfiguration OK!")
    
    print("\n" + "=" * 50)
