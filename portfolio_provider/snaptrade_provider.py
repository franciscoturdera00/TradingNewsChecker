import os, json
from pathlib import Path
from snaptrade_client import SnapTrade, ApiException

USER_SECRET_FILE = Path("user_secret.json")

class SnapTradeProvider:
    def __init__(self):
        self.client_id = os.environ["SNAPTRADE_CLIENT_ID"]
        self.consumer_key = os.environ["SNAPTRADE_CONSUMER_KEY"]
        self.user_id = os.environ["SNAPTRADE_USER_ID"]

        self.snaptrade = SnapTrade(client_id=self.client_id, consumer_key=self.consumer_key)
        self.user_secret = os.getenv("SNAPTRADE_USER_SECRET")

        if not any([self.client_id, self.consumer_key, self.user_id, self.user_secret]):
            raise ValueError("SnapTrade environment variables are not set.")

    # ---------- data ----------
    def get_positions(self):
        accounts = self.snaptrade.account_information.list_user_accounts(
            user_id =  self.user_id, 
            user_secret= self.user_secret
        ).body

        if accounts is None or not isinstance(accounts, list):
            return []

        all_positions = []
        for acct in accounts:
            account_id = acct.get("id")
            if not account_id:
                continue
            pos = self.snaptrade.account_information.get_user_account_positions(
                account_id=account_id,
                user_id=self.user_id,
                user_secret=self.user_secret,
            ).body

            if pos is None or not isinstance(pos, list):
                continue
            # annotate with account id for traceability
            for p in pos:
                p["account_id"] = account_id # type: ignore | We are adding a key
            all_positions.extend(pos)
        return all_positions
