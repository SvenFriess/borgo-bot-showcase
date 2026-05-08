"""
Borgo-Bot - Approval Notifier
Schickt dem Admin per Signal eine DM wenn eine neue KB-Änderung pending ist.
Datei: approval_notifier.py

Wird aus kb_api.py aufgerufen, nachdem add_change() einen neuen Eintrag erstellt hat.

Beispiel-Aufruf:
    from approval_notifier import notify_admin_new_change
    notify_admin_new_change(short_id="A3F9C1", action="update",
                            entry_key="pizzaofen", preview="Heize den Ofen 45 Min...")
"""

import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Konfiguration ──────────────────────────────────────────
ADMIN_NUMBER   = "+4915755901211"
SIGNAL_ACCOUNT = "+4915755901211"          # Deine Bot-Nummer (ggf. anpassen)
SIGNAL_CLI     = Path("/usr/local/bin/signal-cli")   # Pfad zu signal-cli


def _send_signal_dm(recipient: str, message: str) -> bool:
    """
    Sendet eine Signal-DM über signal-cli send.
    Gibt True bei Erfolg zurück.
    """
    try:
        result = subprocess.run(
            [
                str(SIGNAL_CLI),
                "-a", SIGNAL_ACCOUNT,
                "send",
                "-m", message,
                recipient,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            logger.info(f"[Notifier] DM an {recipient} gesendet.")
            return True
        else:
            logger.error(f"[Notifier] signal-cli Fehler: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        logger.error(f"[Notifier] signal-cli nicht gefunden: {SIGNAL_CLI}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("[Notifier] signal-cli Timeout")
        return False
    except Exception as e:
        logger.error(f"[Notifier] Unerwarteter Fehler: {e}")
        return False


def notify_admin_new_change(short_id: str, action: str,
                             entry_key: str, preview: str = "") -> None:
    """
    Benachrichtigt den Admin über eine neue pending Änderung.

    Args:
        short_id:  6-stellige Änderungs-ID
        action:    'create' | 'update' | 'delete'
        entry_key: Schlüssel des KB-Eintrags
        preview:   Erste ~100 Zeichen des neuen Inhalts
    """
    # Vorschau kürzen
    preview_short = (preview[:120] + "…") if len(preview) > 120 else preview

    action_emoji = {
        "create": "🆕",
        "update": "✏️",
        "delete": "🗑️",
    }.get(action, "📝")

    message = (
        f"📋 Neue KB-Änderung wartet auf Freigabe\n"
        f"──────────────────────\n"
        f"ID:      #{short_id}\n"
        f"Aktion:  {action_emoji} {action.upper()}\n"
        f"Eintrag: {entry_key}\n"
        f"──────────────────────\n"
        f"Vorschau:\n{preview_short}\n"
        f"──────────────────────\n"
        f"✅ !approve {short_id}\n"
        f"❌ !reject {short_id}\n"
        f"📋 !pending  (alle offenen)"
    )

    _send_signal_dm(ADMIN_NUMBER, message)
