#!/bin/bash
# Borgo-Bot Status Check

echo "╔════════════════════════════════════════════════╗"
echo "║   Borgo-Bot System Status                     ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Check Ollama
echo "🤖 Ollama:"
if pgrep -x "ollama" > /dev/null; then
    echo "   ✅ Ollama läuft"
    # Zeige geladene Modelle
    if command -v ollama &> /dev/null; then
        echo "   📦 Geladene Modelle:"
        ollama list 2>/dev/null | grep -E "mistral|granite|qwen" | awk '{printf "      • %s\n", $1}' || echo "      (keine Details verfügbar)"
    fi
else
    echo "   ❌ Ollama läuft NICHT"
fi

echo ""

# Check signal-cli
echo "📱 Signal-CLI:"
if pgrep -f "signal-cli.*daemon" > /dev/null; then
    echo "   ✅ signal-cli daemon läuft"
    local signal_pid=$(pgrep -f "signal-cli.*daemon" | head -1)
    echo "   PID: $signal_pid"
else
    echo "   ❌ signal-cli daemon läuft NICHT"
fi

echo ""

# Check Borgo-Bots
echo "🤖 Borgo-Bot Prozesse:"
BORGO_PROCS=$(ps aux | grep "python.*borgo_bot" | grep -v grep)

if [ -z "$BORGO_PROCS" ]; then
    echo "   ❌ Keine Borgo-Bot Prozesse laufen"
else
    echo ""
    echo "$BORGO_PROCS" | awk '{
        printf "   ✅ PID: %-7s | CPU: %5s%% | MEM: %5s%% | Gestartet: %s\n", 
        $2, $3, $4, $9
    }'
    
    # Zähle Prozesse
    local count=$(echo "$BORGO_PROCS" | wc -l | tr -d ' ')
    echo ""
    echo "   📊 Total: $count Bot-Prozess(e)"
fi

echo ""

# Check neueste Logs
echo "📄 Neueste Logs (letzte 5 Minuten):"
LOG_DIR="/Users/svenfriess/borgobatone-04/logs"
if [ -d "$LOG_DIR" ]; then
    RECENT_LOGS=$(find "$LOG_DIR" -name "*.log" -mmin -5 2>/dev/null)
    if [ -z "$RECENT_LOGS" ]; then
        echo "   ℹ️  Keine neuen Logs in den letzten 5 Minuten"
    else
        echo "$RECENT_LOGS" | while read log; do
            local size=$(ls -lh "$log" | awk '{print $5}')
            local time=$(ls -l "$log" | awk '{print $6, $7, $8}')
            echo "   • $(basename "$log") ($size, $time)"
        done
    fi
else
    echo "   ℹ️  Log-Verzeichnis nicht gefunden"
fi

echo ""

# System Resources
echo "💻 System-Ressourcen:"
echo "   CPU: $(top -l 1 | grep "CPU usage" | awk '{print $3, $4, $5}')"
echo "   RAM: $(top -l 1 | grep "PhysMem" | awk '{print $2, $4, $6}')"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Letzte Aktualisierung: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
