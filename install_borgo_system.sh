#!/bin/bash
################################################################################
# Borgo-Bot System Installer
# Kopiert alle Scripts und richtet Autostart + Backup-Cronjob ein
################################################################################

BOT_DIR="/Users/svenfriess/Projekte/borgobatone-04"
LAUNCH_AGENTS="$HOME/Library/LaunchAgents"

echo "============================================"
echo "  🔧 Borgo-Bot System Installer"
echo "============================================"
echo ""

# 1. Scripts kopieren
echo "1️⃣  Kopiere Scripts..."
cp start_borgo_system.sh "$BOT_DIR/"
cp signal_watchdog.sh "$BOT_DIR/"
cp backup_signal.sh "$BOT_DIR/"
chmod +x "$BOT_DIR/start_borgo_system.sh"
chmod +x "$BOT_DIR/signal_watchdog.sh"
chmod +x "$BOT_DIR/backup_signal.sh"
echo "   ✅ Scripts installiert"

# 2. LLM_TIMEOUT fixen
echo "2️⃣  Fixe LLM_TIMEOUT..."
if grep -q "LLM_TIMEOUT_SECONDS = 30" "$BOT_DIR/config.py" 2>/dev/null; then
    sed -i '' 's/LLM_TIMEOUT_SECONDS = 30/LLM_TIMEOUT_SECONDS = 60/' "$BOT_DIR/config.py"
    echo "   ✅ LLM_TIMEOUT: 30s → 60s"
else
    echo "   ⚠️  config.py nicht gefunden oder TIMEOUT bereits geändert"
fi

# 3. Log-Verzeichnis
echo "3️⃣  Erstelle Log-Verzeichnis..."
mkdir -p "$BOT_DIR/logs"
mkdir -p "$HOME/backups/signal-cli"
echo "   ✅ Verzeichnisse erstellt"

# 4. Launchd Autostart
echo "4️⃣  Richte Autostart ein..."
mkdir -p "$LAUNCH_AGENTS"

# Alte Version entladen falls vorhanden
launchctl unload "$LAUNCH_AGENTS/com.borgo.system.plist" 2>/dev/null
launchctl unload "$LAUNCH_AGENTS/com.borgo.watchdog.plist" 2>/dev/null

cp com.borgo.system.plist "$LAUNCH_AGENTS/"
echo "   ✅ launchd plist installiert"
echo "   ⚠️  Autostart wird NICHT sofort aktiviert (erst nach Reboot-Test)"
echo "   → Zum Aktivieren: launchctl load ~/Library/LaunchAgents/com.borgo.system.plist"

# 5. Backup-Cronjob
echo "5️⃣  Richte Backup-Cronjob ein..."
CRON_LINE="0 3 * * * $BOT_DIR/backup_signal.sh >> $BOT_DIR/logs/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "backup_signal.sh"; echo "$CRON_LINE") | crontab -
echo "   ✅ Tägliches Backup um 03:00 Uhr"

echo ""
echo "============================================"
echo "  ✅ Installation abgeschlossen!"
echo "============================================"
echo ""
echo "📋 Was wurde installiert:"
echo "   • start_borgo_system.sh  — Kompletter Systemstart"
echo "   • signal_watchdog.sh     — Automatischer Daemon-Restart"
echo "   • backup_signal.sh       — Tägliches Signal-CLI Backup"
echo "   • com.borgo.system.plist — Autostart nach Reboot"
echo "   • Cronjob                — Backup täglich 03:00"
echo "   • LLM_TIMEOUT            — 30s → 60s"
echo ""
echo "🚀 Manueller Start:"
echo "   cd $BOT_DIR && ./start_borgo_system.sh"
echo ""
echo "🔄 Autostart aktivieren:"
echo "   launchctl load ~/Library/LaunchAgents/com.borgo.system.plist"
echo ""
echo "📊 Status prüfen:"
echo "   ps aux | grep -E 'signal-cli|borgo_bot|watchdog' | grep -v grep"
