# Borgo-Bot System — Tagesbericht 12. Februar 2026

## Zusammenfassung

Signal-CLI Registrierung war komplett verloren. System wurde heute von Grund auf wiederhergestellt. DEV-Gruppe ist wieder voll funktionsfähig. Zwei Gruppen müssen noch eingebunden werden.

---

## Durchgeführte Arbeiten

### 1. Signal-CLI Neu-Registrierung
- Captcha-basierte Registrierung (mehrere Anläufe wegen Token-Handling)
- Automatisiertes Registrierungs-Script erstellt (`signal_register.sh`)
- SMS-Verifizierung erfolgreich
- Profil gesetzt: "Borgo-Bot 🤖"

### 2. Session-Recovery
- Nach Neuregistrierung: Alle Verschlüsselungs-Sessions ungültig (`InvalidMessageException`)
- Safety Number musste auf Sender-Seite akzeptiert werden
- Bot musste aus DEV-Gruppe entfernt und neu eingeladen werden
- `--trust-new-identities always` Flag als Pflicht-Parameter identifiziert
- `signal-cli receive` nötig um Gruppen-Einladung zu akzeptieren (Active: false → true)

### 3. Backups erstellt
- Signal-CLI Account: ~/signal-cli-backup_20260212_171759.tar.gz (13 MB)
- Borgo-Bot Projekt: ~/borgobatone-04-backup_20260212_171819.tar.gz (123 MB)

### 4. Stabilisierungs-Paket installiert
- `start_borgo_system.sh` — Kompletter Systemstart (mit --trust-new-identities)
- `signal_watchdog.sh` — Daemon-Überwachung + Auto-Restart (mit --trust-new-identities)
- `backup_signal.sh` — Tägliches Backup um 03:00
- `com.borgo.system.plist` — Autostart nach Reboot (vorbereitet, nicht aktiviert)
- Cronjob für tägliches Backup eingerichtet

### 5. Config-Fix
- LLM_TIMEOUT in `config_multi_bot.py`: alle drei Bots auf 60s vereinheitlicht (war 45/30/30)

### 6. Dokumentation
- `docs/BORGO_BOT_STABILISIERUNG_20260212.md` erstellt

---

## Aktueller Status

| Komponente | Status |
|------------|--------|
| Signal-CLI Account | ✅ Registriert + Verifiziert |
| Signal-CLI Daemon | ✅ Läuft (mit --trust-new-identities always) |
| Borgo-Bot-DEV 🔧 | ✅ Online + antwortet |
| Borgo-Bot-TEST 🧪 | ❌ Gruppe nicht verbunden |
| Borgo-Bot Community 🤖 | ❌ Gruppe nicht verbunden |
| Watchdog | ✅ Installiert + gepatcht |
| Backup-Cronjob | ✅ Aktiv (täglich 03:00) |
| Autostart (launchd) | ⏳ Vorbereitet, nicht aktiviert |

---

## Bekannte Issues

1. **Bot erscheint als "Unknown contact"** in Signal — kosmetisches Problem, Funktion nicht betroffen
2. **TEST- und Community-Gruppe** noch nicht verbunden — Bot muss eingeladen und Einladung akzeptiert werden
3. **Borgo-Bot Comm...** zeigt in der Chat-Liste "Unknown contact: Borgi test 🤖" — muss nach Gruppen-Setup gefixt werden

---

## Next Steps

### Priorität 1: Gruppen wiederherstellen (5 Min pro Gruppe)

Für jede Gruppe (TEST, Community) den gleichen Prozess:

**In Signal App:**
1. Gruppe öffnen → Gruppennamen tippen → Add members
2. `+4915755901211` hinzufügen

**Auf dem M4:**
```bash
pkill -f "borgo_bot_multi"
pkill -f "signal-cli.*daemon"
sleep 2
signal-cli -a +4915755901211 --trust-new-identities always receive --timeout 15
signal-cli -a +4915755901211 listGroups
# Prüfen: Alle Gruppen Active: true?
# Dann Daemon + Bot starten:
signal-cli -a +4915755901211 --trust-new-identities always daemon --socket /tmp/signal-cli-socket &
sleep 3
python3 borgo_bot_multi.py
```

### Priorität 2: Autostart aktivieren (nach 2-3 Tagen Stabilität)

```bash
launchctl load ~/Library/LaunchAgents/com.borgo.system.plist
```

### Priorität 3: Signal-CLI Backup nach Gruppen-Setup

```bash
tar -czf ~/signal-cli-backup_FINAL_$(date +%Y%m%d).tar.gz -C ~/.local/share signal-cli
```

Wichtig: Erst NACH dem Gruppen-Setup backuppen, damit alle Gruppen im Backup enthalten sind.

### Priorität 4: Monitoring

- 2-3 Tage beobachten ob Watchdog + Daemon stabil bleiben
- Logs prüfen: `tail -f /Users/svenfriess/Projekte/borgobatone-04/logs/*.log`
- Bei Problemen: `ps aux | grep -E 'signal-cli|borgo_bot|watchdog' | grep -v grep`

---

## Lessons Learned

1. **Signal-CLI Neuregistrierung zerstört alle Sessions** — alle Gruppenmitglieder und Kontakte müssen die neue Safety Number akzeptieren
2. **Bot muss aus Gruppen entfernt und neu eingeladen werden** nach Neuregistrierung
3. **`--trust-new-identities always`** ist Pflicht beim Daemon-Start, sonst werden neue Sessions nicht akzeptiert
4. **`signal-cli receive`** muss nach Gruppen-Einladung laufen um Active: true zu setzen
5. **Captcha-Token** verfallen schnell — automatisiertes Script (`signal_register.sh`) spart Zeit
6. **Tägliches Backup der Signal-CLI Daten** verhindert den kompletten Session-Verlust in Zukunft
