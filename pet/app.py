
"""桌宠主窗口\n\nimport logging\nimport os\n\n_log = logging.getLogger("tokenpet")\nlog_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")\nos.makedirs(log_dir, exist_ok=True)\nlogging.basicConfig(\n    filename=os.path.join(log_dir, "tokenpet.log"),\n    level=logging.WARNING,\n    format="%(asctime)s [%(levelname)s] %(message)s",\n)\n — tkinter 实现的无边框、置顶、半透明桌面宠物。"""

from __future__ import annotations

import math
import time
import tkinter as tk
from tkinter import Canvas, Menu, ttk

from .balance import BalanceCollector
from .collector import CodexCollector
from .config import Config, save_config_to_env, find_env_file, set_autostart, is_autostart_enabled
from .state import UsageState

# ── 窗口常量 ──────────────────────────────────────────────
WINDOW_W = 220
WINDOW_H = 280
BG_COLOR = "#1a1a2e"
TEXT_COLOR = "#e2e8f0"
ACCENT = "#6366f1"
BAR_BG = "#2d2d50"
COLOR_GREEN = "#10b981"
COLOR_AMBER = "#f59e0b"
COLOR_RED = "#ef4444"
FONT_FAMILY = "Segoe UI"


class PetWindow:
    """桌宠主窗口\n\nimport logging\nimport os\n\n_log = logging.getLogger("tokenpet")\nlog_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")\nos.makedirs(log_dir, exist_ok=True)\nlogging.basicConfig(\n    filename=os.path.join(log_dir, "tokenpet.log"),\n    level=logging.WARNING,\n    format="%(asctime)s [%(levelname)s] %(message)s",\n)\n。"""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.state = UsageState()
        self.collector = CodexCollector()
        self.balance_collector = BalanceCollector(config.deepseek_api_key)

        # 动画插值
        self._anim_token = 0.0
        self._anim_pct = 0.0
        self._anim_balance_pct = 0.0
        self._anim_balance = 0.0
        self._last_balance_fetch = 0.0

        # ── 创建窗口 ──
        self.root = tk.Tk()
        self.root.title("TokenPet")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-alpha", 0.92)
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        # 位置
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        if config.window_x is not None and config.window_y is not None:
            wx, wy = config.window_x, config.window_y
        else:
            wx, wy = sw - WINDOW_W - 20, sh - WINDOW_H - 60
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}+{wx}+{wy}")

        # Windows 圆角
        self._apply_rounded_corners()

        # ── Canvas ──
        self.canvas = Canvas(
            self.root,
            width=WINDOW_W,
            height=WINDOW_H,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # ── 交互绑定 ──
        self._drag_data = {"x": 0, "y": 0}
        for widget in (self.canvas, self.root):
            widget.bind("<Button-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_move)
            widget.bind("<Button-3>", self._show_menu)
            widget.bind("<Double-Button-1>", self._on_double_click)
            widget.bind("<ButtonRelease-1>", lambda e: self._save_position())

        # ── 右键菜单 ──
        self._build_menu()

        # ── 初始绘制 + 启动轮询 ──
        self._draw()
        self._poll()
        self._poll_balance()
        
        self.root.protocol("WM_DELETE_WINDOW", self._exit_app)

    # ── 窗口交互 ─────────────────────────────────────────

    def _apply_rounded_corners(self) -> None:
        try:
            import ctypes

            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            dwmapi = ctypes.windll.dwmapi
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass

    def _on_drag_start(self, event: tk.Event) -> None:
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_move(self, event: tk.Event) -> None:
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _save_position(self) -> None:
        self.config.window_x = self.root.winfo_x()
        self.config.window_y = self.root.winfo_y()
        self._flush_env()

    def _flush_env(self) -> None:
        env_path = find_env_file()
        if env_path.exists():
            save_config_to_env(self.config, str(env_path))

    def _on_double_click(self, event: tk.Event) -> None:
        """双击角色触发表情动画。"""
        self._flash_emotion()

    def _flash_emotion(self) -> None:
        """表情闪烁动画。"""
        emoji, _ = get_emotion(self.state.emotion)
        alt_emoji = {"😸": "😺", "😺": "😸", "😿": "😹", "🙀": "😹"}.get(emoji, "😺")

        def swap(e, count=0):
            self._draw_emoji(e)
            if count < 4:
                self.root.after(150, swap, alt_emoji if e == emoji else emoji, count + 1)

        swap(emoji)

    def _draw(self) -> None:
        from .renderer import draw as pet_draw
        pet_draw(self.canvas, self.state, self._open_settings, self._force_refresh, self._exit_app)

    def _show_menu(self, event: tk.Event) -> None:
        self.menu.tk_popup(event.x_root, event.y_root)

    def _build_menu(self) -> None:
        self.menu = Menu(self.root, tearoff=0, font=(FONT_FAMILY, 10))
        self.menu.add_command(label="🔄 刷新数据", command=self._force_refresh)
        self.menu.add_command(label="⚙  设置 API Key", command=self._open_settings)
        self.menu.add_separator()
        self.menu.add_command(label="❌ 退出", command=self._exit_app)

    def _force_refresh(self) -> None:
        self._do_collect()
        self._do_fetch_balance()
        self.state.tick()
        self._draw()

    def _open_settings(self) -> None:
        """弹出设置对话框。"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置")
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dx = (sw - 380) // 2
        dy = (sh - 370) // 2
        dialog.geometry(f"380x370+{dx}+{dy}")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg=BG_COLOR)

        frame = ttk.Frame(dialog, padding=16)
        frame.pack(fill="both", expand=True)

        # ── API Key ──
        ttk.Label(frame, text="DeepSeek API Key:").pack(anchor="w")
        key_var = tk.StringVar(value=self.config.deepseek_api_key)
        key_entry = ttk.Entry(frame, textvariable=key_var, width=42, show="*")
        key_entry.pack(fill="x", pady=(4, 6))

        show_var = tk.BooleanVar(value=False)
        def toggle_show():
            key_entry.configure(show="" if show_var.get() else "*")
        ttk.Checkbutton(frame, text="显示 Key", variable=show_var, command=toggle_show).pack(anchor="w")

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=10)

        # ── 轮询间隔（水平排列） ──
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(4, 2))
        ttk.Label(row1, text="Token 更新间隔:").pack(side="left")
        token_var = tk.IntVar(value=self.config.poll_interval_ms)
        ttk.Spinbox(row1, from_=500, to=10000, increment=500, textvariable=token_var, width=8).pack(side="right")
        ttk.Label(row1, text="毫秒", font=(FONT_FAMILY, 9)).pack(side="right", padx=(4, 0))

        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="余额更新间隔:").pack(side="left")
        bal_var = tk.IntVar(value=self.config.balance_interval_ms)
        ttk.Spinbox(row2, from_=10000, to=600000, increment=10000, textvariable=bal_var, width=8).pack(side="right")
        ttk.Label(row2, text="毫秒", font=(FONT_FAMILY, 9)).pack(side="right", padx=(4, 0))

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=6)

        # ── 窗口透明度 ──
        row_alpha = ttk.Frame(frame)
        row_alpha.pack(fill="x", pady=4)
        ttk.Label(row_alpha, text="窗口透明度:").pack(side="left")
        alpha_var = tk.DoubleVar(value=self.config.alpha)
        ttk.Spinbox(row_alpha, from_=0.3, to=1.0, increment=0.05, textvariable=alpha_var, width=8).pack(side="right")
        ttk.Label(row_alpha, text="(0.3-1.0)", font=(FONT_FAMILY, 9)).pack(side="right", padx=(4, 0))

        # ---- auto start ----
        row_startup = ttk.Frame(frame)
        row_startup.pack(fill="x", pady=6)
        startup_var = tk.BooleanVar(value=is_autostart_enabled())
        ttk.Checkbutton(row_startup, text="\u5f00\u673a\u81ea\u542f", variable=startup_var).pack(anchor="w")

        # ── 余额上限 ──
        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=4)
        ttk.Label(row3, text="余额上限:").pack(side="left")
        limit_var = tk.DoubleVar(value=self.config.balance_limit)
        ttk.Spinbox(row3, from_=5.0, to=100.0, increment=5.0, textvariable=limit_var, width=8).pack(side="right")
        ttk.Label(row3, text=self.state._currency_symbol, font=(FONT_FAMILY, 9)).pack(side="right", padx=(4, 0))

        # ── 保存/取消 ──
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(14, 0))

        def save():
            self.config.deepseek_api_key = key_var.get().strip()
            self.balance_collector = BalanceCollector(self.config.deepseek_api_key)
            self.state.balance_configured = bool(self.config.deepseek_api_key)

            self.config.poll_interval_ms = token_var.get()
            self.config.balance_interval_ms = bal_var.get()
            self.config.balance_limit = limit_var.get()
            self.state.deepseek_limit = limit_var.get()

            alpha = max(0.3, min(1.0, alpha_var.get()))
            self.root.wm_attributes("-alpha", alpha)
            self.config.alpha = alpha

            self.config.window_x = self.root.winfo_x()
            self.config.window_y = self.root.winfo_y()

            set_autostart(startup_var.get())

            env_path = find_env_file()
            if env_path.exists():
                save_config_to_env(self.config, str(env_path))

            dialog.destroy()
            self._force_refresh()

        ttk.Button(btn_frame, text="保存", command=save).pack(side="right", padx=(8, 0))
        ttk.Button(btn_frame, text="取消", command=lambda: self._close_dialog(dialog)).pack(side="right")

    def _close_dialog(self, dialog: tk.Toplevel) -> None:
        dialog.destroy()

    def _exit_app(self) -> None:
        self._save_position()
        self.root.quit()
        self.root.destroy()

    # ── 数据采集 ─────────────────────────────────────────

    def _poll(self) -> None:
        """定时轮询 Codex 数据库。"""
        self._do_collect()
        self.state.tick()
        self._draw()
        self.root.after(self.config.poll_interval_ms, self._poll)

    def _do_collect(self) -> None:
        result = self.collector.collect()
        if not result.error:
            self.state.total_tokens = result.total_tokens
            self.state.active_thread_count = result.active_thread_count
            self.state.latest_thread_title = result.latest_thread_title
            self.state.latest_thread_tokens = result.latest_thread_tokens
            self.state.last_poll_time = time.time()
            self.state.balance_configured = self.config.is_balance_configured()

    def _poll_balance(self) -> None:
        """定时查询 DeepSeek 余额。"""
        if self.config.is_balance_configured():
            self._do_fetch_balance()
        self.root.after(self.config.balance_interval_ms, self._poll_balance)

    def _do_fetch_balance(self) -> None:
        if not self.config.is_balance_configured():
            self.state.balance_configured = False
            return

        result = self.balance_collector.fetch()
        self.state.deepseek_balance = result.balance
        self.state.deepseek_total = result.total
        self.state.deepseek_currency = result.currency
        self.state.deepseek_limit = self.config.balance_limit
        self.state.deepseek_last_check = result.fetched_at
        self.state.balance_configured = True
        self.state.balance_error = result.error

    # ── 绘制 ─────────────────────────────────────────────

    def run(self) -> None:
        """启动桌宠事件循环。"""
        self.root.mainloop()
