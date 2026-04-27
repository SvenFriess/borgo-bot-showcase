"""
Borgo-Bot - Approval Handler
Verarbeitet !approve / !reject / !pending Befehle aus Signal.
Datei: approval_handler.py

Integration in borgo_bot_multi.py:
    from approval_handler import handle_approval_command, is_approval_command
    ...
    if is_approval_command(text, sender):
        response = handle_approval_command(text, sender)
        send_signal_message(ADMIN_NUMBER, response)
        return
"""

import logging
import yaml
from pathlib import Path

import pending_store as ps

logger = logging.getLogger(__name__)

# ── Konfiguration ──────────────────────────────────────────
# Deine Signal-Nummer – nur diese darf approven
ADMIN_NUMBER = "+4915755901211"
ADMIN_UUID = "e3a595c4-3d76-4715-9eb6-5a40489e4092"

# Pfad zur produktiven KB
YAML_DB_PATH = Path("borgo_knowledge_base.yaml")

# Bekannte Befehle
APPROVAL_COMMANDS = ("!approve", "!reject", "!pending")


# ──────────────────────────────────────────────────────────
# Hilfsfunktionen
# ──────────────────────────────────────────────────────────

def is_approval_command(text: str, sender: str) -> bool:
    """
    True wenn:
    - Sender ist Admin
    - Text beginnt mit einem Approval-Befehl
    """
    if sender.strip() not in (ADMIN_NUMBER, ADMIN_UUID):
        return False
    return any(text.strip().lower().startswith(cmd) for cmd in APPROVAL_COMMANDS)


def _load_kb() -> dict:
    if not YAML_DB_PATH.exists():
        return {}
    with open(YAML_DB_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_kb(kb: dict) -> None:
    with open(YAML_DB_PATH, "w", encoding="utf-8") as f:
        yaml.dump(kb, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _apply_change_to_kb(change: dict) -> bool:
    """
    Schreibt eine approved Änderung in die produktive YAML.
    Returns True bei Erfolg.
    """
    try:
        kb = _load_kb()
        action     = change["action"]
        entry_key  = change["entry_key"]
        new_data   = change.get("new_data")

        if action in ("create", "update"):
            kb[entry_key] = new_data
        elif action == "delete":
            kb.pop(entry_key, None)
        else:
            logger.error(f"Unbekannte Action: {action}")
            return False

        _save_kb(kb)
        logger.info(f"[ApprovalHandler] KB aktualisiert: {action} '{entry_key}'")
        return True

    except Exception as e:
        logger.error(f"[ApprovalHandler] KB-Fehler: {e}")
        return False


# ──────────────────────────────────────────────────────────
# Haupt-Handler
# ──────────────────────────────────────────────────────────

def handle_approval_command(text: str, sender: str) -> str:
    """
    Verarbeitet einen Approval-Befehl und gibt die Antwort zurück
    (wird als Signal-DM an Admin geschickt).

    Unterstützte Befehle:
        !pending              → Liste aller offenen Änderungen
        !approve <ID>         → Änderung freigeben + KB aktualisieren
        !reject <ID>          → Änderung ablehnen
    """
    text = text.strip()
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    # ── !pending ────────────────────────────────────────────
    if cmd == "!pending":
        return ps.pending_summary()

    # ── !approve <ID> ───────────────────────────────────────
    if cmd == "!approve":
        if not arg:
            return "⚠️ Syntax: !approve <ID>  (z.B. !approve A3F9C1)"

        change = ps.approve(arg)
        if change is None:
            return f"❌ Änderung #{arg.upper()} nicht gefunden oder bereits bearbeitet."

        success = _apply_change_to_kb(change)
        if success:
            return (
                f"✅ #{change['short_id']} freigegeben!\n"
                f"Aktion:  {change['action'].upper()}\n"
                f"Eintrag: {change['entry_key']}\n"
                f"KB wurde aktualisiert. Bot nutzt neuen Eintrag ab sofort."
            )
        else:
            return (
                f"⚠️ #{change['short_id']} als approved markiert,\n"
                f"aber KB-Schreiben fehlgeschlagen!\n"
                f"Bitte YAML manuell prüfen: {YAML_DB_PATH}"
            )

    # ── !reject <ID> ────────────────────────────────────────
    if cmd == "!reject":
        if not arg:
            return "⚠️ Syntax: !reject <ID>  (z.B. !reject A3F9C1)"

        change = ps.reject(arg)
        if change is None:
            return f"❌ Änderung #{arg.upper()} nicht gefunden oder bereits bearbeitet."

        return (
            f"🗑️ #{change['short_id']} abgelehnt.\n"
            f"Aktion:  {change['action'].upper()}\n"
            f"Eintrag: {change['entry_key']}\n"
            f"Keine Änderung an der KB."
        )

    return f"❓ Unbekannter Befehl: {cmd}"
