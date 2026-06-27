"""
绘制函数 — 从 app.py 抽取。
"""

WINDOW_W = 220
WINDOW_H = 280
BG_COLOR = "#1a1a2e"
TEXT_COLOR = "#e2e8f0"
BAR_BG = "#2d2d50"
COLOR_GREEN = "#10b981"
COLOR_AMBER = "#f59e0b"
COLOR_RED = "#ef4444"
FONT_FAMILY = "Segoe UI"


def draw(canvas, state, on_settings, on_refresh, on_exit):
    cw, ch = WINDOW_W, WINDOW_H
    cx = cw // 2
    canvas.delete("all")
    canvas.create_rectangle(0, 0, cw - 1, ch - 1, outline="#2d2d50", width=1)

    emoji, emotion_label = state.get_emotion()
    canvas.create_text(cx, 30, text=emoji, fill=TEXT_COLOR, font=(FONT_FAMILY, 32), anchor="center", tags="emoji")
    canvas.create_text(cx, 58, text=emotion_label, fill="#94a3b8", font=(FONT_FAMILY, 9), anchor="center")

    # token
    canvas.create_text(cx, 78, text="Token 总计", fill=TEXT_COLOR, font=(FONT_FAMILY, 10, "bold"), anchor="center")
    txt = f"{state.total_tokens:,}" if state.total_tokens >= 1000 else str(state.total_tokens)
    canvas.create_text(cx, 98, text=txt, fill=TEXT_COLOR, font=(FONT_FAMILY, 14, "bold"), anchor="center")
    if state.token_delta > 0:
        canvas.create_text(cx + 55, 98, text=f"+{state.token_delta}", fill=COLOR_GREEN, font=(FONT_FAMILY, 9), anchor="w")
    canvas.create_text(cx, 116, text=state.threads_info, fill="#94a3b8", font=(FONT_FAMILY, 9), anchor="center")

    # balance
    canvas.create_text(cx, 142, text="DeepSeek 已用", fill=TEXT_COLOR, font=(FONT_FAMILY, 10, "bold"), anchor="center")
    if state.balance_configured and not state.balance_error:
        _draw_bar(canvas, 20, 157, 180, 12, state.balance_percent, COLOR_AMBER)
        canvas.create_text(200, 163, text=f"{state.balance_percent}%", fill=TEXT_COLOR, font=(FONT_FAMILY, 8), anchor="e")
        used = max(0, state.deepseek_limit - state.deepseek_balance)
        sym = "¥" if state.deepseek_currency == "CNY" else "$"
        canvas.create_text(20, 163, text=f"{sym}{used:.2f}", fill="#94a3b8", font=(FONT_FAMILY, 8), anchor="w")
        canvas.create_text(cx, 179, text=state.balance_detail, fill=TEXT_COLOR, font=(FONT_FAMILY, 11, "bold"), anchor="center")
    elif state.balance_error:
        canvas.create_text(cx, 168, text="查询失败", fill=COLOR_RED, font=(FONT_FAMILY, 10), anchor="center")
        canvas.create_text(cx, 182, text=state.balance_error[:30], fill="#94a3b8", font=(FONT_FAMILY, 8), anchor="center")
    else:
        canvas.create_text(cx, 168, text="右键设置 API Key", fill="#94a3b8", font=(FONT_FAMILY, 9), anchor="center")

    canvas.create_line(10, 205, cw - 10, 205, fill="#2d2d50", width=1)
    canvas.create_text(cx, 220, text=state.sync_text, fill="#64748b", font=(FONT_FAMILY, 8), anchor="center")

    # buttons
    _draw_button(canvas, 30, 245, "⚙", on_settings, 1)
    _draw_button(canvas, cx, 245, "🔄", on_refresh, 2)
    _draw_button(canvas, cw - 30, 245, "✕", on_exit, 3)


def _draw_bar(canvas, x, y, w, h, percent, default_color):
    r = h // 2
    canvas.create_oval(x, y, x + 2 * r, y + h, fill=BAR_BG, outline="", tags="bar")
    canvas.create_oval(x + w - 2 * r, y, x + w, y + h, fill=BAR_BG, outline="", tags="bar")
    canvas.create_rectangle(x + r, y, x + w - r, y + h, fill=BAR_BG, outline="", tags="bar")
    fw = max(4, int(w * percent / 100))
    if percent > 0:
        color = COLOR_RED if percent >= 70 else (COLOR_AMBER if percent >= 40 else COLOR_GREEN)
        fr = min(r, h // 2)
        if fw >= 2 * fr:
            canvas.create_oval(x, y, x + 2 * fr, y + h, fill=color, outline="", tags="bar")
            canvas.create_oval(x + fw - 2 * fr, y, x + fw, y + h, fill=color, outline="", tags="bar")
            canvas.create_rectangle(x + fr, y, x + fw - fr, y + h, fill=color, outline="", tags="bar")
        else:
            canvas.create_oval(x, y, x + fw, y + h, fill=color, outline="", tags="bar")


def _draw_button(canvas, x, y, text, command, tag):
    btn = canvas.create_text(x, y, text=text, fill="#94a3b8", font=(FONT_FAMILY, 14), anchor="center", tags=f"btn_{tag}")
    canvas.tag_bind(f"btn_{tag}", "<Button-1>", lambda e: command())
    canvas.tag_bind(f"btn_{tag}", "<Enter>", lambda e: canvas.itemconfig(f"btn_{tag}", fill=TEXT_COLOR))
    canvas.tag_bind(f"btn_{tag}", "<Leave>", lambda e: canvas.itemconfig(f"btn_{tag}", fill="#94a3b8"))
