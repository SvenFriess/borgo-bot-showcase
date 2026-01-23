# 🚀 BORGO-BOT QUICK START - PROBLEMLÖSUNG

## Problem erkannt
- `/logs` Ordner existierte nicht
- Scripts konnten nicht schreiben
- Keine Reaktion beim Ausführen

## ✅ LÖSUNG - 2 Schritte

### 1️⃣ DIAGNOSE (einmalig ausführen)

```bash
cd /Users/svenfriess/borgobatone-04
chmod +x setup_and_diagnose.sh
./setup_and_diagnose.sh
```

**Das Script:**
✅ Prüft ob alle Dateien vorhanden sind  
✅ Erstellt `/logs` und `/backups` Ordner automatisch  
✅ Prüft Ollama  
✅ Prüft Signal-CLI  
✅ Prüft Python-Pakete  
✅ Zeigt laufende Prozesse  

### 2️⃣ RESTART (jetzt und immer wenn nötig)

```bash
cd /Users/svenfriess/borgobatone-04
chmod +x super_simple_restart.sh
./super_simple_restart.sh
```

**Das Script:**
🔴 Killt ALLE Borgo-Bot Prozesse (sauber)  
📁 Erstellt `/logs` falls nicht vorhanden  
🟢 Startet DEV, TEST, Community-Test Bots  
📊 Zeigt Status am Ende  

## 🔍 Wenn es immer noch nicht funktioniert

### Schritt A: Prüfe was fehlt

```bash
cd /Users/svenfriess/borgobatone-04

# Ist Ollama am Laufen?
pgrep ollama && echo "✅ Läuft" || echo "❌ Starte mit: ollama serve"

# Ist Python da?
python3 --version

# Ist das Haupt-Script da?
ls -la borgo_bot_multi.py

# Ist die .env da?
ls -la .env
```

### Schritt B: Teste Manual-Start

```bash
cd /Users/svenfriess/borgobatone-04

# Teste DEV-Bot direkt (sollte Output zeigen!)
BOT_ENV=dev python3 borgo_bot_multi.py
```

**Drücke Ctrl+C nach 5 Sekunden wenn du Output siehst**

### Schritt C: Prüfe Logs

```bash
# Zeige neueste Logs
ls -lt logs/*.log | head -5

# Schaue letzten Log
tail -50 logs/$(ls -t logs/*.log | head -1)

# ODER Live-View
tail -f logs/*.log
```

## 📝 Schnellreferenz

```bash
# Setup (einmalig)
./setup_and_diagnose.sh

# Restart (immer)
./super_simple_restart.sh

# Status
ps aux | grep "python.*borgo" | grep -v grep

# Logs live
tail -f logs/*.log

# Kill alles
pkill -9 -f "python.*borgo"
```

## 🆘 Notfall-Kommandos

```bash
# Wenn gar nichts geht - kompletter Reset:
cd /Users/svenfriess/borgobatone-04

# 1. Alle Python-Prozesse killen
pkill -9 python3

# 2. Logs löschen (Neuanfang)
rm -rf logs/*

# 3. Logs-Ordner neu erstellen
mkdir -p logs

# 4. Teste manuell
BOT_ENV=dev python3 borgo_bot_multi.py &
sleep 3
ps aux | grep borgo

# 5. Prüfe was los ist
tail -f logs/*.log
```

## 🎯 Häufige Probleme

### "No such file or directory: logs"
➜ **Lösung:** Erst `./setup_and_diagnose.sh` ausführen

### "Module not found"
➜ **Lösung:** `pip3 install pyyaml requests`

### "Ollama connection failed"
➜ **Lösung:** Terminal 2 öffnen: `ollama serve`

### "signal-cli not found"
➜ **Lösung:** `brew install signal-cli` oder Pfad in Scripts anpassen

### Bot startet aber antwortet nicht
➜ **Prüfe:** 
1. `tail -f logs/*.log` - Zeigt es Errors?
2. Signal-CLI daemon läuft? `pgrep -f "signal-cli.*daemon"`
3. Richtige Nummer in .env?

## ✅ Erfolg erkennen

Nach `./super_simple_restart.sh` solltest du sehen:

```
🎉 3 Bot(s) erfolgreich gestartet!

  PID: 12345   | CPU: 0.1% | MEM: 2.3% | Zeit: 09:47
  PID: 12346   | CPU: 0.1% | MEM: 2.3% | Zeit: 09:47
  PID: 12347   | CPU: 0.1% | MEM: 2.3% | Zeit: 09:47
```

Dann läuft alles! 🎊
