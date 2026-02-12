#!/bin/bash
################################################################################
# Tägliches Signal-CLI Backup
# Per Cronjob: 0 3 * * * /Users/svenfriess/Projekte/borgobatone-04/backup_signal.sh
################################################################################

BACKUP_DIR="/Users/svenfriess/backups/signal-cli"
SIGNAL_DATA="$HOME/.local/share/signal-cli"
KEEP_DAYS=14

mkdir -p "$BACKUP_DIR"

FILENAME="signal-cli-backup_$(date +%Y%m%d_%H%M%S).tar.gz"

tar -czf "$BACKUP_DIR/$FILENAME" -C "$HOME/.local/share" signal-cli 2>/dev/null

if [ $? -eq 0 ]; then
    SIZE=$(ls -lh "$BACKUP_DIR/$FILENAME" | awk '{print $5}')
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Backup erstellt: $FILENAME ($SIZE)"
    
    # Alte Backups löschen
    find "$BACKUP_DIR" -name "signal-cli-backup_*.tar.gz" -mtime +${KEEP_DAYS} -delete
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Backup fehlgeschlagen!"
fi
