#!/bin/bash
################################################################################
# Signal-CLI Watchdog
# Überwacht Daemon + Socket, startet automatisch neu bei Problemen
################################################################################

PHONE="+4915755901211"
SOCKET="/tmp/signal-cli-socket"
SIGNAL_CLI="/opt/homebrew/bin/signal-cli"
LOG_DIR="/Users/svenfriess/Projekte/borgobatone-04/logs"
CHECK_INTERVAL=30
MAX_RESTARTS=3
RESTART_WINDOW=300
RESTART_COUNT=0
LAST_RESET=$(date +%s)

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WATCHDOG: $1" | tee -a "$LOG_DIR/watchdog.log"
}

start_daemon() {
    log "🔄 Starte Signal-CLI Daemon..."
    rm -f "$SOCKET"
    nohup "$SIGNAL_CLI" -a "$PHONE" --trust-new-identities always daemon --socket "$SOCKET" \
        >> "$LOG_DIR/signal_daemon.log" 2>&1 &
    
    # Warte auf Socket
    WAIT=0
    while [ ! -S "$SOCKET" ] && [ $WAIT -lt 30 ]; do
        sleep 1
        WAIT=$((WAIT + 1))
    done
    
    if [ -S "$SOCKET" ]; then
        log "✅ Daemon gestartet, Socket bereit"
        return 0
    else
        log "❌ Daemon konnte nicht starten"
        return 1
    fi
}

log "🚀 Watchdog gestartet"
log "   Account: $PHONE"
log "   Socket: $SOCKET"
log "   Check-Interval: ${CHECK_INTERVAL}s"
log "   Max Restarts: $MAX_RESTARTS / ${RESTART_WINDOW}s"

while true; do
    sleep "$CHECK_INTERVAL"
    
    # Reset Restart-Counter nach Zeitfenster
    NOW=$(date +%s)
    ELAPSED=$((NOW - LAST_RESET))
    if [ $ELAPSED -ge $RESTART_WINDOW ]; then
        RESTART_COUNT=0
        LAST_RESET=$NOW
    fi
    
    # Prüfe Daemon-Prozess
    if ! pgrep -f "signal-cli.*daemon" > /dev/null 2>&1; then
        log "❌ Daemon-Prozess nicht gefunden!"
        
        if [ $RESTART_COUNT -ge $MAX_RESTARTS ]; then
            log "🚨 ALARM: $MAX_RESTARTS Restarts in ${RESTART_WINDOW}s — stoppe Watchdog!"
            log "🚨 Manuelle Intervention nötig."
            exit 1
        fi
        
        RESTART_COUNT=$((RESTART_COUNT + 1))
        log "Restart $RESTART_COUNT/$MAX_RESTARTS"
        start_daemon
        continue
    fi
    
    # Prüfe Socket
    if [ ! -S "$SOCKET" ]; then
        log "⚠️  Socket fehlt, aber Daemon läuft — killen und neu starten"
        pkill -f "signal-cli.*daemon"
        sleep 2
        
        RESTART_COUNT=$((RESTART_COUNT + 1))
        start_daemon
        continue
    fi
done
