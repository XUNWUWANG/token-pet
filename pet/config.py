
"""配置管理 — 读取 .env 文件和环境变量。"""

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda: None  # noop fallback


@dataclass
class Config:
    deepseek_api_key: str = ""
    poll_interval_ms: int = 2000
    balance_interval_ms: int = 300000
    balance_limit: float = 20.0
    alpha: float = 0.92
    window_x: int | None = None
    window_y: int | None = None

    def is_balance_configured(self) -> bool:
        return bool(self.deepseek_api_key)


def load_config(env_path: str | Path | None = None) -> Config:
    """从 .env 和系统环境变量加载配置。"""
    load_dotenv(dotenv_path=env_path)

    return Config(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        poll_interval_ms=int(os.getenv("POLL_INTERVAL_MS", "2000")),
        balance_interval_ms=int(os.getenv("BALANCE_INTERVAL_MS", "300000")),
        balance_limit=float(os.getenv("BALANCE_LIMIT", "20.0")),
        alpha=float(os.getenv("ALPHA", "0.92")),
        window_x=_parse_int_or_none(os.getenv("WINDOW_X")),
        window_y=_parse_int_or_none(os.getenv("WINDOW_Y"))
    )


def _parse_int_or_none(v: str | None) -> int | None:
    if v is None or v.strip() == "":
        return None
    try:
        return int(v.strip())
    except ValueError:
        return None


def find_env_file() -> Path:
    """查找项目根目录的 .env 文件。"""
    search = [Path.cwd(), Path(__file__).resolve().parent.parent]
    for d in search:
        candidate = d / ".env"
        if candidate.exists():
            return candidate
    return search[0] / ".env"


def save_config_to_env(config: Config, env_path: str | Path) -> None:
    """将当前配置写回 .env 文件，实现持久化。"""
    path = Path(env_path)
    if not path.exists():
        return

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    mapping = {
        "DEEPSEEK_API_KEY": config.deepseek_api_key,
        "POLL_INTERVAL_MS": str(config.poll_interval_ms),
        "BALANCE_INTERVAL_MS": str(config.balance_interval_ms),
        "BALANCE_LIMIT": str(config.balance_limit),
        "ALPHA": str(config.alpha),
        "WINDOW_X": str(config.window_x) if config.window_x is not None else "",
        "WINDOW_Y": str(config.window_y) if config.window_y is not None else "",
    }

    updated = set()
    out = []
    for line in lines:
        s = line.strip()
        if "=" in s and not s.startswith("#"):
            k = s.split("=", 1)[0].strip()
            if k in mapping:
                out.append(f"{k}={mapping[k]}\n")
                updated.add(k)
                continue
        out.append(line)

    for k, v in mapping.items():
        if k not in updated and v:
            out.append(f"{k}={v}\n")

    path.write_text("".join(out), encoding="utf-8")

def set_autostart(enabled: bool) -> None:
    import shutil
    startup = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    lnk = os.path.join(startup, "TokenPet.lnk")
    if enabled:
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "TokenPet.lnk")
        if os.path.exists(src):
            shutil.copy2(src, lnk)
    else:
        if os.path.exists(lnk):
            os.remove(lnk)

def is_autostart_enabled() -> bool:
    sp = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    return os.path.exists(os.path.join(sp, "TokenPet.lnk"))
