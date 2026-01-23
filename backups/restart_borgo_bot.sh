#!/bin/bash
# Borgo-Bot Complete Kill & Restart Script
# Verwendung auf Mac Mini: bash restart_borgo_bot.sh

echo "🔴 Borgo-Bot System wird gestoppt..."
echo ""

# 1. Finde und beende alle Python Borgo-Bot Prozesse
echo "📍 Suche Python Borgo-Bot Prozesse..."
BORGO_PIDS=$(ps aux | grep -i "python.*borgo" | grep -v grep | awk '{print $2}')

if [ ! -z "$BORGO_PIDS" ]; then
    echo "Gefundene Borgo-Bot PIDs: $BORGO_PIDS"
    for pid in $BORGO_PIDS; do
        echo "  Beende PID $pid..."
        kill -9 $pid 2>/dev/null
    done
    echo "✅ Borgo-Bot Prozesse beendet"
else
    echo "ℹ️  Keine Borgo-Bot Python-Prozesse gefunden"
fi

echo ""

# 2. Finde und beende alle signal-cli Prozesse
echo "📍 Suche signal-cli Prozesse..."
SIGNAL_PIDS=$(ps aux | grep -i "signal-cli" | grep -v grep | awk '{print $2}')

if [ ! -z "$SIGNAL_PIDS" ]; then
    echo "Gefundene signal-cli PIDs: $SIGNAL_PIDS"
    for pid in $SIGNAL_PIDS; do
        echo "  Beende PID $pid..."
        kill -9 $pid 2>/dev/null
    done
    echo "✅ signal-cli Prozesse beendet"
else
    echo "ℹ️  Keine signal-cli Prozesse gefunden"
fi

echo ""

# 3. Warte kurz damit alles sauber beendet ist
echo "⏳ Warte 3 Sekunden..."
sleep 3

# 4. Zeige verbleibende Prozesse (zur Kontrolle)
echo ""
echo "📊 Kontrolle - Verbleibende relevante Prozesse:"
ps aux | grep -E "borgo|signal-cli" | grep -v grep | grep -v "restart_borgo_bot"
if [ $? -ne 0 ]; then
    echo "✅ Keine relevanten Prozesse mehr aktiv"
fi

echo ""
echo "🟢 Bereit für Neustart!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Nächste Schritte:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Für DEV-Bot:"
echo "  cd ~/path/to/borgo-bot-dev"
echo "  python3 borgo_bot_v3_8_dev.py &"
echo ""
echo "Für TEST-Bot:"
echo "  cd ~/path/to/borgo-bot-test"  
echo "  python3 borgo_bot_v3_8_test.py &"
echo ""
echo "Für Community-Test-Bot:"
echo "  cd ~/path/to/borgo-bot-community"
echo "  python3 borgo_bot_v3_8_community.py &"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Alternative - falls du einen Startup-Script hast:"
echo "  ./start_all_bots.sh"
echo ""
