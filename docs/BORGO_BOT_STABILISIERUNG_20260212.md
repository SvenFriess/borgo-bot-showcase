# Borgo-Bot System — Stabilisierung & Recovery Summary

**Datum:** 12. Februar 2026
**System:** Borgo-Bot v0.99 MULTI-BOT
**Hardware:** Mac Mini M4 (16GB)
**Standort:** /Users/svenfriess/Projekte/borgobatone-04

---

## Ausgangslage

Das gesamte Borgo-Bot-System war nicht funktionsfähig. Alle drei Bot-Instanzen (DEV, TEST, Community) waren offline.

**Root Cause:** Die Signal-CLI Registrierung war verloren. Im Datenverzeichnis (`~/.local/share/signal-cli`) existierte kein valider Account mehr. Der Daemon konnte nicht starten (`User +4915755901211 is not registered`), wodurch alle Bots sofort nach dem Start beendet wurden.

**Betroffene Komponenten:**
- signal-cli daemon → exit 1
- accounts.json → leer / kein gültiger Account
- Alle drei Bot-Instanzen → konnten nicht mit Signal kommunizieren

---

## Durchgeführte Maßnahmen

### 1. Signal-CLI Neu-Registrierung

- Captcha-basierte Registrierung über `signalcaptchas.org`
- Automatisiertes Registrierungs-Script erstellt (`signal_register.sh`) wegen Token-Handling-Problemen im Terminal (Token zu lang, Captcha-Timeout, Zwischenablage-Probleme)
- SMS-Verifizierung erfolgreich mit Code 478507
- Account: +4915755901211, Single-Account-Mode

### 2. Daemon + Bot-Start

- signal-cli daemon gestartet auf `/tmp/signal-cli-socket`
- Alle drei Bot-Instanzen erfolgreich hochgefahren:
  - Borgo-Bot-DEV 🔧 → DEV Group
  - Borgo-Bot-TEST 🧪 → TEST Group
  - Borgo-Bot 🤖 → Community-Test Group
- YAML Knowledge Base: 56 Entries geladen

### 3. Backups erstellt

| Backup | Pfad | Größe |
|--------|------|-------|
| Signal-CLI Account | ~/signal-cli-backup_20260212_171759.tar.gz | 13 MB |
| Borgo-Bot Projekt | ~/borgobatone-04-backup_20260212_171819.tar.gz | 123 MB |

### 4. LLM_TIMEOUT Fix

- `config_multi_bot.py` angepasst
- Alle drei Bot-Instanzen von inkonsistenten Werten (45s/30s/30s) auf einheitlich **60s** gesetzt
- Globaler `LLM_TIMEOUT_SECONDS` war bereits auf 60s

### 5. Stabilisierungs-Scripts installiert

| Script | Funktion |
|--------|----------|
| `start_borgo_system.sh` | Kompletter Systemstart: Ollama → Daemon → Watchdog → Bot |
| `signal_watchdog.sh` | Überwacht Daemon + Socket, automatischer Neustart (max 3x in 5 Min) |
| `backup_signal.sh` | Tägliches Signal-CLI Backup, 14 Tage Retention |
| `com.borgo.system.plist` | macOS launchd Autostart nach Reboot |
| `signal_register.sh` | Captcha-automatisiertes Registrierungs-Tool (in ~/Downloads) |

### 6. Cronjob eingerichtet

- Tägliches Signal-CLI Backup um 03:00 Uhr
- Ziel: ~/backups/signal-cli/
- Automatische Löschung nach 14 Tagen

### 7. Autostart vorbereitet (noch nicht aktiviert)

- launchd plist installiert in ~/Library/LaunchAgents/
- Aktivierung: `launchctl load ~/Library/LaunchAgents/com.borgo.system.plist`
- Empfehlung: Erst nach 2-3 Tagen stabiler Laufzeit aktivieren

---

## Aktueller Systemstatus

| Komponente | Status |
|------------|--------|
| Signal-CLI Account | ✅ Registriert + Verifiziert |
| Signal-CLI Daemon | ✅ Läuft (PID 34186, Socket aktiv) |
| Borgo-Bot-DEV | ✅ Online |
| Borgo-Bot-TEST | ✅ Online |
| Borgo-Bot Community | ✅ Online |
| Ollama | ✅ Läuft |
| Watchdog | ✅ Installiert |
| Backup-Cronjob | ✅ Aktiv (täglich 03:00) |
| Autostart | ⏳ Vorbereitet, nicht aktiviert |

---

## Dateistruktur nach Stabilisierung

```
/Users/svenfriess/Projekte/borgobatone-04/
├── borgo_bot_multi.py          # Haupt-Bot (Multi-Bot System)
├── config_multi_bot.py         # Konfiguration (LLM_TIMEOUT: 60s)
├── signal_interface.py         # Signal JSON-RPC Daemon Interface
├── llm_handler.py              # LLM-Integration (Ollama)
├── context_manager.py          # YAML Knowledge Base Manager
├── keyword_extractor.py        # Keyword-Extraktion
├── monitoring.py               # Monitoring-System
├── fallback_system.py          # Fallback bei LLM-Fehlern
├── message_deduplication.py    # Deduplizierung
├── input_validator.py          # Input-Validierung
├── start_borgo_system.sh       # ✨ NEU: Kompletter Systemstart
├── signal_watchdog.sh          # ✨ NEU: Daemon-Watchdog
├── backup_signal.sh            # ✨ NEU: Tägliches Backup
├── com.borgo.system.plist      # ✨ NEU: Autostart-Config
├── install_borgo_system.sh     # ✨ NEU: Installer
└── logs/                       # Log-Verzeichnis
```

---

## Bekannte Einschränkungen / Offene Punkte

1. **Autostart** noch nicht aktiviert — manueller Start nach Reboot nötig via `./start_borgo_system.sh`
2. **Signal-CLI Registrierung** kann erneut verloren gehen bei Datenverlust — tägliches Backup ist eingerichtet als Schutz
3. **macOS bash 3.x** — alle Scripts nutzen POSIX-kompatible Syntax, keine `declare -A` (associative arrays)

---

## Recovery-Anleitung bei erneutem Ausfall

### Signal-CLI Account verloren:
```bash
cd /Users/svenfriess/Projekte/borgobatone-04
# Option A: Backup wiederherstellen
tar -xzf ~/backups/signal-cli/signal-cli-backup_NEUESTES.tar.gz -C ~/.local/share/

# Option B: Neu registrieren
~/Downloads/signal_register.sh
```

### Bot startet nicht:
```bash
cd /Users/svenfriess/Projekte/borgobatone-04
./start_borgo_system.sh
```

### Manueller Neustart einzelner Komponenten:
```bash
# Daemon
signal-cli -a +4915755901211 daemon --socket /tmp/signal-cli-socket &

# Bot
python3 borgo_bot_multi.py

# Watchdog
./signal_watchdog.sh &
```

### Status prüfen:
```bash
ps aux | grep -E 'signal-cli|borgo_bot|watchdog' | grep -v grep
ls -la /tmp/signal-cli-socket
```
