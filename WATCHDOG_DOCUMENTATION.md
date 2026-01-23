# 🔄 Signal-CLI Watchdog - Installation & Nutzung

## 📋 ÜBERSICHT

Der Signal-CLI Watchdog überwacht den Signal-CLI Daemon und startet ihn automatisch neu bei:
- Prozess-Crashes
- Socket-Problemen
- Unerwarteten Beendigungen

---

## 🚀 INSTALLATION (5 Minuten)

### Schritt 1: Dateien ins Projekt kopieren

```bash
cd /Users/svenfriess/Projekte/borgobatone-04/

# Downloade die Dateien aus dem Chat:
# - signal_watchdog.sh
# - start_borgo_bot.sh

# Setze Ausführungsrechte
chmod +x signal_watchdog.sh
chmod +x start_borgo_bot.sh
```

### Schritt 2: Test-Run

```bash
# Teste Watchdog einzeln (Ctrl+C zum Beenden)
./signal_watchdog.sh

# Erwartete Ausgabe:
# [2026-01-07 10:45:00] 🚀 Signal-CLI Watchdog gestartet
# [2026-01-07 10:45:00]    Account: +4915755901211
# [2026-01-07 10:45:00]    Socket: /tmp/signal-cli-socket
# [2026-01-07 10:45:00]    Check-Interval: 30s
# [2026-01-07 10:45:00] ✅ Signal-CLI Daemon läuft stabil
```

---

## 📖 NUTZUNG

### Option A: Bot + Watchdog zusammen starten (EMPFOHLEN)

```bash
./start_borgo_bot.sh
```

**Das macht das Script:**
1. ✅ Startet Watchdog (überwacht Signal-CLI)
2. ✅ Watchdog startet Signal-CLI Daemon (falls nötig)
3. ✅ Startet Borgo-Bot
4. ✅ Bei Ctrl+C: Sauberes Beenden aller Prozesse

### Option B: Nur Watchdog im Hintergrund

```bash
# Watchdog starten
nohup ./signal_watchdog.sh > watchdog.log 2>&1 &

# Bot separat starten
python3 borgo_bot_community_only.py

# Watchdog stoppen
pkill -f signal_watchdog.sh
```

### Option C: Wie bisher (ohne Watchdog)

```bash
# Signal-CLI manuell starten (falls nicht läuft)
signal-cli -a +4915755901211 daemon --socket /tmp/signal-cli-socket &

# Bot starten
python3 borgo_bot_community_only.py
```

---

## 🔧 KONFIGURATION

**signal_watchdog.sh - Anpassbare Parameter:**

```bash
CHECK_INTERVAL=30              # Sekunden zwischen Checks
MAX_RESTART_ATTEMPTS=3         # Max. Neustarts innerhalb Zeitfenster
RESTART_WINDOW=300             # Zeitfenster (5 Min)
LOG_FILE="signal_watchdog.log" # Log-Datei
```

**Was bedeutet das?**
- Watchdog prüft alle 30s ob Daemon läuft
- Max. 3 Restarts innerhalb 5 Minuten erlaubt
- Bei mehr Restarts: ALARM + Watchdog stoppt

---

## 📊 MONITORING

### Logs ansehen

```bash
# Watchdog-Log (live)
tail -f signal_watchdog.log

# Signal-CLI Daemon-Log (live)
tail -f signal_cli_daemon.log

# Bot-Log (falls vorhanden)
tail -f borgo_bot_community_only.log
```

### Status prüfen

```bash
# Läuft Signal-CLI Daemon?
pgrep -f "signal-cli.*daemon"

# Läuft Watchdog?
pgrep -f "signal_watchdog.sh"

# Läuft Bot?
pgrep -f "borgo_bot_community_only.py"
```

---

## 🚨 ALARM-HANDLING

**Watchdog stoppt bei zu vielen Restarts:**

```
[2026-01-07 10:45:00] 🚨 ALARM: Zu viele Restarts (3 innerhalb 300s)!
[2026-01-07 10:45:00] 🚨 Watchdog gestoppt. Manuelle Intervention erforderlich!
```

**Was tun?**

1. **Prüfe Signal-CLI Installation:**
   ```bash
   signal-cli --version
   ```

2. **Prüfe Socket-Pfad:**
   ```bash
   ls -la /tmp/signal-cli-socket
   ```

3. **Prüfe Logs:**
   ```bash
   tail -50 signal_cli_daemon.log
   ```

4. **Manueller Test:**
   ```bash
   signal-cli -a +4915755901211 daemon --socket /tmp/signal-cli-socket
   ```

5. **Watchdog neu starten:**
   ```bash
   ./signal_watchdog.sh
   ```

---

## 🔄 AUTO-START BEI SYSTEM-BOOT (Optional)

### macOS launchd Service

```bash
# Erstelle ~/Library/LaunchAgents/com.borgo.watchdog.plist
cat > ~/Library/LaunchAgents/com.borgo.watchdog.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.borgo.watchdog</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/svenfriess/Projekte/borgobatone-04/start_borgo_bot.sh</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/svenfriess/Projekte/borgobatone-04</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/svenfriess/Projekte/borgobatone-04/borgo_bot_startup.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/svenfriess/Projekte/borgobatone-04/borgo_bot_startup_error.log</string>
</dict>
</plist>
EOF

# Service laden
launchctl load ~/Library/LaunchAgents/com.borgo.watchdog.plist

# Service starten
launchctl start com.borgo.watchdog

# Service stoppen
launchctl stop com.borgo.watchdog

# Service deaktivieren
launchctl unload ~/Library/LaunchAgents/com.borgo.watchdog.plist
```

---

## ✅ TESTING-SZENARIEN

### Test 1: Daemon-Crash simulieren

```bash
# 1. Starte Watchdog
./signal_watchdog.sh &

# 2. Töte Signal-CLI Daemon
pkill -f "signal-cli.*daemon"

# 3. Beobachte Logs
tail -f signal_watchdog.log

# Erwartung:
# [timestamp] ❌ Signal-CLI Daemon-Prozess nicht gefunden!
# [timestamp] 🔄 Starte Signal-CLI Daemon...
# [timestamp] ✅ Signal-CLI Daemon erfolgreich gestartet (PID: ...)
```

### Test 2: Socket-Problem simulieren

```bash
# 1. Lösche Socket (während Daemon läuft)
rm /tmp/signal-cli-socket

# 2. Beobachte Logs
tail -f signal_watchdog.log

# Erwartung: Watchdog erkennt Problem und startet Daemon neu
```

### Test 3: Zu viele Restarts

```bash
# Mehrmals hintereinander Daemon töten
for i in {1..4}; do
    pkill -f "signal-cli.*daemon"
    sleep 2
done

# Erwartung: Nach 3 Restarts stoppt Watchdog mit ALARM
```

---

## 📈 PERFORMANCE

**Ressourcen-Verbrauch:**
- Watchdog-Script: ~1-2 MB RAM
- CPU: Minimal (nur alle 30s Check)
- Log-Rotation: Empfohlen ab 100 MB

**Log-Rotation einrichten:**

```bash
# Füge zu /etc/newsyslog.conf hinzu (oder erstelle eigene Rotation)
# /Users/svenfriess/Projekte/borgobatone-04/signal_watchdog.log 644 7 100 * J
```

---

## 🎯 SUCCESS METRICS

**Watchdog funktioniert wenn:**
- ✅ Signal-CLI Daemon läuft stabil 99.9%+ der Zeit
- ✅ Automatische Restarts < 1x pro Tag
- ✅ Keine manuellen Interventionen nötig
- ✅ Bot-Verfügbarkeit 24/7

---

## 📞 SUPPORT

**Bei Problemen:**
1. Prüfe Logs: `signal_watchdog.log`, `signal_cli_daemon.log`
2. Teste Signal-CLI manuell
3. Prüfe Dateiberechtigungen: `chmod +x signal_watchdog.sh`
4. Kontaktiere Community

**Häufige Probleme:**
- "Permission denied" → `chmod +x signal_watchdog.sh`
- "signal-cli not found" → Pfad in Script anpassen
- Zu viele Restarts → Signal-CLI Installation prüfen

---

**Erstellt:** 7. Januar 2026  
**Version:** 1.0  
**Status:** Production-Ready ✅
