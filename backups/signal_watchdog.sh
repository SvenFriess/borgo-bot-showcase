#!/bin/bash

################################################################################
# Signal-CLI Watchdog Script
# Überwacht Signal-CLI Daemon und startet ihn bei Bedarf neu
################################################################################

# Konfiguration
SIGNAL_CLI="/opt/homebrew/bin/signal-cli"
SIGNAL_ACCOUNT="+4915755901211"
SIGNAL_SOCKET="/tmp/signal-cli-socket"
CHECK_INTERVAL=30  # Sekunden zwischen Checks
MAX_RESTART_ATTEMPTS=3  # Max. Neustarts innerhalb RESTART_WINDOW
RESTART_WINDOW=300  # 5 Minuten in Sekunden
LOG_FILE="signal_watchdog.log"

# Restart-Tracking
RESTART_TIMES=()

################################################################################
# Funktionen
################################################################################

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

is_daemon_running() {
    # Prüfe ob signal-cli daemon Prozess läuft
    if pgrep -f "signal-cli.*daemon.*${SIGNAL_SOCKET}" > /dev/null 2>&1; then
        return 0  # Läuft
    else
        return 1  # Läuft nicht
    fi
}

is_socket_available() {
    # Prüfe ob Socket existiert
    if [ -S "$SIGNAL_SOCKET" ]; then
        return 0  # Socket existiert
    else
        return 1  # Socket fehlt
    fi
}

check_restart_rate() {
    # Bereinige alte Restart-Zeiten (außerhalb des Fensters)
    current_time=$(date +%s)
    cutoff_time=$((current_time - RESTART_WINDOW))
    
    new_restart_times=()
    for restart_time in "${RESTART_TIMES[@]}"; do
        if [ "$restart_time" -gt "$cutoff_time" ]; then
            new_restart_times+=("$restart_time")
        fi
    done
    RESTART_TIMES=("${new_restart_times[@]}")
    
    # Prüfe ob zu viele Restarts
    if [ ${#RESTART_TIMES[@]} -ge $MAX_RESTART_ATTEMPTS ]; then
        return 1  # Zu viele Restarts
    else
        return 0  # OK
    fi
}

start_daemon() {
    log "🔄 Starte Signal-CLI Daemon..."
    
    # Prüfe Restart-Rate
    if ! check_restart_rate; then
        log "🚨 ALARM: Zu viele Restarts (${#RESTART_TIMES[@]} innerhalb ${RESTART_WINDOW}s)!"
        log "🚨 Watchdog gestoppt. Manuelle Intervention erforderlich!"
        exit 1
    fi
    
    # Lösche alten Socket falls vorhanden
    if [ -S "$SIGNAL_SOCKET" ]; then
        log "🧹 Lösche alten Socket..."
        rm -f "$SIGNAL_SOCKET"
    fi
    
    # Starte Daemon
    nohup "$SIGNAL_CLI" -a "$SIGNAL_ACCOUNT" daemon --socket "$SIGNAL_SOCKET" \
        >> signal_cli_daemon.log 2>&1 &
    
    local daemon_pid=$!
    
    # Warte kurz und prüfe ob Start erfolgreich
    sleep 3
    
    if is_daemon_running && is_socket_available; then
        log "✅ Signal-CLI Daemon erfolgreich gestartet (PID: $daemon_pid)"
        RESTART_TIMES+=("$(date +%s)")
        return 0
    else
        log "❌ Signal-CLI Daemon Start fehlgeschlagen!"
        return 1
    fi
}

stop_watchdog() {
    log "🛑 Watchdog wird beendet..."
    exit 0
}

# Signal-Handler für sauberes Beenden
trap stop_watchdog SIGTERM SIGINT

################################################################################
# Main Loop
################################################################################

log "🚀 Signal-CLI Watchdog gestartet"
log "   Account: $SIGNAL_ACCOUNT"
log "   Socket: $SIGNAL_SOCKET"
log "   Check-Interval: ${CHECK_INTERVAL}s"
log "   Max Restarts: $MAX_RESTART_ATTEMPTS innerhalb ${RESTART_WINDOW}s"

# Initiale Prüfung
if ! is_daemon_running || ! is_socket_available; then
    log "⚠️  Signal-CLI Daemon läuft nicht, starte initial..."
    start_daemon
fi

# Watchdog-Loop
while true; do
    sleep "$CHECK_INTERVAL"
    
    # Prüfe Daemon-Status
    if ! is_daemon_running; then
        log "❌ Signal-CLI Daemon-Prozess nicht gefunden!"
        start_daemon
        continue
    fi
    
    # Prüfe Socket
    if ! is_socket_available; then
        log "❌ Signal-CLI Socket nicht verfügbar!"
        # Stoppe alten Daemon (falls noch läuft)
        pkill -f "signal-cli.*daemon.*${SIGNAL_SOCKET}"
        sleep 1
        start_daemon
        continue
    fi
    
    # Optional: Socket-Health-Check (kann aktiviert werden)
    # if ! timeout 5 curl --unix-socket "$SIGNAL_SOCKET" http://localhost/ 2>/dev/null; then
    #     log "⚠️  Socket reagiert nicht, Neustart..."
    #     pkill -f "signal-cli.*daemon.*${SIGNAL_SOCKET}"
    #     sleep 1
    #     start_daemon
    # fi
    
    # Alles OK
    # log "✅ Signal-CLI Daemon läuft stabil"
done
