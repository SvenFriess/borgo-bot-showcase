"""
kb_manager.py - Knowledge Base Management via Signal-Kommandos
Borgo-Bot v1.0

Unterstützte Kommandos (nur in DEV-Gruppe):
  !kb add    | schlüssel | kategorie | keyword1,keyword2 | Antworttext
  !kb edit   | schlüssel | keyword1,keyword2 | Neuer Antworttext
  !kb delete | schlüssel
  !kb list
"""

import logging
import re
from pathlib import Path
from typing import Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

KB_COMMAND_PREFIX = "!kb"

HELP_TEXT = """📚 *Knowledge Base Kommandos:*

➕ *Neu hinzufügen:*
`!kb add | schlüssel | kategorie | keyword1,keyword2 | Antworttext`

✏️ *Bearbeiten:*
`!kb edit | schlüssel | keyword1,keyword2 | Neuer Antworttext`

🗑️ *Löschen:*
`!kb delete | schlüssel`

📋 *Alle anzeigen:*
`!kb list`

📖 *Hilfe:*
`!kb help`

*Kategorien:* basics, facilities, safety, rules, contact, emergency, faq, seasonal, technical, general"""


class KBManager:
    """
    Verwaltet YAML Knowledge Base Einträge via Signal-Kommandos.
    Unterstützt add, edit, delete, list.
    """

    def __init__(self, yaml_path: Path):
        self.yaml_path = yaml_path
        if not self.yaml_path.exists():
            raise FileNotFoundError(f"YAML nicht gefunden: {yaml_path}")
        logger.info(f"✅ KBManager initialisiert — {yaml_path}")

    # ------------------------------------------------------------------ #
    # Public: Kommando parsen & ausführen
    # ------------------------------------------------------------------ #

    def is_kb_command(self, text: str) -> bool:
        return text.strip().lower().startswith(KB_COMMAND_PREFIX)

    def handle(self, text: str) -> str:
        """
        Verarbeitet ein !kb-Kommando und gibt eine Antwort zurück.
        """
        text = text.strip()
        parts = [p.strip() for p in text.split("|")]
        command_part = parts[0].strip().lower()

        # Subkommando extrahieren: "!kb add" → "add"
        tokens = command_part.split()
        if len(tokens) < 2:
            return HELP_TEXT

        subcommand = tokens[1]

        try:
            if subcommand == "add":
                return self._handle_add(parts)
            elif subcommand == "edit":
                return self._handle_edit(parts)
            elif subcommand == "delete":
                return self._handle_delete(parts)
            elif subcommand == "list":
                return self._handle_list()
            elif subcommand == "help":
                return HELP_TEXT
            else:
                return f"❓ Unbekanntes Kommando: `{subcommand}`\n\n{HELP_TEXT}"
        except Exception as e:
            logger.error(f"❌ KBManager Fehler: {e}", exc_info=True)
            return f"❌ Fehler beim Ausführen des Kommandos: {e}"

    # ------------------------------------------------------------------ #
    # !kb add
    # ------------------------------------------------------------------ #

    def _handle_add(self, parts: list) -> str:
        """
        Format: !kb add | schlüssel | kategorie | keyword1,keyword2 | Antworttext
        """
        if len(parts) < 5:
            return (
                "❌ Format ungültig. Erwartet:\n"
                "`!kb add | schlüssel | kategorie | keyword1,keyword2 | Antworttext`"
            )

        key = self._sanitize_key(parts[1])
        category = parts[2].strip().lower()
        keywords = [k.strip().lower() for k in parts[3].split(",") if k.strip()]
        answer = parts[4].strip()

        if not key:
            return "❌ Schlüssel darf nicht leer sein."
        if not answer:
            return "❌ Antworttext darf nicht leer sein."

        kb = self._load()

        if key in kb:
            return (
                f"⚠️ Eintrag `{key}` existiert bereits.\n"
                f"Zum Bearbeiten: `!kb edit | {key} | keywords | neue Antwort`"
            )

        kb[key] = {
            "category": category or "general",
            "priority": "medium",
            "synonyms": keywords,
            "content": answer,
        }

        self._save(kb)
        logger.info(f"✅ KB: Neuer Eintrag '{key}' hinzugefügt")
        return (
            f"✅ Eintrag *{key}* hinzugefügt!\n"
            f"📁 Kategorie: {category}\n"
            f"🔑 Keywords: {', '.join(keywords)}\n"
            f"💬 Antwort: {answer[:80]}{'…' if len(answer) > 80 else ''}"
        )

    # ------------------------------------------------------------------ #
    # !kb edit
    # ------------------------------------------------------------------ #

    def _handle_edit(self, parts: list) -> str:
        """
        Format: !kb edit | schlüssel | keyword1,keyword2 | Neuer Antworttext
        """
        if len(parts) < 4:
            return (
                "❌ Format ungültig. Erwartet:\n"
                "`!kb edit | schlüssel | keyword1,keyword2 | Neuer Antworttext`"
            )

        key = self._sanitize_key(parts[1])
        keywords = [k.strip().lower() for k in parts[2].split(",") if k.strip()]
        answer = parts[3].strip()

        if not key:
            return "❌ Schlüssel darf nicht leer sein."

        kb = self._load()

        if key not in kb:
            return (
                f"❌ Eintrag `{key}` nicht gefunden.\n"
                f"Alle Einträge: `!kb list`"
            )

        old_entry = kb[key]
        kb[key]["synonyms"] = keywords if keywords else old_entry.get("synonyms", [])
        kb[key]["content"] = answer if answer else old_entry.get("content", "")

        self._save(kb)
        logger.info(f"✅ KB: Eintrag '{key}' bearbeitet")
        return (
            f"✅ Eintrag *{key}* aktualisiert!\n"
            f"🔑 Keywords: {', '.join(kb[key]['synonyms'])}\n"
            f"💬 Neue Antwort: {kb[key]['content'][:80]}{'…' if len(kb[key]['content']) > 80 else ''}"
        )

    # ------------------------------------------------------------------ #
    # !kb delete
    # ------------------------------------------------------------------ #

    def _handle_delete(self, parts: list) -> str:
        """
        Format: !kb delete | schlüssel
        """
        if len(parts) < 2:
            return "❌ Format ungültig. Erwartet:\n`!kb delete | schlüssel`"

        key = self._sanitize_key(parts[1])

        if not key:
            return "❌ Schlüssel darf nicht leer sein."

        kb = self._load()

        if key not in kb:
            return f"❌ Eintrag `{key}` nicht gefunden."

        del kb[key]
        self._save(kb)
        logger.info(f"✅ KB: Eintrag '{key}' gelöscht")
        return f"🗑️ Eintrag *{key}* wurde gelöscht."

    # ------------------------------------------------------------------ #
    # !kb list
    # ------------------------------------------------------------------ #

    def _handle_list(self) -> str:
        """
        Gibt alle Einträge gruppiert nach Kategorie zurück.
        """
        kb = self._load()

        if not kb:
            return "📋 Knowledge Base ist leer."

        # Nach Kategorie gruppieren
        by_category: dict = {}
        for key, entry in kb.items():
            cat = entry.get("category", "general")
            by_category.setdefault(cat, []).append(key)

        lines = [f"📋 *Knowledge Base — {len(kb)} Einträge:*\n"]
        for cat in sorted(by_category.keys()):
            keys = sorted(by_category[cat])
            lines.append(f"*{cat.upper()}*")
            for k in keys:
                lines.append(f"  • {k}")

        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Hilfsmethoden
    # ------------------------------------------------------------------ #

    def _load(self) -> dict:
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}

    def _save(self, kb: dict) -> None:
        with open(self.yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(
                kb,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=True,
            )
        logger.info(f"💾 YAML gespeichert: {self.yaml_path}")

    def _sanitize_key(self, key: str) -> str:
        """Bereinigt Schlüssel: Kleinbuchstaben, nur Buchstaben/Zahlen/Unterstrich"""
        key = key.strip().lower()
        key = re.sub(r"[^a-z0-9_äöüß]", "_", key)
        key = re.sub(r"_+", "_", key).strip("_")
        return key
