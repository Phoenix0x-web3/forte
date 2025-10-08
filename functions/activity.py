import asyncio
import random
from datetime import datetime, timedelta
from typing import List

from loguru import logger

from data.settings import Settings
from functions.controller import Controller
from libs.eth_async.client import Client
from libs.eth_async.data.models import Networks
from utils.db_api.models import Wallet
from utils.db_api.wallet_api import db, get_wallet_by_address
from utils.encryption import check_encrypt_param
from utils.resource_manager import ResourceManager


async def random_sleep_before_start(wallet):
    random_sleep = random.randint(Settings().random_pause_start_wallet_min, Settings().random_pause_start_wallet_max)
    now = datetime.now()

    logger.info(f"{wallet} Start at {now + timedelta(seconds=random_sleep)} sleep {random_sleep} seconds before start actions")
    await asyncio.sleep(random_sleep)


async def execute(wallets: List[Wallet], task_func, random_pause_wallet_after_completion: int = 0):
    while True:
        semaphore = asyncio.Semaphore(min(len(wallets), Settings().threads))

        if Settings().shuffle_wallets:
            random.shuffle(wallets)

        async def sem_task(wallet: Wallet):
            async with semaphore:
                try:
                    await task_func(wallet)
                except Exception as e:
                    logger.error(f"[{wallet.id}] failed: {e}")

        tasks = [asyncio.create_task(sem_task(wallet)) for wallet in wallets]
        await asyncio.gather(*tasks, return_exceptions=True)

        if random_pause_wallet_after_completion == 0:
            break

        # update dynamically the pause time
        next_run = datetime.now() + timedelta(seconds=random_pause_wallet_after_completion)
        logger.info(f"Sleeping {random_pause_wallet_after_completion} seconds. Next run at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        await asyncio.sleep(random_pause_wallet_after_completion)


async def activity(action: int):
    if not check_encrypt_param():
        logger.error(f"Decryption Failed | Wrong Password")
        return

    wallets = db.all(Wallet)
    range_wallets = Settings().range_wallets_to_run
    if range_wallets != [0, 0]:
        start, end = range_wallets
        wallets = [wallet for i, wallet in enumerate(wallets, start=1) if start <= i <= end]
    else:
        if Settings().exact_wallets_to_run:
            wallets = [wallet for i, wallet in enumerate(wallets, start=1) if i in Settings().exact_wallets_to_run]

    logger.info(f"Found {len(wallets)} wallets for action")
    if action == 1 and wallets:
        await execute(
            wallets,
            start_main_action,
            random.randint(Settings().random_pause_wallet_after_all_completion_min, Settings().random_pause_wallet_after_all_completion_max),
        )


async def start_main_action(wallet):
    await random_sleep_before_start(wallet=wallet)

    client = Client(private_key=wallet.private_key, proxy=wallet.proxy, network=Networks.Gravity)

    controller = Controller(client=client, wallet=wallet)

    for _ in range(Settings().retry):
        try:
            await controller.base.browser.get(url="https://api.ipify.org")
            break
        except Exception as e:
            if not Settings().auto_replace_proxy:
                logger.error(f"{controller.wallet} proxy issue and auto replace disabled")
                continue

            resource_manager = ResourceManager()
            await resource_manager.mark_proxy_as_bad(controller.wallet.id)
            logger.error(f"{controller.wallet} Proxy error: {e}.")
            success, message = await resource_manager.replace_proxy(controller.wallet.id)
            if success:
                logger.success(f"{controller.wallet} | proxy automatically replaced: {message}")
                updated_user = get_wallet_by_address(address=controller.wallet.address)
                if updated_user:
                    client = Client(private_key=wallet.private_key, proxy=updated_user.proxy, network=Networks.Gravity)
                    controller = Controller(client=client, wallet=wallet)
            else:
                logger.error(f"{controller.wallet} | failed to replace proxy: {message}")
                return

    return await controller.complete_galxe_quests()
