from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class UsageState:
    # Codex 用量
    total_tokens: int = 0
    active_thread_count: int = 0
    latest_thread_title: str = ""
    latest_thread_tokens: int = 0
    last_poll_time: float = 0.0

    # DeepSeek 余额
    deepseek_balance: float = 0.0
    deepseek_total: float = 0.0
    deepseek_currency: str = ""
    deepseek_last_check: float = 0.0
    deepseek_limit: float = 20.0
    balance_configured: bool = False
    balance_error: str = ""

    # 计算字段
    balance_percent: int = 0
    emotion: str = "happy"

    _prev_total_tokens: int = field(default=0, repr=False)
    token_delta: int = 0

    def tick(self) -> None:
        # 余额百分比：已用量 / 上限
        if self.deepseek_limit > 0 and self.balance_configured:
            used = self.deepseek_limit - self.deepseek_balance
            used = max(0, used)
            self.balance_percent = min(100, int(used / self.deepseek_limit * 100))
        else:
            self.balance_percent = 0
        self.token_delta = self.total_tokens - self._prev_total_tokens
        self._prev_total_tokens = self.total_tokens
        self._calc_emotion()


    def get_emotion(self) -> tuple[str, str]:
        _emo = {"happy": ("\U0001f638","\u5f00\u5fc3"), "normal": ("\U0001f63a","\u5e73\u9759"), "worried": ("\U0001f63f","\u7126\u8651"), "alert": ("\U0001f640","\u5371\u9669")}
        return _emo.get(self.emotion, ("\U0001f63a", "\u5e73\u9759"))
    def _calc_emotion(self) -> None:
        p = self.balance_percent
        if p >= 85:
            self.emotion = "alert"
        elif p >= 60:
            self.emotion = "worried"
        elif p >= 25:
            self.emotion = "normal"
        else:
            self.emotion = "happy"

    @property
    def _currency_symbol(self) -> str:
        if self.deepseek_currency == "CNY":
            return "\u00a5"  # ¥
        if self.deepseek_currency == "USD":
            return "$"
        return "$"

    @property
    def balance_formatted(self) -> str:
        if not self.balance_configured:
            return "\u672a\u8bbe\u7f6e API Key"  # 未设置 API Key
        if self.balance_error:
            return "\u67e5\u8be2\u5931\u8d25"  # 查询失败
        sym = self._currency_symbol
        return f"{sym}{self.deepseek_balance:.2f}"

    @property
    def balance_detail(self) -> str:
        if not self.balance_configured or self.balance_error:
            return ""
        sym = self._currency_symbol
        return f"{sym}{self.deepseek_balance:.2f} / {sym}{self.deepseek_limit:.2f}"

    @property
    def tokens_formatted(self) -> str:
        if self.total_tokens >= 1_000_000:
            return f"{self.total_tokens / 1_000_000:.2f}M"
        if self.total_tokens >= 1_000:
            return f"{self.total_tokens / 1_000:.1f}K"
        return str(self.total_tokens)


    @property
    def sync_text(self) -> str:
        now = time.time()
        if self.last_poll_time == 0:
            return "\u7b49\u5f85\u6570\u636e..."  # 等待数据...
        token_secs = int(now - self.last_poll_time)
        if token_secs < 10:
            token_str = "\u521a\u521a"  # 刚刚
        elif token_secs < 60:
            token_str = f"{token_secs}\u79d2\u524d"  # X秒前
        else:
            token_str = f"{token_secs // 60}\u5206\u949f\u524d"  # X分钟前
        if self.balance_configured and self.deepseek_last_check > 0:
            bal_secs = int(now - self.deepseek_last_check)
            if bal_secs < 60:
                bal_str = "\u521a\u521a"
            else:
                bal_str = f"{bal_secs // 60}\u5206\u949f\u524d"
            return f"Token: {token_str}  \u4f59\u989d: {bal_str}"  # Token: XX 余额: XX
        return f"Token: {token_str}"

    @property
    def threads_info(self) -> str:
        """显示会话数量的辅助文本。"""
        return f"{self.active_thread_count} 个会话"
