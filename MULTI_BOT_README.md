# Borgo-Bot v3.6 - Multi-Bot Architektur

## Konzept

**EINE Bot-Instanz** simuliert **DREI logisch getrennte Bots**:

```
┌─────────────────────────────────────┐
│  EINE Python-Instanz läuft          │
│  (borgo_bot_multi.py)               │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │  Signal Messages │
    │  mit group_id    │
    └────────┬─────────┘
             │
   ┌─────────┼─────────┐
   │         │         │
 DEV-Bot  TEST-Bot  Community-Test-Bot
   │         │         │
Antwortet Antwortet Antwortet
nur DEV   nur TEST  nur Community-Test
```

## Strikte Isolation

- **Keine Cross-Posts**: Jeder Bot antwortet NUR in seiner Gruppe
- **Eigene Config**: Jeder Bot kann eigene Modelle, Features, Settings haben
- **Eigene Logs**: Separate Monitoring pro Bot
- **Deduplizierung**: Verhindert doppelte Antworten bei Multi-Worker

## Gruppen-Mapping

| Bot | Signal-Gruppe | Group-ID | Zweck |
|-----|---------------|----------|--------|
| **Borgi-DEV 🔧** | Borgo-Bot DEV | `i4UA7h...` | Entwicklung, Tests, Experimente |
| **Borgi-TEST 🧪** | Borgo-Bot TEST | `21oiqc...` | Standard-Tests |
| **Borgi 🤖** | Borgo-Bot Community-Test | `GIRAgo...` | Community-Testing |

## Installation

```bash
cd /Users/svenfriess/Projekte/borgobatone-04

# Backup alte Files
cp config.py config_old.py.backup
cp borgo_bot_v3_5.py borgo_bot_old.py.backup

# Neue Files installieren
# (lade config_multi_bot.py und borgo_bot_multi.py herunter)

# Umbenennen für Kompatibilität (optional)
# ln -s config_multi_bot.py config.py
```

## Starten

```bash
# Alte Instanzen stoppen
pkill -f borgo_bot

# Multi-Bot System starten
python borgo_bot_multi.py
```

Du siehst dann:

```
🚀 Starting Borgo-Bot v3.6 MULTI-BOT System
================================================================================

🤖 Initializing Bot Instances...
🤖 Initializing Borgi-DEV 🔧...
✅ Borgi-DEV 🔧 initialized
🤖 Initializing Borgi-TEST 🧪...
✅ Borgi-TEST 🧪 initialized
🤖 Initializing Borgi 🤖...
✅ Borgi 🤖 initialized

📋 Bot → Group Mapping:
   Borgi-DEV 🔧         → DEV Group
   Borgi-TEST 🧪        → TEST Group
   Borgi 🤖             → Community-Test Group

✅ All bots initialized. Listening for messages...
```

## DEV-Bot anpassen

In `config_multi_bot.py` → `DEV_BOT_CONFIG`:

```python
DEV_BOT_CONFIG = {
    # Experimentelles Modell testen
    'llm_models': [
        'llama3.2:latest',      # ← Ändere hier!
        'mistral:instruct',
        'granite3.3:2b',
    ],
    
    # Mehr Context für Tests
    'max_context_words': 1500,  # ← Erhöhe hier!
    
    # Features an/aus
    'features': {
        'hallucination_detection': False,  # ← Deaktiviere für Test!
        # ...
    },
    
    # Debug Mode
    'debug_mode': True,  # ← Mehr Logging!
}
```

Nach Änderungen Bot neu starten!

## Testen

**In DEV-Gruppe:**
```
!bot Wie funktioniert der Pizzaofen?
```
→ Antwort kommt von **Borgi-DEV 🔧** (mit experimentellem Modell)

**In Community-Test-Gruppe:**
```
!bot Wie funktioniert der Pizzaofen?
```
→ Antwort kommt von **Borgi 🤖** (mit Standard-Config)

**Beide Antworten können unterschiedlich sein!**

## Logs

```bash
# Live-Logs verfolgen
tail -f borgo_bot_multi.log

# Nach Bot-Namen filtern
tail -f borgo_bot_multi.log | grep "Borgi-DEV"

# Nur Errors
tail -f borgo_bot_multi.log | grep ERROR
```

## Monitoring

Jeder Bot hat eigene Metriken:

```bash
# Im Log erscheinen Tags wie:
# [Borgi-DEV 🔧] Processing message...
# [Borgi-TEST 🧪] Generated response...
# [Borgi 🤖] Using fallback...
```

## Wichtige Sicherheitsregeln

1. **Nur erlaubte Gruppen**: Unbekannte group_ids werden blockiert
2. **Keine Cross-Posts**: Response geht NUR an Ursprungsgruppe
3. **Deduplizierung**: Multi-Worker erzeugen keine Duplikate
4. **Strikte Isolation**: Bots teilen keinen State

## Troubleshooting

**Problem: Keine Antworten**
```bash
# Check ob Bot läuft
ps aux | grep borgo_bot_multi

# Check Logs
tail -n 50 borgo_bot_multi.log
```

**Problem: Bot antwortet in falscher Gruppe**
```bash
# Check group_id in Logs
grep "group_id" borgo_bot_multi.log | tail -20

# Verifiziere GROUP_IDS in config_multi_bot.py
python config_multi_bot.py
```

**Problem: Doppelte Antworten**
```bash
# Check ob mehrere Instanzen laufen
ps aux | grep borgo_bot

# Alle killen und neu starten
pkill -f borgo_bot
python borgo_bot_multi.py
```

## Nächste Schritte

1. ✅ System testen in allen drei Gruppen
2. ✅ DEV-Bot Config anpassen für Experimente
3. ✅ Logs monitoren für Performance
4. ⏳ Separate Knowledge Bases pro Bot (optional)
5. ⏳ Systemd/Supervisor Setup für Auto-Restart

## Migration von altem System

Das alte Environment-System (`BORGO_ENV=development`) ist jetzt ersetzt durch das Multi-Bot System.

**Alt:**
```bash
BORGO_ENV=development python borgo_bot_v3_5.py  # Nur eine Gruppe
```

**Neu:**
```bash
python borgo_bot_multi.py  # Alle drei Gruppen gleichzeitig!
```

## Vorteile

✅ Ein Deployment für alle Bots
✅ Jeder Bot kann eigene Config haben
✅ Strikte Isolation verhindert Fehler
✅ Einfaches Testing von Features in DEV
✅ Keine versehentlichen Cross-Posts
