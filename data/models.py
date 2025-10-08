from dataclasses import dataclass

from data.settings import Settings
from libs.eth_async.classes import Singleton
from libs.eth_async.data.models import DefaultABIs, RawContract
from libs.exchanger.okx.models import OKXCredentials


class Contracts(Singleton):
    ETH = RawContract(title="ETH", address="0x0000000000000000000000000000000000000000", abi=DefaultABIs.Token)


settings = Settings()


@dataclass
class FromTo:
    from_: int | float
    to_: int | float


class OkxModel:
    required_minimum_balance: float
    withdraw_amount: FromTo
    delay_between_withdrawals: FromTo
    credentials: OKXCredentials


okx = OkxModel()
okx_credentials = OKXCredentials(api_key="", secret_key="", passphrase="")
