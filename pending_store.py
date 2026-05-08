"""
Borgo-Bot - Pending Store
Verwaltet ausstehende KB-Änderungen vor Admin-Freigabe.
Datei: pending_store.py
"""

import yaml
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PENDING_FILE = Path("pending_changes.yaml")

# Status-Konstanten
STATUS_PENDING  = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"


def _load() -> dict:
    """Lädt pending_changes.yaml, erstellt sie wenn nötig."""
    if not PENDING_FILE.exists():
        return {"changes": []}
    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if "changes" not in data:
        data["changes"] = []
    return data


def _save(data: dict) -> None:
    """Schreibt pending_changes.yaml zurück."""
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _short_id(full_id: str) -> str:
    """Gibt die ersten 6 Zeichen der UUID zurück (lesbare Kurzform)."""
    return full_id[:6].upper()


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def add_change(action: str, entry_key: str, new_data: dict,
               old_data: Optional[dict] = None, editor: str = "kb-editor") -> str:
    """
    Fügt eine neue Änderung als PENDING ein.

    Args:
        action:    'create' | 'update' | 'delete'
        entry_key: Schlüssel des KB-Eintrags (z.B. 'pizzaofen')
        new_data:  Neuer Inhalt des Eintrags
        old_data:  Alter Inhalt (nur bei update/delete relevant)
        editor:    Quelle der Änderung (default: 'kb-editor')

    Returns:
        short_id: 6-stellige ID für Signal-Befehle
    """
    data = _load()
    full_id = str(uuid.uuid4())
    short = _short_id(full_id)

    change = {
        "id":         full_id,
        "short_id":   short,
        "action":     action,          # create | update | delete
        "entry_key":  entry_key,
        "new_data":   new_data,
        "old_data":   old_data,
        "editor":     editor,
        "status":     STATUS_PENDING,
        "created_at": datetime.now().isoformat(),
        "resolved_at": None,
    }

    data["changes"].append(change)
    _save(data)
    logger.info(f"[PendingStore] Neue Änderung #{short} ({action}: {entry_key})")
    return short


def get_pending() -> list:
    """Gibt alle Einträge mit status=pending zurück."""
    data = _load()
    return [c for c in data["changes"] if c["status"] == STATUS_PENDING]


def get_by_short_id(short_id: str) -> Optional[dict]:
    """Sucht einen Eintrag anhand der 6-stelligen ID (case-insensitive)."""
    data = _load()
    short_id = short_id.upper()
    for c in data["changes"]:
        if c.get("short_id", "").upper() == short_id:
            return c
    return None


def approve(short_id: str) -> Optional[dict]:
    """
    Setzt Status auf 'approved'.
    Gibt den Eintrag zurück, damit kb_api.py ihn in die YAML schreiben kann.
    """
    data = _load()
    short_id = short_id.upper()
    for c in data["changes"]:
        if c.get("short_id", "").upper() == short_id and c["status"] == STATUS_PENDING:
            c["status"] = STATUS_APPROVED
            c["resolved_at"] = datetime.now().isoformat()
            _save(data)
            logger.info(f"[PendingStore] #{short_id} APPROVED")
            return c
    logger.warning(f"[PendingStore] #{short_id} nicht gefunden oder nicht pending")
    return None


def reject(short_id: str) -> Optional[dict]:
    """Setzt Status auf 'rejected'. Keine KB-Änderung."""
    data = _load()
    short_id = short_id.upper()
    for c in data["changes"]:
        if c.get("short_id", "").upper() == short_id and c["status"] == STATUS_PENDING:
            c["status"] = STATUS_REJECTED
            c["resolved_at"] = datetime.now().isoformat()
            _save(data)
            logger.info(f"[PendingStore] #{short_id} REJECTED")
            return c
    logger.warning(f"[PendingStore] #{short_id} nicht gefunden oder nicht pending")
    return None


def pending_summary() -> str:
    """Gibt eine lesbare Zusammenfassung aller offenen Änderungen zurück."""
    items = get_pending()
    if not items:
        return "✅ Keine offenen Änderungen."
    lines = [f"📋 {len(items)} offene Änderung(en):\n"]
    for c in items:
        ts = c["created_at"][:16].replace("T", " ")
        lines.append(
            f"  #{c['short_id']} [{c['action'].upper()}] {c['entry_key']}  ({ts})"
        )
    lines.append("\n!approve <ID> | !reject <ID>")
    return "\n".join(lines)
