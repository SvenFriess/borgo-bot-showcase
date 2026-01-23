#!/bin/bash
# Borgo-Bot Community-Test - Start Script
# Für den Community-Test bis 7. Januar 2026, 23:59

cd /Users/svenfriess/Projekte/borgobatone-04

echo "🔴 Stoppe alte Bots..."
pkill -9 -f "borgo"
sleep 2

echo "🟢 Starte Community-Test Bot..."
mkdir -p logs
python3 borgo_bot_community_only.py > logs/community_only_$(date +%Y%m%d_%H%M%S).log 2>&1 &

sleep 3

echo ""
echo "📊 Status:"
RUNNING=$(ps aux | grep "python.*borgo_bot_community" | grep -v grep | wc -l | tr -d ' ')
if [ "$RUNNING" -eq 1 ]; then
    ps aux | grep "python.*borgo" | grep -v grep | awk '{printf "  ✅ PID: %s | Gestartet: %s\n", $2, $9}'
    echo ""
    echo "🎉 Community-Test Bot läuft!"
    echo "📄 Logs: tail -f logs/community_only_*.log"
else
    echo "  ⚠️  Problem beim Start - prüfe Logs!"
fi
