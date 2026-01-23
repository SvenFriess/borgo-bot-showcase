#!/bin/bash
# Borgo-Bot Quick Kill & Restart für borgobatone-04
# Einfach ausführen: ./quick_restart.sh

BORGO_DIR="/Users/svenfriess/borgobatone-04"

echo "╔════════════════════════════════════════════════╗"
echo "║   Borgo-Bot Quick Restart                     ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 1. Kill alle Borgo-Bot Prozesse
echo "🔴 Stoppe alle Borgo-Bot Prozesse..."
pkill -9 -f "python.*borgo_bot" || echo "   ℹ️  Keine Borgo-Bot Prozesse gefunden"

# 2. Kill signal-cli (optional - auskommentiert weil meist nicht nötig)
# echo "🔴 Stoppe signal-cli..."
# pkill -9 -f "signal-cli.*daemon" || echo "   ℹ️  signal-cli läuft nicht"

# Kurz warten
sleep 2

# 3. Status zeigen
echo ""
echo "📊 Status nach Kill:"
ps aux | grep -E "python.*borgo|signal-cli" | grep -v grep || echo "✅ Alle Prozesse gestoppt"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 4. Neustart
echo "🟢 Starte Bots neu..."
echo ""

cd "$BORGO_DIR"

# DEV-Bot
echo "  🚀 DEV-Bot..."
BOT_ENV=dev nohup python3 borgo_bot_multi.py > logs/dev_bot_$(date +%Y%m%d_%H%M%S).log 2>&1 &
sleep 1

# TEST-Bot
echo "  🚀 TEST-Bot..."
BOT_ENV=test nohup python3 borgo_bot_multi.py > logs/test_bot_$(date +%Y%m%d_%H%M%S).log 2>&1 &
sleep 1

# Community-Test-Bot
echo "  🚀 Community-Test-Bot..."
BOT_ENV=community nohup python3 borgo_bot_multi.py > logs/community_bot_$(date +%Y%m%d_%H%M%S).log 2>&1 &
sleep 2

# 5. Status prüfen
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Finale Status-Prüfung:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

RUNNING=$(ps aux | grep -c "python.*borgo_bot_multi" | grep -v grep)
echo "✅ $RUNNING Borgo-Bot Prozesse laufen"
ps aux | grep "python.*borgo_bot_multi" | grep -v grep | awk '{printf "   PID: %-7s | Gestartet: %s %s\n", $2, $9, $10}'

echo ""
echo "🎉 Neustart abgeschlossen!"
echo ""
echo "Logs findest du in: $BORGO_DIR/logs/"
