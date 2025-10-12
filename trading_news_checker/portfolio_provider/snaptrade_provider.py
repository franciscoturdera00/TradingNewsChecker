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
        self.user_secret = self._get_or_create_secret()

    # ---------- secret mgmt ----------
    def _get_or_create_secret(self) -> str:
        s = self._load_secret()
        if s:
            return s
        try:
            resp = self.snaptrade.authentication.register_snap_trade_user(body={"userId": self.user_id})
            secret = (resp.body or {}).get("userSecret")
            if not secret:
                raise RuntimeError("No userSecret in register response")
            self._save_secret(secret)
            return secret
        except ApiException as e:
            if getattr(e, "status", None) == 400:  # user exists → rotate to get a secret
                resp = self.snaptrade.authentication.reset_snap_trade_user_secret(
                    user_id= self.user_id
                )
                secret = (resp.body or {}).get("userSecret")
                if not secret:
                    raise RuntimeError("No userSecret in reset response")
                self._save_secret(secret)
                return secret
            raise

    def _load_secret(self):
        try:
            return json.loads(USER_SECRET_FILE.read_text())["user_secret"]
        except FileNotFoundError:
            return None

    def _save_secret(self, secret: str):
        USER_SECRET_FILE.write_text(json.dumps({"user_secret": secret}))

    # ---------- data ----------
    def get_positions(self):
        accounts = self.snaptrade.account_information.list_user_accounts(
            user_id =  self.user_id, 
            user_secret= self.user_secret
        ).body or []

        all_positions = []
        for acct in accounts:
            account_id = acct.get("id")
            if not account_id:
                continue
            pos = self.snaptrade.account_information.get_user_account_positions(
                account_id=account_id,
                user_id=self.user_id,
                user_secret=self.user_secret,
            ).body or []
            # annotate with account id for traceability
            for p in pos:
                p["account_id"] = account_id
            all_positions.extend(pos)
        return all_positions
