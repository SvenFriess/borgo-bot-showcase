#!/bin/bash
# Borgo-Bot Super-Simple Restart (KEINE Log-Dependencies!)

echo "╔════════════════════════════════════════════════╗"
echo "║   Borgo-Bot Quick Kill & Restart              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 1. Zeige aktuelle Prozesse
echo "📊 Aktuelle Borgo-Bot Prozesse:"
ps aux | grep "python.*borgo" | grep -v grep || echo "   Keine gefunden"
echo ""

# 2. Kill alle Python Borgo-Bot Prozesse
echo "🔴 Stoppe alle Borgo-Bot Prozesse..."
pkill -9 -f "python.*borgo" && echo "   ✅ Gestoppt" || echo "   ℹ️  Nichts zu stoppen"

sleep 2
echo ""

# 3. Prüfe ob noch was läuft
REMAINING=$(ps aux | grep "python.*borgo" | grep -v grep | wc -l | tr -d ' ')
if [ "$REMAINING" -gt 0 ]; then
    echo "⚠️  Noch $REMAINING Prozesse aktiv - versuche erneut..."
    pkill -9 -f "python"
    sleep 2
fi

# 4. Erstelle logs-Ordner wenn nicht vorhanden
mkdir -p /Users/svenfriess/borgobatone-04/logs

# 5. Starte Bots NEU (im Hintergrund, Logs ins Verzeichnis)
cd /Users/svenfriess/borgobatone-04

echo "🟢 Starte Bots neu..."
echo ""

# DEV-Bot
echo "  🚀 Starte DEV-Bot..."
BOT_ENV=dev python3 borgo_bot_multi.py > logs/dev_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo "     PID: $!"
sleep 1

# TEST-Bot
echo "  🚀 Starte TEST-Bot..."
BOT_ENV=test python3 borgo_bot_multi.py > logs/test_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo "     PID: $!"
sleep 1

# Community-Test-Bot
echo "  🚀 Starte Community-Test-Bot..."
BOT_ENV=community python3 borgo_bot_multi.py > logs/community_$(date +%Y%m%d_%H%M%S).log 2>&1 &
echo "     PID: $!"
sleep 2

# 6. Zeige Status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Finale Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

RUNNING=$(ps aux | grep "python.*borgo_bot_multi" | grep -v grep | wc -l | tr -d ' ')
echo "Laufende Bots: $RUNNING"
echo ""

if [ "$RUNNING" -gt 0 ]; then
    ps aux | grep "python.*borgo_bot_multi" | grep -v grep | awk '{printf "  PID: %-7s | CPU: %3s%% | MEM: %3s%% | Zeit: %s\n", $2, $3, $4, $9}'
    echo ""
    echo "🎉 $RUNNING Bot(s) erfolgreich gestartet!"
else
    echo "❌ Keine Bots laufen - prüfe Logs:"
    echo "   tail -f logs/*.log"
fi

echo ""
echo "Logs: /Users/svenfriess/borgobatone-04/logs/"
