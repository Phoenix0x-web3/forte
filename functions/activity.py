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

    settings = Settings()
    sleep_s = 30
    max_retries = settings.retry
    auto_replace = settings.auto_replace_proxy

    def build_controller(w):
        client = Client(private_key=w.private_key, proxy=w.proxy, network=Networks.Gravity)
        return Controller(client=client, wallet=w)

    controller = build_controller(wallet)

    errors = 0
    while True:
        try:
            await controller.base.browser.get(url="https://api.ipify.org")
            break  # proxy OK
        except Exception as e:
            errors += 1
            logger.error(f"{controller.wallet} Proxy error: {e}. Retry {errors}/{max_retries}")

            if errors < max_retries:
                logger.info(f"{controller.wallet} sleeping {sleep_s}s before retry")
                await asyncio.sleep(sleep_s)
                continue

            if not auto_replace:
                logger.error(f"{controller.wallet} proxy issue {errors}/{max_retries}; auto-replace disabled -> abort")
                return

            logger.warning(f"{controller.wallet} retries exhausted; attempting proxy replacement")
            rm = ResourceManager()
            await rm.mark_proxy_as_bad(controller.wallet.id)
            success, message = await rm.replace_proxy(controller.wallet.id)
            if not success:
                logger.error(f"{controller.wallet} failed to replace proxy: {message}")
                return

            logger.success(f"{controller.wallet} proxy replaced: {message}")

            wallet = get_wallet_by_address(address=controller.wallet.address) or controller.wallet

            controller = build_controller(wallet)
            errors = 0

    return await controller.complete_galxe_quests()
