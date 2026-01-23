#!/bin/bash
# Signal-CLI Watchdog für Borgo-Bot v0.99
# Überwacht signal-cli und startet es bei Bedarf neu
# 
# Verwendung:
#   Als Cronjob alle 5 Minuten: */5 * * * * /path/to/signal_cli_watchdog.sh
#   Oder als Daemon im Hintergrund: ./signal_cli_watchdog.sh daemon

set -e

# ============================================
# KONFIGURATION
# ============================================

SIGNAL_CLI_PATH="/opt/homebrew/bin/signal-cli"  # Typischer Homebrew-Pfad auf Mac
SIGNAL_ACCOUNT="+49XXXXXXXXXX"                   # TODO: Aus .env auslesen!

# Alternative: Aus .env laden (wenn vorhanden)
if [ -f "/Users/svenfriess/borgobatone-04/.env" ]; then
    source "/Users/svenfriess/borgobatone-04/.env"
    # SIGNAL_ACCOUNT sollte dann in .env als SIGNAL_NUMBER oder ähnlich definiert sein
fi

# Log-Konfiguration
LOG_DIR="/Users/svenfriess/borgobatone-04/logs/signal-watchdog"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/watchdog_$(date +%Y%m%d).log"

# Watchdog-Einstellungen
CHECK_INTERVAL_SECONDS=300  # 5 Minuten
MAX_RESTART_ATTEMPTS=3
RESTART_COOLDOWN_SECONDS=60

# State-Datei für Restart-Tracking
STATE_FILE="/tmp/signal_watchdog_state"

# ============================================
# FUNKTIONEN
# ============================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

is_signal_cli_running() {
    pgrep -f "signal-cli.*daemon" > /dev/null 2>&1
    return $?
}

get_restart_count() {
    if [ -f "$STATE_FILE" ]; then
        local count=$(cat "$STATE_FILE" | grep "restart_count=" | cut -d'=' -f2)
        local timestamp=$(cat "$STATE_FILE" | grep "last_restart=" | cut -d'=' -f2)
        
        # Reset count nach 1 Stunde
        if [ ! -z "$timestamp" ]; then
            local now=$(date +%s)
            local diff=$((now - timestamp))
            if [ $diff -gt 3600 ]; then
                echo "0"
                return
            fi
        fi
        echo "${count:-0}"
    else
        echo "0"
    fi
}

increment_restart_count() {
    local current=$(get_restart_count)
    local new_count=$((current + 1))
    local timestamp=$(date +%s)
    
    echo "restart_count=$new_count" > "$STATE_FILE"
    echo "last_restart=$timestamp" >> "$STATE_FILE"
}

reset_restart_count() {
    rm -f "$STATE_FILE"
}

start_signal_cli() {
    log "🚀 Starte signal-cli daemon..."
    
    # Prüfe ob signal-cli verfügbar ist
    if [ ! -x "$SIGNAL_CLI_PATH" ]; then
        log "❌ signal-cli nicht gefunden: $SIGNAL_CLI_PATH"
        return 1
    fi
    
    # Starte signal-cli im Daemon-Modus
    "$SIGNAL_CLI_PATH" -a "$SIGNAL_ACCOUNT" daemon --ignore-attachments &
    local pid=$!
    
    # Warte und prüfe ob es läuft
    sleep 5
    
    if is_signal_cli_running; then
        log "✅ signal-cli erfolgreich gestartet (PID: $pid)"
        increment_restart_count
        return 0
    else
        log "❌ signal-cli konnte nicht gestartet werden"
        return 1
    fi
}

check_and_restart() {
    if is_signal_cli_running; then
        log "✅ signal-cli läuft"
        reset_restart_count
        return 0
    fi
    
    log "⚠️  signal-cli läuft NICHT"
    
    # Prüfe Restart-Limit
    local restart_count=$(get_restart_count)
    if [ $restart_count -ge $MAX_RESTART_ATTEMPTS ]; then
        log "❌ Maximale Restart-Versuche erreicht ($MAX_RESTART_ATTEMPTS)"
        log "   Bitte manuell prüfen und neu starten"
        return 1
    fi
    
    log "🔄 Restart-Versuch $(($restart_count + 1))/$MAX_RESTART_ATTEMPTS"
    
    # Versuche zu starten
    if start_signal_cli; then
        log "✅ Neustart erfolgreich"
        
        # Cooldown nach Restart
        log "⏳ Cooldown für $RESTART_COOLDOWN_SECONDS Sekunden..."
        sleep $RESTART_COOLDOWN_SECONDS
        
        return 0
    else
        log "❌ Neustart fehlgeschlagen"
        return 1
    fi
}

run_daemon() {
    log "🐕 Signal-CLI Watchdog startet (Daemon-Modus)"
    log "   Check-Interval: $CHECK_INTERVAL_SECONDS Sekunden"
    log "   Max Restarts: $MAX_RESTART_ATTEMPTS pro Stunde"
    
    while true; do
        check_and_restart
        sleep $CHECK_INTERVAL_SECONDS
    done
}

run_once() {
    log "🐕 Signal-CLI Watchdog: Einmaliger Check"
    check_and_restart
}

show_status() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Signal-CLI Watchdog Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if is_signal_cli_running; then
        echo "✅ signal-cli läuft"
        local pid=$(pgrep -f "signal-cli.*daemon" | head -1)
        echo "   PID: $pid"
    else
        echo "❌ signal-cli läuft NICHT"
    fi
    
    echo ""
    
    local restart_count=$(get_restart_count)
    echo "Restart-Zähler: $restart_count/$MAX_RESTART_ATTEMPTS"
    
    if [ -f "$STATE_FILE" ]; then
        local timestamp=$(cat "$STATE_FILE" | grep "last_restart=" | cut -d'=' -f2)
        if [ ! -z "$timestamp" ]; then
            local restart_time=$(date -r $timestamp '+%Y-%m-%d %H:%M:%S')
            echo "Letzter Restart: $restart_time"
        fi
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "Letzte Log-Einträge:"
        tail -5 "$LOG_FILE"
    fi
}

# ============================================
# HAUPTPROGRAMM
# ============================================

case "${1:-once}" in
    daemon)
        run_daemon
        ;;
    once)
        run_once
        ;;
    status)
        show_status
        ;;
    reset)
        reset_restart_count
        log "🔄 Restart-Zähler zurückgesetzt"
        ;;
    *)
        echo "Verwendung: $0 {daemon|once|status|reset}"
        echo ""
        echo "  daemon  - Läuft als Daemon und prüft kontinuierlich"
        echo "  once    - Einmaliger Check (Standard, für Cronjob)"
        echo "  status  - Zeigt aktuellen Status"
        echo "  reset   - Setzt Restart-Zähler zurück"
        exit 1
        ;;
esac