"""
Message Deduplication für Borgo-Bot
Verhindert doppelte Verarbeitung durch Multi-Worker
"""

import threading
import time
from typing import Set, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MessageFingerprint:
    """Eindeutige Message-Identifikation"""
    text: str
    sender: str
    timestamp: float
    
    def __hash__(self):
        # Kombiniere Text + Sender für eindeutigen Hash
        # Timestamp auf Sekunden runden (gegen Race Conditions)
        rounded_ts = int(self.timestamp)
        return hash((self.text[:100], self.sender, rounded_ts))
    
    def __eq__(self, other):
        if not isinstance(other, MessageFingerprint):
            return False
        return hash(self) == hash(other)


class MessageDeduplicator:
    """
    Thread-safe Message Deduplication
    Hält Track von bereits verarbeiteten Messages mit TTL
    """
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Args:
            ttl_seconds: Time-To-Live für Message-IDs (Standard: 5 Min)
        """
        self.ttl_seconds = ttl_seconds
        self.processed: Set[MessageFingerprint] = set()
        self.timestamps: dict = {}  # fingerprint -> processing_time
        self.lock = threading.Lock()
        
        logger.info(f"🔒 MessageDeduplicator initialized (TTL: {ttl_seconds}s)")
    
    def is_duplicate(
        self,
        text: str,
        sender: str,
        timestamp: Optional[float] = None
    ) -> bool:
        """
        Prüft ob Message bereits verarbeitet wurde
        
        Args:
            text: Message-Text
            sender: Sender-ID
            timestamp: Optional timestamp (sonst current time)
        
        Returns:
            True wenn Duplikat, False wenn neu
        """
        if timestamp is None:
            timestamp = time.time()
        
        fingerprint = MessageFingerprint(text, sender, timestamp)
        
        with self.lock:
            # Cleanup alte Entries
            self._cleanup_old_entries()
            
            # Check ob schon verarbeitet
            if fingerprint in self.processed:
                logger.info(f"⏭️  Duplicate message detected: '{text[:50]}...' from {sender}")
                return True
            
            # Als verarbeitet markieren
            self.processed.add(fingerprint)
            self.timestamps[fingerprint] = time.time()
            
            logger.debug(f"✅ New message registered: '{text[:50]}...' from {sender}")
            return False
    
    def _cleanup_old_entries(self):
        """Entfernt abgelaufene Entries (intern, lock assumed)"""
        current_time = time.time()
        expired = []
        
        for fingerprint, process_time in self.timestamps.items():
            if current_time - process_time > self.ttl_seconds:
                expired.append(fingerprint)
        
        for fingerprint in expired:
            self.processed.discard(fingerprint)
            del self.timestamps[fingerprint]
        
        if expired:
            logger.debug(f"🧹 Cleaned up {len(expired)} expired message(s)")
    
    def get_stats(self) -> dict:
        """Gibt Statistiken zurück"""
        with self.lock:
            return {
                'tracked_messages': len(self.processed),
                'ttl_seconds': self.ttl_seconds,
            }
    
    def clear(self):
        """Löscht alle tracked Messages (für Tests/Debug)"""
        with self.lock:
            count = len(self.processed)
            self.processed.clear()
            self.timestamps.clear()
            logger.info(f"🗑️  Cleared {count} tracked message(s)")
