# ============================================================
# BORGO-BOT - APPROVAL SYSTEM: INTEGRATION PATCHES
# ============================================================
# Zeigt genau welche Stellen in den bestehenden Dateien
# geändert/ergänzt werden müssen.
# ============================================================


# ────────────────────────────────────────────────────────────
# 1) kb_api.py  – Saves abfangen → pending statt direkt YAML
# ────────────────────────────────────────────────────────────
#
# Am Anfang der Datei ergänzen:
# ─────────────────────────────
import pending_store as ps
from approval_notifier import notify_admin_new_change
import yaml


# ─────────────────────────────────────────────────────────────
# Die bestehende Save-Route (PUT /entries/{key} oder POST /entries)
# wird so umgebaut (Beispiel FastAPI):
# ─────────────────────────────────────────────────────────────

# VORHER (direkt in YAML schreiben):
# -----------------------------------
# @app.put("/entries/{key}")
# def update_entry(key: str, entry: EntryModel):
#     kb = load_kb()
#     kb[key] = entry.dict()
#     save_kb(kb)
#     return {"status": "saved"}

# NACHHER (in Pending-Store schreiben):
# --------------------------------------
# @app.put("/entries/{key}")
# def update_entry(key: str, entry: EntryModel):
#     kb = load_kb()
#     old_data = kb.get(key)                       # für Vergleich/Rollback
#     action   = "update" if old_data else "create"
#     new_data = entry.dict()
#
#     short_id = ps.add_change(
#         action    = action,
#         entry_key = key,
#         new_data  = new_data,
#         old_data  = old_data,
#         editor    = "kb-editor",
#     )
#
#     # Vorschau für Signal-Nachricht
#     preview = new_data.get("answer", new_data.get("content", str(new_data)))[:120]
#     notify_admin_new_change(short_id, action, key, preview)
#
#     return {"status": "pending", "id": short_id,
#             "message": f"Änderung #{short_id} wartet auf Admin-Freigabe"}

# Analog für DELETE:
# ------------------
# @app.delete("/entries/{key}")
# def delete_entry(key: str):
#     kb = load_kb()
#     old_data = kb.get(key)
#     if not old_data:
#         raise HTTPException(404, "Eintrag nicht gefunden")
#
#     short_id = ps.add_change(
#         action    = "delete",
#         entry_key = key,
#         new_data  = {},
#         old_data  = old_data,
#         editor    = "kb-editor",
#     )
#     notify_admin_new_change(short_id, "delete", key, str(old_data)[:120])
#
#     return {"status": "pending", "id": short_id,
#             "message": f"Löschung #{short_id} wartet auf Admin-Freigabe"}


# ────────────────────────────────────────────────────────────
# 2) borgo_bot_multi.py  – !approve / !reject / !pending
# ────────────────────────────────────────────────────────────
#
# Am Anfang der Datei ergänzen:
# ─────────────────────────────
from approval_handler import is_approval_command, handle_approval_command


# In der Message-Handler-Funktion (dort wo eingehende Nachrichten
# ausgewertet werden), VOR der normalen Bot-Logik einfügen:
# ─────────────────────────────────────────────────────────────

# def handle_message(sender: str, text: str, group_id: str = None):
#
#     # ── Approval-Befehle (nur Admin, nur DM) ───────────────
#     if is_approval_command(text, sender):
#         response = handle_approval_command(text, sender)
#         send_signal_message(recipient=sender, message=response)
#         return
#
#     # ── Normaler Bot-Flow ──────────────────────────────────
#     # ... bestehender Code ...


# ────────────────────────────────────────────────────────────
# 3) config.py  – Approval-Sektion ergänzen
# ────────────────────────────────────────────────────────────
#
# Nach der SIGNAL INTEGRATION Sektion einfügen:

APPROVAL_CONFIG = """
# ========================================
# APPROVAL SYSTEM
# ========================================

ADMIN_NUMBER          = "+4915755901211"   # Einziger Approver
PENDING_FILE          = "pending_changes.yaml"
APPROVAL_COMMANDS     = ("!approve", "!reject", "!pending")

FEATURES['approval_workflow'] = True      # Feature-Flag
"""


# ────────────────────────────────────────────────────────────
# 4) KB-Editor Frontend  – Status-Badge (optional)
# ────────────────────────────────────────────────────────────
#
# GET /entries kann um ein "pending"-Flag erweitert werden:
#
# @app.get("/entries")
# def list_entries():
#     kb = load_kb()
#     pending = {c["entry_key"] for c in ps.get_pending()}
#     result = {}
#     for key, val in kb.items():
#         result[key] = val
#         result[key]["_pending"] = key in pending   # 🟡 Badge im Frontend
#     return result
#
# Im HTML/JS dann z.B.:
#   if (entry._pending) badge.textContent = "⏳ Pending";
