"""
signal_interface.py - JSON-RPC Daemon Mode
UPDATED: Multi-Gruppen Support (None, String oder Liste)

Signal-Schnittstelle für Borgo-Bot v3.5
Nutzt signal-cli daemon via direkter Socket-Kommunikation
"""

import asyncio
import json
import logging
import os
from typing import AsyncIterator, Dict, Optional

logger = logging.getLogger(__name__)

# Konfiguration aus config.py
try:
    from config_multi_bot import SIGNAL_ACCOUNT
except Exception:
    SIGNAL_ACCOUNT = None

try:
    from config_multi_bot import SIGNAL_GROUP_ID
except Exception:
    SIGNAL_GROUP_ID = None

try:
    from config_multi_bot import SIGNAL_CLI_PATH
except Exception:
    SIGNAL_CLI_PATH = "signal-cli"

SIGNAL_CLI_SOCKET = "/tmp/signal-cli-socket"


class SignalInterface:
    """
    Wrapper um signal-cli daemon via JSON-RPC Socket
    - Empfängt Messages via subscribe Method
    - Sendet Messages via send Method
    - ✨ NEU: Unterstützt None (alle Gruppen), String (eine Gruppe) oder Liste (mehrere Gruppen)
    """

    def __init__(
        self,
        number: Optional[str] = None,
        group_id: Optional[str] = None,
        signal_cli: Optional[str] = None,
    ):
        self.signal_cli: str = signal_cli or SIGNAL_CLI_PATH or "signal-cli"
        
        self.number: Optional[str] = (
            number
            or SIGNAL_ACCOUNT
            or os.getenv("SIGNAL_NUMBER")
            or os.getenv("SIGNAL_ACCOUNT")
        )
        
        self.group_id = (
            group_id
            or SIGNAL_GROUP_ID
            or os.getenv("SIGNAL_GROUP_ID")
        )
        
        self.socket_path = os.getenv("SIGNAL_CLI_SOCKET", SIGNAL_CLI_SOCKET)

        if not self.number:
            raise ValueError(
                "SignalInterface: Keine Signal-Nummer konfiguriert. "
                "Bitte SIGNAL_ACCOUNT in config.py setzen."
            )

        # Logging-Ausgabe je nach group_id Typ
        if self.group_id is None:
            logger.info(
                f"📡 SignalInterface (JSON-RPC DAEMON) initialisiert — "
                f"Account={self.number}, GroupID=ALLE, Socket={self.socket_path}"
            )
        elif isinstance(self.group_id, list):
            logger.info(
                f"📡 SignalInterface (JSON-RPC DAEMON) initialisiert — "
                f"Account={self.number}, GroupIDs={len(self.group_id)} Gruppen, "
                f"Socket={self.socket_path}"
            )
        else:
            logger.info(
                f"📡 SignalInterface (JSON-RPC DAEMON) initialisiert — "
                f"Account={self.number}, GroupID={self.group_id}, "
                f"Socket={self.socket_path}"
            )

    # ========================================================
    # Empfangen: JSON-RPC subscribe via Unix Socket
    # ========================================================
    async def listen(self) -> AsyncIterator[Dict]:
        """
        Lauscht auf eingehende Nachrichten via JSON-RPC Socket.

        Yields:
            {"text": str, "sender": str, "group_id": str | None}
        """
        while True:
            try:
                if not os.path.exists(self.socket_path):
                    logger.error(
                        f"❌ signal-cli daemon socket nicht gefunden: {self.socket_path}\n"
                        f"Bitte starte den Daemon in einem separaten Terminal:\n"
                        f"  signal-cli -a {self.number} daemon --socket {self.socket_path}"
                    )
                    await asyncio.sleep(5)
                    continue

                logger.info(f"📡 Verbinde mit JSON-RPC daemon: {self.socket_path}")

                reader, writer = await asyncio.open_unix_connection(self.socket_path)
                
                logger.info("✅ Mit Daemon verbunden, subscribe zu Messages...")

                subscribe_request = {
                    "jsonrpc": "2.0",
                    "method": "subscribe",
                    "params": {"account": self.number},
                    "id": 1
                }
                
                writer.write((json.dumps(subscribe_request) + "\n").encode())
                await writer.drain()

                async for line_bytes in reader:
                    line = line_bytes.decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        logger.debug(f"Nicht-JSON Zeile ignoriert: {line[:100]}")
                        continue

                    if data.get("method") == "receive":
                        params = data.get("params", {})
                        envelope = params.get("envelope", {})
                        
                        source = envelope.get("sourceNumber") or envelope.get("source")
                        
                        sync_message = envelope.get("syncMessage")
                        data_message = envelope.get("dataMessage")
                        
                        message_obj = data_message
                        if not message_obj and sync_message:
                            message_obj = sync_message.get("sentMessage")
                        
                        if not message_obj:
                            continue
                            
                        text = message_obj.get("message", "")
                        if not text:
                            continue

                        group_info = message_obj.get("groupInfo") or message_obj.get("group") or {}
                        group_id = group_info.get("groupId") or group_info.get("id") or self.group_id

                        yield {
                            "text": text,
                            "sender": source,
                            "group_id": group_id,
                        }

                writer.close()
                await writer.wait_closed()
                logger.warning("⚠️ Verbindung zum Daemon unterbrochen — Neustart in 2s...")
                await asyncio.sleep(2)

            except ConnectionRefusedError:
                logger.error(
                    f"❌ Daemon nicht erreichbar auf {self.socket_path}\n"
                    f"Läuft der Daemon? Starte ihn mit:\n"
                    f"  signal-cli -a {self.number} daemon --socket {self.socket_path}"
                )
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ Fehler im Signal-Listener: {e}", exc_info=True)
                await asyncio.sleep(2)

    # ========================================================
    # High-Level: run_listener (von BorgoBot genutzt)
    # ========================================================
    async def run_listener(self, handler):
        """
        Startet einen Listener-Loop und ruft für jede eingehende Nachricht
        den übergebenen Handler auf.

        handler-Signatur:
            async def handler(text: str, sender: str, group_id: str): ...
        """
        async for msg in self.listen():
            text = msg.get("text")
            sender = msg.get("sender")
            group_id = msg.get("group_id")

            if not text:
                continue

            # ✨ NEUE GRUPPEN-FILTERUNG: None, String oder Liste
            if self.group_id:
                # Option A: Liste von erlaubten Gruppen
                if isinstance(self.group_id, list):
                    if group_id not in self.group_id:
                        logger.debug(
                            f"⏭️ Ignoriere Nachricht aus nicht-erlaubter Gruppe: "
                            f"{group_id[:30]}..."
                        )
                        continue
                # Option B: Single String (alte Logik)
                elif group_id != self.group_id:
                    logger.debug(
                        f"⏭️ Ignoriere Nachricht aus anderer Gruppe: "
                        f"{group_id} (erwartet: {self.group_id})"
                    )
                    continue
            # Option C: self.group_id = None → Alle Gruppen erlauben

            try:
                await handler(text, sender, group_id)
            except Exception as e:
                logger.error(f"❌ Fehler im Signal-Handler: {e}", exc_info=True)

    # ========================================================
    # Senden: JSON-RPC send via Unix Socket
    # ========================================================
    async def send(self, text: str, group_id: Optional[str] = None) -> None:
        """
        Sendet eine Nachricht via JSON-RPC Socket.
        KEIN Config-Lock Problem mehr!
        """
        # Target-Gruppe bestimmen
        if group_id:
            target_group = group_id
        elif isinstance(self.group_id, list):
            # Bei Liste: nimm erste Gruppe als Fallback
            target_group = self.group_id[0] if self.group_id else None
        else:
            target_group = self.group_id
        
        if not target_group:
            raise ValueError(
                "SignalInterface.send: Keine group_id angegeben und keine SIGNAL_GROUP_ID gesetzt."
            )

        if not os.path.exists(self.socket_path):
            logger.error(
                f"❌ signal-cli daemon socket nicht gefunden: {self.socket_path}\n"
                f"Bitte starte den Daemon:\n"
                f"  signal-cli -a {self.number} daemon --socket {self.socket_path}"
            )
            return

        logger.info(f"📤 Sende Nachricht via JSON-RPC an group_id={target_group[:30]}...: {text!r}")

        try:
            reader, writer = await asyncio.open_unix_connection(self.socket_path)

            send_request = {
                "jsonrpc": "2.0",
                "method": "send",
                "params": {
                    "account": self.number,
                    "groupId": target_group,
                    "message": text
                },
                "id": 2
            }
            
            writer.write((json.dumps(send_request) + "\n").encode())
            await writer.drain()

            response_line = await asyncio.wait_for(reader.readline(), timeout=10.0)
            response_str = response_line.decode("utf-8", errors="ignore").strip()

            writer.close()
            await writer.wait_closed()

            if response_str:
                response = json.loads(response_str)
                if "error" in response:
                    error = response["error"]
                    logger.error(
                        f"❌ signal-cli daemon send error: {error.get('message', error)}"
                    )
                else:
                    logger.info("✅ Nachricht erfolgreich via JSON-RPC gesendet")
            else:
                logger.warning("⚠️ Keine Response vom Daemon erhalten")

        except asyncio.TimeoutError:
            logger.error("❌ Timeout beim Senden (10s) - Daemon antwortet nicht")
        except Exception as e:
            logger.error(f"❌ Fehler beim Senden via JSON-RPC: {e}", exc_info=True)
