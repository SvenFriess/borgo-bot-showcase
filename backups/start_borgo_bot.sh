#!/bin/bash

################################################################################
# Borgo-Bot Startup Script
# Startet Signal-CLI Daemon, Watchdog und Bot zusammen
################################################################################

BOT_DIR="/Users/svenfriess/Projekte/borgobatone-04"
BOT_SCRIPT="borgo_bot_community_only.py"
WATCHDOG_SCRIPT="signal_watchdog.sh"

cd "$BOT_DIR" || exit 1

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

################################################################################
# Cleanup-Funktion
################################################################################
cleanup() {
    log "🛑 Beende alle Prozesse..."
    
    # Stoppe Bot
    pkill -f "$BOT_SCRIPT"
    
    # Stoppe Watchdog
    pkill -f "$WATCHDOG_SCRIPT"
    
    # Optional: Stoppe Signal-CLI Daemon
    # pkill -f "signal-cli.*daemon"
    
    log "✅ Cleanup abgeschlossen"
    exit 0
}

trap cleanup SIGTERM SIGINT

################################################################################
# Start-Sequenz
################################################################################

log "🚀 Starte Borgo-Bot System..."

# 1. Prüfe ob Signal-CLI Daemon läuft
if ! pgrep -f "signal-cli.*daemon" > /dev/null; then
    log "⚠️  Signal-CLI Daemon läuft nicht, wird vom Watchdog gestartet..."
fi

# 2. Starte Watchdog (im Hintergrund)
log "🔄 Starte Signal-CLI Watchdog..."
chmod +x "$WATCHDOG_SCRIPT"
nohup ./"$WATCHDOG_SCRIPT" > watchdog.log 2>&1 &
WATCHDOG_PID=$!
log "✅ Watchdog gestartet (PID: $WATCHDOG_PID)"

# Warte kurz damit Watchdog Signal-CLI starten kann
sleep 5

# 3. Starte Bot
log "🤖 Starte Borgo-Bot..."
python3 "$BOT_SCRIPT"

# Wenn Bot beendet wird, cleanup
cleanup
