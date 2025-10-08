import asyncio
import random
from datetime import datetime, timedelta

from faker import Faker
from loguru import logger

from data.constants import EXT_WORLD_LIST
from data.settings import Settings
from libs.eth_async.client import Client
from libs.eth_async.data.models import Network, Networks
from utils.db_api.models import Wallet
from utils.db_api.wallet_api import (
    get_random_invite_code,
    mark_complete_pioner_galxe,
    twitter_creation_at,
    update_points,
    update_rank,
    update_ref_code,
    update_twitter_followers,
)
from utils.galxe.galxe_client import GalxeClient
from utils.resource_manager import ResourceManager
from utils.retry import async_retry
from utils.twitter.twitter_client import TwitterClient


class Quests:
    def __init__(self, client: Client, wallet: Wallet):
        self.client = client
        self.wallet = wallet
        self.proxy_errors = 0
        self.twitter_client = TwitterClient(user=self.wallet)

    async def update_points(self, galxe_client):
        points, rank = await galxe_client.update_points_and_rank(campaign_id=81173)
        update_points(address=self.wallet.address, points=points)
        update_rank(address=self.wallet.address, rank=rank)
        logger.info(f"{self.wallet} have {self.wallet.points} points and rank {self.wallet.rank} in Galxe")

    async def complete_quests(self, galxe_client: GalxeClient):
        campaign_ids = ["GCpict6X7N", "GC5mTt8px6", "GCoUVt8dHz"]

        for campaign_id in campaign_ids:
            data = await self._get_campaign_data(galxe_client, campaign_id)
            await self._save_ref_code(campaign_id=campaign_id, ref_code=data["referralCode"])
            data = data["taskConfig"]
            participate_tiers = self._parse_participate_tiers(data)
            reward_tiers = self._parse_reward_tiers(data)
            reward_claimed = reward_tiers[0]["rewardCount"]
            logger.debug(f"{self.wallet} Rewards Claimed For campaign ({campaign_id}): {reward_claimed}")
            referral_tiers = self._parse_referral_tiers(data)

            await self._process_rewards(galxe_client, campaign_id, reward_tiers)
            await self._ensure_participation(galxe_client, participate_tiers)
            await self._referral_sync(galxe_client, referral_tiers)

            await self._try_claim_points(galxe_client, campaign_id, reward_claimed)

    @async_retry()
    async def _get_campaign_data(self, galxe_client, campaign_id: str):
        info = await galxe_client.get_quest_cred_list(campaign_id=campaign_id)
        return info["data"]["campaign"]

    async def _save_ref_code(self, campaign_id: str, ref_code: str):
        if campaign_id == "GCpict6X7N" and self.wallet.first_quest_invite:
            return True
        elif campaign_id == "GC5mTt8px6" and self.wallet.second_quest_invite:
            return True
        elif campaign_id == "GCoUVt8dHz" and self.wallet.third_quest_invite:
            return True
        return update_ref_code(id=self.wallet.id, quest=campaign_id, ref_code=ref_code)

    def _parse_participate_tiers(self, task_config):
        return [
            {
                "cred_id": int(cond["cred"]["id"]),
                "eligible": cond["eligible"],
                "name": cond["cred"]["name"],
                "attrs": cond["attrs"],
            }
            for cond in task_config["participateCondition"]["conditions"]
        ]

    def _parse_referral_tiers(self, task_config):
        return [
            {
                "cred_id": int(cond["cred"]["id"]),
                "eligible": cond["eligible"],
                "name": cond["cred"]["name"],
                "attrs": cond["attrs"],
            }
            for cond in task_config["referralConfig"]["conditions"]
        ]

    def _parse_reward_tiers(self, task_config):
        result = []
        for config in task_config["rewardConfigs"]:
            for condition in config["conditions"]:
                cred = condition["cred"]
                result.append(
                    {
                        "cred_id": int(cred["id"]),
                        "exp_reward": int(config["rewards"][0]["arithmeticFormula"]),
                        "eligible": config["eligible"],
                        "name": cred["name"],
                        "rewardCount": config["rewards"][0]["rewardCount"],
                    }
                )
        return result

    async def _process_rewards(self, galxe_client, campaign_id, reward_tiers):
        for tier in reward_tiers:
            if tier["eligible"]:
                continue

            for attempt in range(Settings().retry):
                success = await self._handle_tier(galxe_client, campaign_id, tier)
                if success:
                    logger.success(f"{self.wallet} success sync quest for {tier['name']} on Galxe. Sleep 60s")
                    await asyncio.sleep(60)
                    break
                else:
                    logger.warning(f"{self.wallet} can't sync quest for {tier['name']}, attempt {attempt + 1}")
                    await asyncio.sleep(30)

    @async_retry()
    async def _handle_tier(self, galxe_client, campaign_id, tier):
        name = tier["name"]

        if "Follow Forte Foundation" in name:
            await galxe_client.follow_space(space_id=81173)
            await asyncio.sleep(random.randint(3, 5))
            return await galxe_client.sync_quest(cred_id=tier["cred_id"])

        elif "Tweet Bullish About @ForteProtocol" in name:
            return await self._tweet_and_sync(galxe_client, tier)

        elif any(x in name for x in ["X", "Twitter", "Tweet"]):
            return await galxe_client.sync_twitter_quest(cred_id=tier["cred_id"], campaign_id=campaign_id)

        elif "Quiz" in name:
            return await galxe_client.sync_quiz(cred_id=tier["cred_id"], answers=["1", "0", "2", "3"])

        logger.debug(f"{self.wallet} quest not recognized: {tier}")
        return False

    async def _tweet_and_sync(self, galxe_client, tier):
        faker = Faker()
        text = faker.text(max_nb_chars=random.randint(20, 40), ext_word_list=EXT_WORLD_LIST)
        text += " @ForteProtocol #ProofOfFortification"
        tweet = await self.twitter_client.post_tweet(text=text)
        if not tweet:
            logger.error(f"{self.wallet} can't tweet for quest")
            return False

        logger.info(f"{self.wallet} sleep 30s after tweet post")
        await asyncio.sleep(30)
        for attempt in range(Settings().retry):
            sync = await galxe_client.sync_quest(cred_id=tier["cred_id"])
            if sync:
                await self.twitter_client.delete_tweet(tweet=tweet.id)
                return True
            logger.warning(f"{self.wallet} sync failed, retry {attempt + 1}")
            await asyncio.sleep(30)
        return False

    async def _ensure_participation(self, galxe_client, participate_tiers):
        tier = participate_tiers[0]
        if not tier["eligible"]:
            for _ in range(Settings().retry):
                sync = await galxe_client.sync_credit_value(attrs=tier["attrs"], cred_id=str(tier["cred_id"]))
                if sync:
                    logger.success(f"{self.wallet} success sync requirements criteria on Galxe. Sleep 60s")
                    await asyncio.sleep(60)
                    return

                random_sleep = random.randint(80, 100)
                logger.info(f"{self.wallet} sync delayed. Auto retry in {random_sleep}s. ({_ + 1}/{Settings().retry}). No action needed")
                await asyncio.sleep(random_sleep)

    async def _referral_sync(self, galxe_client, referral_tiers):
        tier = referral_tiers[0]
        sync = await galxe_client.sync_credit_value(attrs=tier["attrs"], cred_id=str(tier["cred_id"]))
        if sync:
            logger.success(f"{self.wallet} success sync Referral quest on Galxe. Sleep 60s")
            await asyncio.sleep(60)
            return
        else:
            logger.debug(f"{self.wallet} can't sync for Referral quest on Galxe.")
            return

    @async_retry()
    async def _try_claim_points(self, galxe_client, campaign_id, reward_claimed: int):
        if await galxe_client.get_subscription() or await self.check_available_claim():
            ref_code = get_random_invite_code(id=self.wallet.id, quest=campaign_id) if reward_claimed == 0 else None
            logger.debug(f"{self.wallet} choose ref code: {ref_code}. For complete quest: {campaign_id}")
            if await galxe_client.claim_points(campaign_id=campaign_id, ref_code=ref_code):
                if campaign_id == "GCoUVt8dHz":
                    logger.success(f"{self.wallet} success complete Pioneer Stone Campaign!. Sleep for 2m")
                    mark_complete_pioner_galxe(address=self.wallet.address)
                    await asyncio.sleep(120)
                await asyncio.sleep(15)

    async def get_tweet_url(self, id: str):
        text = f"Verifying my Twitter account for my #GalxeID gid:{id} @Galxe "
        tweet = await self.twitter_client.post_tweet(text=text)
        if tweet:
            return f"https://x.com/{self.twitter_client.twitter_account.username}/status/{tweet.id}"

    @async_retry(delay=60)
    async def check_twitter_connect(self, galxe_client):
        self.twitter_client = TwitterClient(user=self.wallet)
        if self.wallet.twitter_status != "OK" and not Settings().auto_replace_twitter:
            logger.warning(f"{self.wallet} twitter status is {self.wallet.twitter_status}. Skip Twitter quests")
            return False
        if not self.wallet.twitter_token:
            logger.warning(f"{self.wallet} doesn't have twitter tokens for twitters action")
            return False

        if not await self.twitter_client.initialize() and Settings().auto_replace_twitter:
            logger.warning(f"{self.wallet} can't initialize Twitter")
            resource_manager = ResourceManager()
            replace = await resource_manager.replace_twitter(id=self.wallet.id)
            if replace:
                return await self.check_twitter_connect(galxe_client=galxe_client)
            else:
                logger.error(f"{self.wallet} can't initialize and connect Twitter!")
                return False

        follow_numbers = self.twitter_client.twitter_account.followers_count
        if not follow_numbers:
            follow_numbers = 0
        logger.debug(f"{self.wallet} follow numbers: {follow_numbers}")
        update_twitter_followers(address=self.wallet.address, followers=follow_numbers)
        created_at_twitter = self.twitter_client.twitter_account.created_at
        logger.debug(f"{self.wallet} created_at_twitter: {created_at_twitter}")
        if created_at_twitter:
            twitter_creation_at(address=self.wallet.address, creation_at=created_at_twitter)
        if follow_numbers and follow_numbers < 28 or created_at_twitter and datetime.now() - created_at_twitter < timedelta(days=91):
            logger.warning(
                f"{self.wallet} can't complete Forto Galxe Campaign with this twitter account. Followers count: {follow_numbers}. Minimum need followers 28. Twitter created at: {created_at_twitter}. Need twitter > 3 months age. Please replace or upgrade this twitter token"
            )
            return False

        session = await galxe_client.session()
        twitter_connect_id = session["data"]["addressInfo"]["twitterUserID"]
        twitter_id = self.twitter_client.twitter_account.id

        if twitter_connect_id and int(twitter_connect_id) != int(twitter_id):
            logger.warning(f"{self.wallet} twitter Galxe Account does not match twitter in DataBase. Replace Twitter Account")
            twitter_connect_id = None
            await galxe_client.delete_social_account(social="twitter")
            logger.success(f"{self.wallet} success delete old twitter account from Galxe.")
            await asyncio.sleep(5)

        if not twitter_connect_id:
            id = session["data"]["addressInfo"]["id"]
            tweet_url = await self.get_tweet_url(id=id)
            if not tweet_url:
                logger.error(f"{self.wallet} can't post tweets")
                return False
            connect = await galxe_client.connect_twitter(tweet_url=tweet_url)
            if connect["data"]["verifyTwitterAccount"]["twitterUserID"]:
                logger.success(f"{self.wallet} success twitter connect")
                return True
        return True

    async def check_available_claim(self):
        gravity_balance = await self.client.wallet.balance()
        if gravity_balance.Ether > 2.5:
            return True
        network_values = [value for key, value in Networks.__dict__.items() if isinstance(value, Network)]
        random.shuffle(network_values)
        for network in network_values:
            if network.name in Settings().network_for_bridge:
                try:
                    client = Client(private_key=self.client.account._private_key.hex(), network=network, proxy=self.client.proxy)
                    balance = await client.wallet.balance()
                    if balance.Ether > Settings().random_eth_for_bridge_max:
                        return True
                except Exception as e:
                    logger.warning(f"{self.wallet} can't check network {network.name} error: {e}")
                    continue
        return False
