"""
Zentrale Konfiguration für Borgo-Bot v3.5
UPDATED: Multi-Gruppen Support für DEV + Community-Test
"""

# =====================================================================================
# BASIS-INFO
# =====================================================================================

BOT_VERSION = "3.6"
BOT_NAME = "Borgo-Bot"
BOT_COMMAND_PREFIX = "!bot"

# =====================================================================================
# SIGNAL KONFIGURATION
# =====================================================================================

# Voller Pfad zur signal-cli Installation
SIGNAL_CLI_PATH = "/opt/homebrew/bin/signal-cli"

# Account-Nummer des Bots
SIGNAL_ACCOUNT = "+4915755901211"
SIGNAL_PHONE_NUMBER = "+4915755901211"  # Alias

# ✨ NEU: Multi-Gruppen Support
# Option 1: Liste von Gruppen (DEV + Community-Test)
SIGNAL_GROUP_ID = [
    "i4UA7hmoTi1HYq+vO0/NvyR/MEcqKfLTrODlw9W8dDM=",  # Borgo-Bot DEV
    "GIRAgoi6g+wpsFCliNWoXPXAErU/li2tW8TQ1xKhqcE="   # Borgo-Bot Community-Test
]

# Option 2: Alle Gruppen (keine Filterung)
# SIGNAL_GROUP_ID = None

# Option 3: Nur eine Gruppe (alte Methode)
# SIGNAL_GROUP_ID = "i4UA7hmoTi1HYq+vO0/NvyR/MEcqKfLTrODlw9W8dDM="

# Signal-CLI Settings
SIGNAL_RECEIVE_TIMEOUT = 45
SIGNAL_RECEIVE_BACKOFF = [1, 2, 5, 10]
MAX_MESSAGE_LENGTH = 4096  # Signal-Limit

# =====================================================================================
# LLM KONFIGURATION
# =====================================================================================

# Modell-Hierarchie für Fallback
LLM_MODELS = [
    'mistral:instruct',     # Primär
    'granite3.3:2b',        # Fallback 1
    'llama3.2:latest'       # Fallback 2
]

PRIMARY_MODEL = LLM_MODELS[0]
SECONDARY_MODEL = 'granite3.3:2b'

MAX_LLM_RETRIES = 2
LLM_TIMEOUT_SECONDS = 30
MODEL_TIMEOUT_SECONDS = 30

# Context-Limits
MAX_CONTEXT_WORDS = 800
MAX_CONTEXT_ENTRIES = 3

# =====================================================================================
# INPUT VALIDATION
# =====================================================================================

MIN_INPUT_LENGTH = 3
MAX_INPUT_LENGTH = 500

PROBLEMATIC_PATTERNS = [
    r'^\s*$',
    r'^[!?.,;:\-_/\\]+$',
    r'^(.)\1{20,}',
    r'^[0-9]{50,}',
]

INVALID_INPUT_PATTERNS = [
    r"^[!?.,;:\-\s]+$",
    r"^[0-9\s]+$",
    r"^[A-Za-z]{1,2}$",
]

QUICK_RESPONSES = {
    "ping": "pong",
    "test": "Borgo-Bot läuft.",
    "status": "Borgo-Bot online und bereit.",
}

# =====================================================================================
# KEYWORD EXTRAKTION
# =====================================================================================

KEYWORD_CONFIDENCE = {
    'high': 0.95,
    'medium': 0.75,
    'low': 0.50
}

FUZZY_MATCH_THRESHOLD = 80
MIN_KEYWORDS_REQUIRED = 0

# =====================================================================================
# CONTEXT MANAGER / YAML HANDLING
# =====================================================================================

CONTEXT_MIXING_RULES = {
    'pizza': ['rasenmäher', 'benzin', 'startleine', 'motor'],
    'hunde': ['säureabfalltüchel', 'spülen im hinterhof'],
    'schlangen': ['schlangenwurm', 'absetzen', 'spülen'],
}

CONTEXT_FALLBACK_CATEGORIES = {
    "tiere": "tierinfo",
    "notfall": "emergency",
    "pizza": "cooking",
    "heizung": "heating",
}

YAML_DB_PATH = "borgo_knowledge_base.yaml"
YAML_CATEGORIES = [
    'basics', 'facilities', 'safety', 'rules', 'contact',
    'emergency', 'faq', 'seasonal', 'technical', 'general'
]

# =====================================================================================
# HALLUZINATIONS-ERKENNUNG
# =====================================================================================

HALLUCINATION_PATTERNS = [
    (r'\d+\s*Viertel\s*Tonne', 'Viertel Tonne'),
    (r'\d+\.\d{3,}\s*kg', 'Zu präzise Gewichtsangabe'),
    (r'\d+\s*Gallone[n]?', 'Gallonen (falsche Einheit)'),
    (r'Säureabfalltüchel', 'Erfundener Begriff'),
    (r'Schlangenwurm', 'Erfundenes Tier'),
    (r'Pflanzenmanager', 'Erfundene Rolle'),
    (r'Rasenmäher.*Pizza', 'Pizza/Rasenmäher verwechselt'),
    (r'Startleine.*Pizzaofen', 'Pizzaofen/Motor verwechselt'),
]

# =====================================================================================
# RESPONSE VALIDATION
# =====================================================================================

MIN_RESPONSE_LENGTH = 10
MAX_RESPONSE_LENGTH = 2000

QUALITY_CHECKS = {
    'too_short': MIN_RESPONSE_LENGTH,
    'too_long': MAX_RESPONSE_LENGTH,
    'hallucination': True,
    'context_mixing': True,
    'incomplete': True,
}

FORBIDDEN_PHRASES = [
    "Ich bin ein Sprachmodell",
    "Als KI",
    "OpenAI",
    "ChatGPT",
    "Ich bin Claude",
]

# =====================================================================================
# FALLBACK SYSTEM
# =====================================================================================

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

    'unknown': """Entschuldigung, ein unerwarteter Fehler ist aufgetreten.

Bitte versuche es erneut oder kontaktiere die Onsite-Gruppe für Hilfe.

Die technischen Details wurden geloggt. 🔧""",
    
    'NO_KEYWORDS': "Ich konnte keine relevanten Informationen finden.",
    'AMBIGUOUS': "Deine Frage ist mehrdeutig – kannst du sie präzisieren?",
    'VALIDATION_FAILED': "Die Eingabe enthält problematische Inhalte.",
    'LLM_ERROR': "Es gab ein Problem beim Generieren der Antwort.",
    'UNKNOWN': "Ein unerwarteter Fehler ist aufgetreten.",
}

# =====================================================================================
# MONITORING & LOGGING
# =====================================================================================

LOG_LEVEL = "INFO"
LOG_FILE = "borgo_bot_v3_5.log"
LOG_ROTATION_MB = 10
LOG_RETENTION_DAYS = 30

METRICS_FILE = "borgo_bot_metrics.json"
MAX_LOG_ENTRIES = 5000

TRACK_METRICS = {
    'query_processing_time': True,
    'llm_response_time': True,
    'keyword_extraction_time': True,
    'validation_time': True,
    'signal_send_time': True,
}

ALERT_THRESHOLDS = {
    'slow_response_seconds': 10,
    'high_error_rate_percent': 20,
    'hallucination_count_per_hour': 5,
}

# =====================================================================================
# WORKER KONFIGURATION
# =====================================================================================

NUM_WORKERS = 3
QUEUE_TIMEOUT_SECONDS = 60

# =====================================================================================
# DEVELOPMENT & TESTING
# =====================================================================================

DEBUG_MODE = False
TEST_MODE = False
DRY_RUN = False

TEST_QUERIES = [
    "Wie viel Mehl für 24 Personen Pizza?",
    "Ich habe eine Schlange gesehen",
    "Sind Hunde erlaubt?",
    "Wie funktioniert der Pizzaofen?",
    "WLAN Passwort?",
]

# =====================================================================================
# FEATURES FLAGS
# =====================================================================================

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

# =====================================================================================
# HILFSFUNKTIONEN
# =====================================================================================

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
    
    if not LLM_MODELS:
        errors.append("LLM_MODELS darf nicht leer sein")
    
    if not SIGNAL_ACCOUNT:
        errors.append("SIGNAL_ACCOUNT muss gesetzt sein")
    
    if MIN_INPUT_LENGTH < 1:
        errors.append("MIN_INPUT_LENGTH muss >= 1 sein")
    
    return errors

if __name__ == "__main__":
    print(f"Borgo-Bot v{BOT_VERSION} Configuration")
    print("=" * 50)
    
    status = get_feature_status()
    print(f"\n✅ Aktivierte Features: {len(status['enabled'])}/{status['total']}")
    for feature in status['enabled']:
        print(f"   • {feature}")
    
    print("\n🔍 Konfiguration validieren...")
    errors = validate_config()
    if errors:
        print("❌ Fehler gefunden:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("✅ Konfiguration OK!")
    
    # Zeige Gruppen-Konfiguration
    print(f"\n📡 Signal-Gruppen:")
    if SIGNAL_GROUP_ID is None:
        print("   ALLE Gruppen erlaubt")
    elif isinstance(SIGNAL_GROUP_ID, list):
        print(f"   {len(SIGNAL_GROUP_ID)} Gruppen konfiguriert:")
        for i, gid in enumerate(SIGNAL_GROUP_ID, 1):
            print(f"   {i}. {gid[:30]}...")
    else:
        print(f"   1 Gruppe: {SIGNAL_GROUP_ID[:30]}...")
    
    print("\n" + "=" * 50)
