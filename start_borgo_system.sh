#!/bin/bash
################################################################################
# Borgo-Bot Complete System Startup
# Startet: Ollama → Signal-CLI Daemon → Watchdog → Bot
# Kompatibel mit macOS zsh + bash 3.x
################################################################################

PHONE="+4915755901211"
SOCKET="/tmp/signal-cli-socket"
BOT_DIR="/Users/svenfriess/Projekte/borgobatone-04"
LOG_DIR="${BOT_DIR}/logs"
SIGNAL_CLI="/opt/homebrew/bin/signal-cli"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

cleanup() {
    log "🛑 Stoppe alle Prozesse..."
    pkill -f "signal_watchdog.sh" 2>/dev/null
    pkill -f "signal-cli.*daemon" 2>/dev/null
    pkill -f "borgo_bot_multi.py" 2>/dev/null
    rm -f "$SOCKET"
    log "✅ Alles gestoppt."
    exit 0
}

trap cleanup SIGINT SIGTERM

log "============================================"
log "  🚀 Borgo-Bot System Startup"
log "============================================"

# 1. Ollama prüfen
log "1️⃣  Prüfe Ollama..."
if ! pgrep -f "ollama" > /dev/null 2>&1; then
    log "   Starte Ollama..."
    ollama serve > "$LOG_DIR/ollama.log" 2>&1 &
    sleep 3
fi
log "   ✅ Ollama läuft"

# 2. Alte Prozesse aufräumen
log "2️⃣  Räume alte Prozesse auf..."
pkill -f "signal-cli.*daemon" 2>/dev/null
pkill -f "borgo_bot_multi.py" 2>/dev/null
pkill -f "signal_watchdog.sh" 2>/dev/null
rm -f "$SOCKET"
sleep 2

# 3. Signal-CLI Daemon starten
log "3️⃣  Starte Signal-CLI Daemon..."
nohup "$SIGNAL_CLI" -a "$PHONE" --trust-new-identities always daemon --socket "$SOCKET" \
    >> "$LOG_DIR/signal_daemon.log" 2>&1 &
DAEMON_PID=$!
log "   PID: $DAEMON_PID"

# Warte auf Socket
WAIT=0
while [ ! -S "$SOCKET" ] && [ $WAIT -lt 30 ]; do
    sleep 1
    WAIT=$((WAIT + 1))
done

if [ -S "$SOCKET" ]; then
    log "   ✅ Daemon läuft, Socket bereit"
else
    log "   ❌ Daemon konnte nicht starten!"
    exit 1
fi

# 4. Watchdog starten
log "4️⃣  Starte Watchdog..."
nohup "${BOT_DIR}/signal_watchdog.sh" >> "$LOG_DIR/watchdog.log" 2>&1 &
WATCHDOG_PID=$!
log "   ✅ Watchdog PID: $WATCHDOG_PID"

# 5. Bot starten
log "5️⃣  Starte Borgo-Bot..."
cd "$BOT_DIR"
python3 borgo_bot_multi.py

# Wenn Bot beendet wird → cleanup
cleanup
