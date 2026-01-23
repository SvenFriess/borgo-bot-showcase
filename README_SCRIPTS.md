# Borgo-Bot Management Scripts

Komplettes Set von Management-Scripts für dein Borgo-Bot v3.8 Multi-Bot Setup.

## 📁 Dateien

- **quick_restart.sh** - Schneller Kill & Restart (EMPFOHLEN für normale Nutzung)
- **restart_borgo_bot.sh** - Detaillierter Kill aller Prozesse
- **start_all_borgo_bots.sh** - Vollständiges Startup mit Environment-Checks
- **status_check.sh** - System-Status und Health-Check
- **signal_cli_watchdog.sh** - Signal-CLI Überwachung (TODO aus deiner Liste!)

## 🚀 Schnellstart

### Sofortlösung: Quick Restart

```bash
cd /Users/svenfriess/borgobatone-04
./quick_restart.sh
```

Das macht:
1. Killt alle Borgo-Bot Prozesse
2. Wartet 2 Sekunden
3. Startet DEV, TEST, und Community-Test Bots neu
4. Zeigt Status

### Status prüfen

```bash
./status_check.sh
```

Zeigt:
- Ollama Status und Modelle
- Signal-CLI Status  
- Laufende Bot-Prozesse
- Neueste Logs
- System-Ressourcen

### Vollständiger Neustart mit Checks

```bash
./start_all_borgo_bots.sh
```

Prüft:
- Ollama läuft
- signal-cli verfügbar
- Startet alle Bots mit korrekten Environments
- Zeigt detaillierte Logs

### Nur Killen (ohne Restart)

```bash
./restart_borgo_bot.sh
```

## 🐕 Signal-CLI Watchdog (aus TODO-Liste)

### Einmalige Prüfung

```bash
./signal_cli_watchdog.sh once
```

### Als Cronjob (alle 5 Minuten)

```bash
crontab -e
```

Füge hinzu:
```
*/5 * * * * /Users/svenfriess/borgobatone-04/signal_cli_watchdog.sh once
```

### Als Daemon (permanent im Hintergrund)

```bash
nohup ./signal_cli_watchdog.sh daemon > /dev/null 2>&1 &
```

### Watchdog Status

```bash
./signal_cli_watchdog.sh status
```

### Restart-Zähler zurücksetzen

```bash
./signal_cli_watchdog.sh reset
```

## ⚙️ Konfiguration

### Signal-CLI Watchdog anpassen

Editiere `signal_cli_watchdog.sh`:

```bash
# Zeile 9-11: Signal-CLI Pfad
SIGNAL_CLI_PATH="/opt/homebrew/bin/signal-cli"  # Prüfe mit: which signal-cli

# Zeile 12: Deine Signal-Nummer
SIGNAL_ACCOUNT="+491234567890"  # Aus .env auslesen
```

Signal-Nummer findest du in `/Users/svenfriess/borgobatone-04/.env`

### Startup-Script anpassen

Wenn du andere Bot-Umgebungen brauchst, editiere `start_all_borgo_bots.sh`:

```bash
# Zeile 15-17: Welche Bots starten?
START_DEV=true
START_TEST=true
START_COMMUNITY=true
```

## 🔧 Troubleshooting

### Bots starten nicht

1. Prüfe Ollama:
   ```bash
   pgrep ollama || echo "Ollama läuft nicht!"
   ```

2. Prüfe signal-cli:
   ```bash
   pgrep -f "signal-cli.*daemon" || echo "signal-cli läuft nicht!"
   ```

3. Prüfe Logs:
   ```bash
   tail -f logs/*.log
   ```

### Signal-CLI startet nicht

1. Finde Signal-CLI:
   ```bash
   which signal-cli
   ```

2. Update Pfad in `signal_cli_watchdog.sh`

3. Teste manuell:
   ```bash
   signal-cli -a +49XXX daemon
   ```

### Zu viele Prozesse laufen

Manuell aufräumen:
```bash
pkill -9 -f "python.*borgo_bot"
./status_check.sh
```

## 📊 Logs

Alle Logs sind in: `/Users/svenfriess/borgobatone-04/logs/`

- `dev_bot_*.log` - DEV-Bot
- `test_bot_*.log` - TEST-Bot
- `community_bot_*.log` - Community-Test-Bot
- `signal-watchdog/` - Signal-CLI Watchdog Logs

Neueste Logs anzeigen:
```bash
ls -lt logs/*.log | head -5
tail -f logs/community_bot_*.log  # Live-View
```

## ✅ TODO-Liste Status

- ✅ **Signal-CLI Watchdog Script** - Fertig!
- ✅ **Startup Script für alle Services** - Fertig!
- ⏳ **LLM_TIMEOUT auf 60s** - In config_multi_bot.py anpassen

## 📝 Community-Test Ende

**7. Januar 2026, 23:59 Uhr**

Danach: Rollout auf alle 100+ Community-Member

## 🆘 Support

Bei Problemen:
1. `./status_check.sh` ausführen
2. Logs prüfen: `tail -f logs/*.log`
3. Manual restart: `./quick_restart.sh`
4. Im Zweifel: Mac Mini neu starten
