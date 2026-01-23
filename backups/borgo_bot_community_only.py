#!/usr/bin/env python3
"""
Borgo-Bot v0.99 - Community-Test Only
Vereinfachte Version die nur den Community-Test Bot startet
"""

import asyncio
import logging
from borgo_bot_multi import BorgoBotInstance, SignalInterface, MessageDeduplicator
from config_multi_bot import COMMUNITY_TEST_BOT_CONFIG, GROUP_IDS, BOT_COMMAND_PREFIX, is_allowed_group

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("=" * 80)
    logger.info("🚀 Starting Borgo-Bot v0.99 - COMMUNITY-TEST ONLY")
    logger.info("=" * 80)
    
    signal_interface = SignalInterface(group_id=None)
    deduplicator = MessageDeduplicator(ttl_seconds=300)
    
    # Nur Community-Test Bot
    community_bot = BorgoBotInstance(COMMUNITY_TEST_BOT_CONFIG)
    logger.info(f"✅ {community_bot.name} initialized for Community-Test Group")
    logger.info("=" * 80 + "\n")
    
    async def handler(text: str, sender: str, group_id: str):
        if not text.lower().startswith(BOT_COMMAND_PREFIX):
            return
        
        if not is_allowed_group(group_id):
            logger.warning(f"⛔ Unauthorized group: {group_id[:20]}...")
            return
        
        if deduplicator.is_duplicate(text, sender):
            logger.info(f"⏭️  Skipping duplicate from {sender}")
            return
        
        # Nur Community-Test Gruppe
        if group_id == GROUP_IDS['community_test']:
            logger.info(f"💬 [{community_bot.name}] Processing from {sender[:10]}...")
            
            logger.info(f"📨 [{community_bot.name}] Processing: '{text[:50]}...'")
            
            response, success = await community_bot.process_message(text, sender)
            
            if response:
                await signal_interface.send(response, group_id=group_id)
                logger.info(f"📤 [{community_bot.name}] Sent response")
            else:
                logger.warning(f"⚠️  [{community_bot.name}] No response generated")
        else:
            logger.warning(f"⚠️  Message from non-community group: {group_id[:20]}...")
    
    await signal_interface.run_listener(handler)

if __name__ == "__main__":
    asyncio.run(main())
