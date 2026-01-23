#!/bin/bash
# Borgo-Bot v0.99 - Startup Script für alle Services
# Multi-Bot Architektur: DEV, TEST, Community-Test

set -e  # Beende bei Fehler

# ============================================
# KONFIGURATION
# ============================================

# Basis-Verzeichnis für Borgo-Bot (alle Bots laufen hier)
BORGO_DIR="/Users/svenfriess/borgobatone-04"

# Haupt-Script
BOT_SCRIPT="borgo_bot_multi.py"

# Log-Verzeichnis
LOG_DIR="$BORGO_DIR/logs"
mkdir -p "$LOG_DIR"

# Welche Bots starten?
START_DEV=true
START_TEST=true
START_COMMUNITY=true

# Bot-Umgebungen (Environment Variables für Multi-Bot Setup)
# Diese werden an das Script übergeben
declare -A BOT_ENVS=(
    ["DEV"]="BOT_ENV=dev"
    ["TEST"]="BOT_ENV=test"
    ["COMMUNITY"]="BOT_ENV=community"
)

# ============================================
# FUNKTIONEN
# ============================================

start_bot() {
    local bot_name=$1
    local bot_env=$2
    local log_file="$LOG_DIR/${bot_name}_$(date +%Y%m%d_%H%M%S).log"
    
    echo "🚀 Starte $bot_name..."
    
    # Prüfe ob Script existiert
    if [ ! -f "$BORGO_DIR/$BOT_SCRIPT" ]; then
        echo "   ❌ Script nicht gefunden: $BORGO_DIR/$BOT_SCRIPT"
        return 1
    fi
    
    # Wechsle ins Borgo-Verzeichnis und starte mit Environment
    cd "$BORGO_DIR"
    nohup env $bot_env python3 "$BOT_SCRIPT" > "$log_file" 2>&1 &
    local pid=$!
    
    # Warte kurz und prüfe ob Prozess noch läuft
    sleep 2
    if ps -p $pid > /dev/null; then
        echo "   ✅ $bot_name gestartet (PID: $pid)"
        echo "   📄 Log: $log_file"
        return 0
    else
        echo "   ❌ $bot_name konnte nicht gestartet werden"
        echo "   📄 Siehe Log: $log_file"
        return 1
    fi
}

check_ollama() {
    echo "🔍 Prüfe Ollama..."
    if ! command -v ollama &> /dev/null; then
        echo "   ⚠️  Ollama nicht gefunden im PATH"
        return 1
    fi
    
    if ! pgrep -x "ollama" > /dev/null; then
        echo "   ⚠️  Ollama läuft nicht - starte Ollama zuerst!"
        return 1
    fi
    
    echo "   ✅ Ollama läuft"
    return 0
}

check_signal_cli() {
    echo "🔍 Prüfe signal-cli..."
    if ! command -v signal-cli &> /dev/null; then
        echo "   ⚠️  signal-cli nicht gefunden im PATH"
        return 1
    fi
    echo "   ✅ signal-cli verfügbar"
    return 0
}

show_status() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Borgo-Bot Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Zeige alle Borgo-Bot Prozesse
    local borgo_processes=$(ps aux | grep -i "python.*borgo" | grep -v grep)
    if [ ! -z "$borgo_processes" ]; then
        echo ""
        echo "Laufende Borgo-Bot Prozesse:"
        echo "$borgo_processes" | awk '{printf "  PID: %-7s | %s\n", $2, $11" "$12" "$13}'
    else
        echo ""
        echo "⚠️  Keine Borgo-Bot Prozesse gefunden"
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ============================================
# HAUPTPROGRAMM
# ============================================

echo "╔════════════════════════════════════════════════╗"
echo "║   Borgo-Bot v0.99 - Service Startup             ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Voraussetzungen prüfen
check_ollama || { echo "❌ Ollama muss laufen!"; exit 1; }
check_signal_cli || { echo "⚠️  signal-cli nicht gefunden - Bot könnte Probleme haben"; }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Starte Bots..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Zähler für Erfolg/Fehler
success_count=0
total_count=0

# Starte DEV-Bot
if [ "$START_DEV" = true ]; then
    ((total_count++))
    if start_bot "DEV-Bot" "${BOT_ENVS[DEV]}"; then
        ((success_count++))
    fi
    echo ""
fi

# Starte TEST-Bot
if [ "$START_TEST" = true ]; then
    ((total_count++))
    if start_bot "TEST-Bot" "${BOT_ENVS[TEST]}"; then
        ((success_count++))
    fi
    echo ""
fi

# Starte Community-Test-Bot
if [ "$START_COMMUNITY" = true ]; then
    ((total_count++))
    if start_bot "Community-Test-Bot" "${BOT_ENVS[COMMUNITY]}"; then
        ((success_count++))
    fi
    echo ""
fi

# Status anzeigen
show_status

# Zusammenfassung
echo ""
if [ $success_count -eq $total_count ]; then
    echo "🎉 Alle $success_count/$total_count Bots erfolgreich gestartet!"
    exit 0
else
    echo "⚠️  $success_count/$total_count Bots gestartet"
    exit 1
fi
