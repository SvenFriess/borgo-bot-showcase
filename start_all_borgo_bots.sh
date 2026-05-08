#!/bin/bash
BORGO_DIR="$HOME/Projekte/borgobatone-04"
LOG_DIR="$BORGO_DIR/logs"
mkdir -p "$LOG_DIR"

echo "🚀 Starte Borgo-Bot Multi (DEV+TEST+COMMUNITY)..."

cd "$BORGO_DIR"
nohup python3 borgo_bot_multi.py > "$LOG_DIR/borgo_multi_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
PID=$!

sleep 2
if ps -p $PID > /dev/null; then
    echo "✅ Borgo-Bot gestartet (PID: $PID)"
    echo "📄 Log: $LOG_DIR/borgo_multi_*.log"
else
    echo "❌ Start fehlgeschlagen - Log prüfen!"
fi
