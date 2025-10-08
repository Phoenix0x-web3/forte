import asyncio
from loguru import logger
from datetime import datetime,timedelta
import random
from data.settings import Settings
from libs.eth_async.client import Client
from libs.base import Base
from libs.eth_async.data.models import Networks
from modules.quests_client import Quests

from utils.db_api.models import Wallet
from utils.galxe.galxe_client import GalxeClient
from utils.twitter.twitter_client import TwitterClient


class Controller:

    def __init__(self, client: Client, wallet: Wallet):
        #super().__init__(client)
        self.client = client
        self.wallet = wallet
        self.base = Base(client=client, wallet=wallet)
        self.quest_client = Quests(client=client,wallet=wallet)

    async def complete_galxe_quests(self):
        galxe_client = GalxeClient(wallet=self.wallet, client=self.client)
        if not Settings().use_banned_galxe and await galxe_client.is_account_banned():
            return False
        if not self.wallet.points or self.wallet.points and self.wallet.points < 65:
            if not await self.quest_client.check_twitter_connect(galxe_client=galxe_client):
                return False

        functions = [
            self.quest_client.complete_quests,
        ]
        random.shuffle(functions)
        for func in functions:
            try:
                await func(galxe_client)
            except Exception as e:
                logger.error(f"{self.wallet} wrong with galxe quest: {e}")
                continue
        await self.quest_client.update_points(galxe_client)
        return

