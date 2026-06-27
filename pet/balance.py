import json, time, urllib.request, urllib.error
from dataclasses import dataclass

BALANCE_URL = "https://api.deepseek.com/user/balance"

@dataclass
class BalanceResult:
    balance: float
    total: float
    currency: str
    fetched_at: float
    error: str = ""

class BalanceCollector:
    def __init__(self, api_key: str):
        self._api_key = api_key
        self._last = None

    def fetch(self) -> BalanceResult:
        if not self._api_key:
            return BalanceResult(0.0, 0.0, "", time.time(), error="API Key 未配置")
        try:
            req = urllib.request.Request(
                BALANCE_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            infos = data.get("balance_infos", [])
            if infos:
                info = infos[0]
                balance = float(info.get("total_balance", 0))
                topped_up = float(info.get("topped_up_balance", 0))
                total = topped_up if topped_up > 0 else balance
                currency = info.get("currency", "")
            else:
                balance = float(data.get("balance", 0))
                total = float(data.get("total", 0))
                currency = "USD"
            result = BalanceResult(balance=balance, total=total, currency=currency, fetched_at=time.time())
            self._last = result
            return result
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            self._last = None
            return BalanceResult(0.0, 0.0, "", time.time(), error=f"HTTP {e.code}: {body[:200]}")
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            self._last = None
            return BalanceResult(0.0, 0.0, "", time.time(), error=str(e))
