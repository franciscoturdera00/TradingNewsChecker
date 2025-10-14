import os, json
from pathlib import Path
from snaptrade_client import SnapTrade, ApiException
from logging_config import get_logger

USER_SECRET_FILE = Path("user_secret.json")

logger = get_logger(__name__)


class SnapTradeProvider:
    def __init__(self):
        try:
            self.client_id = os.environ["SNAPTRADE_CLIENT_ID"]
            self.consumer_key = os.environ["SNAPTRADE_CONSUMER_KEY"]
            self.user_id = os.environ["SNAPTRADE_USER_ID"]

            self.snaptrade = SnapTrade(client_id=self.client_id, consumer_key=self.consumer_key)
            self.user_secret = os.getenv("SNAPTRADE_USER_SECRET")

            if not any([self.client_id, self.consumer_key, self.user_id, self.user_secret]):
                raise ValueError("SnapTrade environment variables are not set.")
        except Exception:
            logger.exception("Failed to initialize SnapTradeProvider")
            raise

    # ---------- data ----------
    def get_positions(self):
        try:
            accounts_resp = self.snaptrade.account_information.list_user_accounts(
                user_id=self.user_id,
                user_secret=self.user_secret,
            )
            accounts = getattr(accounts_resp, "body", None)

            if accounts is None or not isinstance(accounts, list):
                logger.warning("No accounts returned from SnapTrade for user_id=%s", self.user_id)
                return []

            all_positions = []
            for acct in accounts:
                account_id = acct.get("id")
                if not account_id:
                    continue
                pos_resp = self.snaptrade.account_information.get_user_account_positions(
                    account_id=account_id,
                    user_id=self.user_id,
                    user_secret=self.user_secret,
                )
                pos = getattr(pos_resp, "body", None)

                if pos is None or not isinstance(pos, list):
                    logger.debug("No positions for account %s", account_id)
                    continue
                # annotate with account id for traceability
                for p in pos:
                    p["account_id"] = account_id  # type: ignore | We are adding a key
                all_positions.extend(pos)

            logger.info("Retrieved total positions: %d", len(all_positions))
            return all_positions
        except ApiException as e:
            logger.exception("SnapTrade API exception while fetching positions: %s", e)
            return []
        except Exception:
            logger.exception("Unexpected error while fetching SnapTrade positions")
            return []
