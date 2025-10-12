import robin_stocks.robinhood as r
import os
from dotenv import load_dotenv
from .base_provider import BaseProvider
import time

load_dotenv()

def _disable_trading():
    def deny(*_, **__):
        raise RuntimeError("Trading is disabled in this provider.")
    for name in dir(r):
        if name.startswith("order") or name in {"cancel_all_open_orders", "cancel_stock_order"}:
            try:
                setattr(r, name, deny)
            except Exception:
                pass

class RobinhoodProvider(BaseProvider):
    def __init__(self):
        self.login()

    def login(self):
        username = os.getenv("ROBINHOOD_USERNAME")
        password = os.getenv("ROBINHOOD_PASSWORD")
        if not username or not password:
            raise RuntimeError("Missing ROBINHOOD_USERNAME or ROBINHOOD_PASSWORD.")
        r.login(username=username, password=password, store_session=False, expiresIn=600)
        time.sleep(10)
        r.login(username=username, password=password, store_session=False, expiresIn=600)
        time.sleep(10)
        _disable_trading()

    def get_positions(self):
        try:
            return r.build_holdings()
        finally:
            # end session even if call succeeds/fails
            try:
                r.logout()
            except Exception:
                pass
