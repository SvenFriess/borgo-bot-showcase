"""
Zentrale Konfiguration für Borgo-Bot v3.7
MULTI-BOT ARCHITEKTUR: Drei logisch getrennte Bots in einer Instanz
"""

import os

# =====================================================================================
# BASIS-INFO
# =====================================================================================

BOT_VERSION = "3.7"
BOT_COMMAND_PREFIX = "!bot"

# =====================================================================================
# SIGNAL KONFIGURATION
# =====================================================================================

# Voller Pfad zur signal-cli Installation
SIGNAL_CLI_PATH = "/opt/homebrew/bin/signal-cli"

# Account-Nummer des Bots
SIGNAL_ACCOUNT = "+4915755901211"
SIGNAL_PHONE_NUMBER = "+4915755901211"  # Alias

# Socket-Pfad für Daemon-Kommunikation
SIGNAL_SOCKET_PATH = '/tmp/signal-cli-socket'

# Signal-CLI Settings
SIGNAL_RECEIVE_TIMEOUT = 45
SIGNAL_RECEIVE_BACKOFF = [1, 2, 5, 10]
MAX_MESSAGE_LENGTH = 4096  # Signal-Limit

# =====================================================================================
# GRUPPEN-ROUTING & BOT-DEFINITIONEN
# =====================================================================================

# Signal-Gruppen-IDs (aus listGroups)
GROUP_IDS = {
    'dev': 'i4UA7hmoTi1HYq+vO0/NvyR/MEcqKfLTrODlw9W8dDM=',
    'test': '21oiqcpO37/ScyKFhmctf/45MQ5QYdN2h/VQp9WMKCM=',
    'community_test': 'GIRAgoi6g+wpsFCliNWoXPXAErU/li2tW8TQ1xKhqcE=',
}

# Erlaubte Gruppen (für strikte Kontrolle)
ALLOWED_GROUP_IDS = list(GROUP_IDS.values())

# Bot-Namen pro Gruppe
BOT_NAMES = {
    'dev': 'Borgi-DEV 🔧',
    'test': 'Borgi-TEST 🧪',
    'community_test': 'Borgi 🤖',
}

# =====================================================================================
# DEV BOT KONFIGURATION
# =====================================================================================

DEV_BOT_CONFIG = {
    'name': BOT_NAMES['dev'],
    'yaml_path': 'borgo_knowledge_base.yaml',  # oder borgo_knowledge_base_dev.yaml
    'ollama_url': 'http://localhost:11434',
    
    # LLM Settings (EXPERIMENTELL - hier kannst du andere Modelle testen!)
    'llm_models': [
        'qwen2.5:7b',      # Experimentelles Modell für DEV
        'mistral:instruct',     # Fallback
        'granite3.3:2b',
    ],
    'primary_model': 'mistral:instruct',
    'max_llm_retries': 3,
    'llm_timeout_seconds': 45,
    
    # Context Settings
    'max_context_words': 1000,  # Mehr Context für DEV-Tests
    'max_context_entries': 5,
    
    # Features (kannst du einzeln togglen)
    'features': {
        'input_validation': True,
        'keyword_confidence_scoring': True,
        'context_isolation': True,
        'hallucination_detection': True,
        'multi_model_fallback': True,
        'fuzzy_keyword_matching': True,
        'response_validation': True,
        'detailed_logging': True,
    },
    
    # Debug Settings
    'debug_mode': True,
    'log_level': 'DEBUG',
}

# =====================================================================================
# TEST BOT KONFIGURATION
# =====================================================================================

TEST_BOT_CONFIG = {
    'name': BOT_NAMES['test'],
    'yaml_path': 'borgo_knowledge_base.yaml',
    'ollama_url': 'http://localhost:11434',
    
    # LLM Settings (Standard)
    'llm_models': [
        'mistral:instruct',
        'granite3.3:2b',
        'qwen2.5:7b'
    ],
    'primary_model': 'mistral:instruct',
    'max_llm_retries': 2,
    'llm_timeout_seconds': 30,
    
    # Context Settings
    'max_context_words': 800,
    'max_context_entries': 3,
    
    # Features
    'features': {
        'input_validation': True,
        'keyword_confidence_scoring': True,
        'context_isolation': True,
        'hallucination_detection': True,
        'multi_model_fallback': True,
        'fuzzy_keyword_matching': True,
        'response_validation': True,
        'detailed_logging': True,
    },
    
    # Debug Settings
    'debug_mode': False,
    'log_level': 'INFO',
}

# =====================================================================================
# COMMUNITY-TEST BOT KONFIGURATION
# =====================================================================================

COMMUNITY_TEST_BOT_CONFIG = {
    'name': BOT_NAMES['community_test'],
    'yaml_path': 'borgo_knowledge_base.yaml',
    'ollama_url': 'http://localhost:11434',
    
    # LLM Settings (Production-ready)
    'llm_models': [
        'mistral:instruct',
        'granite3.3:2b',
        'qwen2.5:7b'
    ],
    'primary_model': 'mistral:instruct',
    'max_llm_retries': 2,
    'llm_timeout_seconds': 30,
    
    # Context Settings
    'max_context_words': 800,
    'max_context_entries': 3,
    
    # Features
    'features': {
        'input_validation': True,
        'keyword_confidence_scoring': True,
        'context_isolation': True,
        'hallucination_detection': True,
        'multi_model_fallback': True,
        'fuzzy_keyword_matching': True,
        'response_validation': True,
        'detailed_logging': True,
    },
    
    # Debug Settings
    'debug_mode': False,
    'log_level': 'INFO',
}

# =====================================================================================
# SHARED SETTINGS (für alle Bots gleich)
# =====================================================================================

# Input Validation
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

# Keyword Extraction
KEYWORD_CONFIDENCE = {
    'high': 0.95,
    'medium': 0.75,
    'low': 0.50
}

FUZZY_MATCH_THRESHOLD = 80
MIN_KEYWORDS_REQUIRED = 0

# Context Management
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

YAML_CATEGORIES = [
    'basics', 'facilities', 'safety', 'rules', 'contact',
    'emergency', 'faq', 'seasonal', 'technical', 'general'
]

# Hallucination Detection
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

# Response Validation
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

# Fallback System
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
}

# Monitoring & Logging
LOG_FILE = "borgo_bot_multi.log"
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

# Worker Configuration
NUM_WORKERS = 3
QUEUE_TIMEOUT_SECONDS = 60

# =====================================================================================
# HILFSFUNKTIONEN
# =====================================================================================

def get_bot_config(group_id: str) -> dict:
    """
    Gibt die richtige Bot-Config basierend auf group_id zurück
    
    Args:
        group_id: Signal Group ID
    
    Returns:
        Bot-Config dict oder None wenn Gruppe nicht erlaubt
    """
    if group_id == GROUP_IDS['dev']:
        return DEV_BOT_CONFIG
    elif group_id == GROUP_IDS['test']:
        return TEST_BOT_CONFIG
    elif group_id == GROUP_IDS['community_test']:
        return COMMUNITY_TEST_BOT_CONFIG
    else:
        return None

def get_bot_name_for_group(group_id: str) -> str:
    """Gibt Bot-Namen für Gruppe zurück"""
    if group_id == GROUP_IDS['dev']:
        return BOT_NAMES['dev']
    elif group_id == GROUP_IDS['test']:
        return BOT_NAMES['test']
    elif group_id == GROUP_IDS['community_test']:
        return BOT_NAMES['community_test']
    else:
        return "Unknown Bot"

def is_allowed_group(group_id: str) -> bool:
    """Prüft ob group_id erlaubt ist"""
    return group_id in ALLOWED_GROUP_IDS

def validate_config():
    """Validiert Multi-Bot Konfiguration"""
    errors = []
    
    # Prüfe Group IDs
    if len(GROUP_IDS) == 0:
        errors.append("GROUP_IDS darf nicht leer sein")
    
    # Prüfe dass alle Configs vorhanden sind
    for key in ['dev', 'test', 'community_test']:
        if key not in GROUP_IDS:
            errors.append(f"GROUP_IDS fehlt Eintrag für '{key}'")
    
    # Prüfe Signal Account
    if not SIGNAL_ACCOUNT:
        errors.append("SIGNAL_ACCOUNT muss gesetzt sein")
    
    return errors

if __name__ == "__main__":
    print(f"Borgo-Bot v{BOT_VERSION} Multi-Bot Configuration")
    print("=" * 50)
    
    print(f"\n📡 Configured Bots:")
    for key, group_id in GROUP_IDS.items():
        bot_name = BOT_NAMES[key]
        print(f"   {key.upper():15} → {bot_name:20} | {group_id[:20]}...")
    
    print(f"\n🔧 DEV Bot Features:")
    for feature, enabled in DEV_BOT_CONFIG['features'].items():
        status = "✓" if enabled else "✗"
        print(f"   {status} {feature}")
    
    print("\n🔍 Konfiguration validieren...")
    errors = validate_config()
    if errors:
        print("❌ Fehler gefunden:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("✅ Konfiguration OK!")
    
    print("\n" + "=" * 50)
