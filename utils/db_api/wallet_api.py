import random

from data.config import WALLETS_DB
from data.settings import Settings
from utils.db_api.db import DB
from utils.db_api.models import Base, Wallet


def get_wallets(sqlite_query: bool = False) -> list[Wallet]:
    if sqlite_query:
        return db.execute("SELECT * FROM wallets")

    return db.all(entities=Wallet)


def get_wallet_by_private_key(private_key: str, sqlite_query: bool = False) -> Wallet | None:
    if sqlite_query:
        return db.execute("SELECT * FROM wallets WHERE private_key = ?", (private_key,), True)

    return db.one(Wallet, Wallet.private_key == private_key)


def get_wallet_by_address(address: str, sqlite_query: bool = False) -> Wallet | None:
    if sqlite_query:
        return db.execute("SELECT * FROM wallets WHERE address = ?", (address,), True)

    return db.one(Wallet, Wallet.address == address)


def update_twitter_token(address: str, updated_token: str | None) -> bool:
    """
    Updates the Twitter token for a wallet with the given private_key.

    Args:
        address: The address of the wallet to update
        new_token: The new Twitter token to set

    Returns:
        bool: True if update was successful, False if wallet not found
    """
    if not updated_token:
        return False

    wallet = db.one(Wallet, Wallet.address == address)
    if not wallet:
        return False

    wallet.twitter_token = updated_token
    db.commit()
    return True


def update_next_action_time(address: str, next_action_time) -> bool:
    wallet = db.one(Wallet, Wallet.address == address)
    if not wallet:
        return False
    wallet.next_action_time = next_action_time
    db.commit()
    return True


def mark_galxe_account_banned(id: int) -> bool:
    wallet = db.one(Wallet, Wallet.id == id)
    if not wallet:
        return False
    wallet.galxe_account_banned = True
    db.commit()
    return True


def mark_complete_pioner_galxe(address: str):
    wallet = db.one(Wallet, Wallet.address == address)
    if not wallet:
        return False
    wallet.pioner_galxe_completed = True
    db.commit()
    return True


def update_rank(address: str, rank: int) -> bool:
    wallet = db.one(Wallet, Wallet.address == address)
    if not wallet:
        return False

    wallet.rank = rank
    db.commit()
    return True


def update_points(address: str, points: int) -> bool:
    wallet = db.one(Wallet, Wallet.address == address)
    if not wallet:
        return False

    wallet.points = points
    db.commit()
    return True


def update_twitter_followers(address: str, followers: int) -> bool:
    wallet = db.one(Wallet, Wallet.address == address)
    if not wallet:
        return False

    wallet.twitter_follow_count = followers
    db.commit()
    return True


def add_count_game(address: str) -> bool:
    wallet = db.one(Wallet, Wallet.address == address)
    if not wallet:
        return False
    if not wallet.completed_games:
        wallet.completed_games = 1

    wallet.completed_games += 1
    db.commit()
    return True


def replace_bad_proxy(id: int, new_proxy: str) -> bool:
    wallet = db.one(Wallet, Wallet.id == id)
    if not wallet:
        return False
    wallet.proxy = new_proxy
    wallet.proxy_status = "OK"
    db.commit()
    return True


def replace_bad_twitter(id: int, new_token: str) -> bool:
    wallet = db.one(Wallet, Wallet.id == id)
    if not wallet:
        return False
    wallet.twitter_token = new_token
    wallet.twitter_status = "OK"
    db.commit()
    return True


def mark_proxy_as_bad(id: int) -> bool:
    wallet = db.one(Wallet, Wallet.id == id)
    if not wallet:
        return False
    wallet.proxy_status = "BAD"
    db.commit()
    return True


def mark_twitter_status(id: int, status: str) -> bool:
    wallet = db.one(Wallet, Wallet.id == id)
    if not wallet:
        return False
    wallet.twitter_status = status
    db.commit()
    return True


def get_wallets_with_bad_proxy() -> list:
    return db.all(Wallet, Wallet.proxy_status == "BAD")


def get_wallets_with_bad_twitter() -> list:
    return db.all(Wallet, Wallet.twitter_status == "BAD")


def twitter_creation_at(address: str, creation_at) -> bool:
    wallet = db.one(Wallet, Wallet.address == address)
    if not wallet:
        return False
    wallet.twitter_creation_at = creation_at
    db.commit()
    return True


def get_random_invite_code(id: int, quest: str) -> str | None:
    if not Settings().only_settings_invite_codes:
        if quest == "GCpict6X7N":
            invite_codes = Settings().first_quest_invite
            wallets = db.all(Wallet, Wallet.first_quest_invite.isnot(None), Wallet.id != id)
            if not wallets and not invite_codes:
                return None
            for wallet in wallets:
                invite_codes.append(wallet.first_quest_invite)
            return random.choice(invite_codes)
        elif quest == "GC5mTt8px6":
            invite_codes = Settings().second_quest_invite
            wallets = db.all(Wallet, Wallet.second_quest_invite.isnot(None), Wallet.id != id)
            if not wallets and not invite_codes:
                return None
            for wallet in wallets:
                invite_codes.append(wallet.second_quest_invite)
            return random.choice(invite_codes)
        else:
            invite_codes = Settings().third_quest_invite
            wallets = db.all(Wallet, Wallet.third_quest_invite.isnot(None), Wallet.id != id)
            if not wallets and not invite_codes:
                return None
            for wallet in wallets:
                invite_codes.append(wallet.third_quest_invite)
            return random.choice(invite_codes)

    else:
        if quest == "GCpict6X7N":
            if not Settings().first_quest_invite:
                return None
            return random.choice(Settings().first_quest_invite)
        elif quest == "GC5mTt8px6":
            if not Settings().second_quest_invite:
                return None
            return random.choice(Settings().second_quest_invite)
        else:
            if not Settings().third_quest_invite:
                return None
            return random.choice(Settings().third_quest_invite)


def update_ref_code(id: int, quest: str, ref_code: str) -> bool:
    wallet = db.one(Wallet, Wallet.id == id)
    if not wallet:
        return False
    if quest == "GCpict6X7N":
        wallet.first_quest_invite = ref_code
    elif quest == "GC5mTt8px6":
        wallet.second_quest_invite = ref_code
    else:
        wallet.third_quest_invite = ref_code
    db.commit()
    return True


db = DB(f"sqlite:///{WALLETS_DB}", echo=False, pool_recycle=3600, connect_args={"check_same_thread": False})
db.create_tables(Base)
