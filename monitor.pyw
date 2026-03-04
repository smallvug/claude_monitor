"""
Claude Code 사용량 트레이 모니터
- api.anthropic.com/api/oauth/usage 에서 사용량 조회
- 트레이 아이콘에 5시간 / 7일 사용률 표시
"""
import json
import os
import sys
import threading
import time
import requests
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont
import pystray

# ── 설정 ──────────────────────────────────────────────────────────────────────
CREDS_PATH = os.path.join(os.environ["USERPROFILE"], ".claude", ".credentials.json")
API_URL = "https://api.anthropic.com/api/oauth/usage"
PROFILE_URL = "https://api.anthropic.com/api/oauth/profile"
REFRESH_URL = "https://platform.claude.com/v1/oauth/token"
CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
OAUTH_SCOPE = "user:profile user:inference user:sessions:claude_code user:mcp_servers"
REFRESH_INTERVAL = 60  # 기본값 (초)
_refresh_interval = [REFRESH_INTERVAL]  # 런타임 변경 가능

# 실제 Windows 트레이 아이콘 크기 (DPI 반영)
def _get_tray_icon_size():
    try:
        import ctypes
        # SM_CXSMICON=49, SM_CYSMICON=50
        w = ctypes.windll.user32.GetSystemMetrics(49)
        return w if w > 0 else 32
    except Exception:
        return 32

ICON_SIZE = _get_tray_icon_size() * 2   # 2x 오버샘플 후 다운샘플

# ── 상태 ──────────────────────────────────────────────────────────────────────
state = {
    "five_hour": None,
    "seven_day": None,
    "seven_day_sonnet": None,
    "extra_usage": None,
    "error": None,
    "last_update": None,
}


def load_credentials():
    with open(CREDS_PATH, encoding="utf-8") as f:
        return json.load(f)["claudeAiOauth"]


def save_credentials(data):
    with open(CREDS_PATH, encoding="utf-8") as f:
        full = json.load(f)
    full["claudeAiOauth"].update(data)
    with open(CREDS_PATH, "w", encoding="utf-8") as f:
        json.dump(full, f, indent=2)


def get_token():
    """액세스 토큰 반환 (만료 시 갱신)"""
    creds = load_credentials()
    expires_at = creds.get("expiresAt", 0) / 1000
    # 5분 여유를 두고 갱신
    if time.time() > expires_at - 300:
        try:
            r = requests.post(REFRESH_URL, json={
                "grant_type": "refresh_token",
                "refresh_token": creds["refreshToken"],
                "client_id": CLIENT_ID,
                "scope": OAUTH_SCOPE,
            }, timeout=10)
            if r.status_code == 200:
                new_data = r.json()
                # API 응답 키를 credentials.json 형식으로 매핑
                save_credentials({
                    "accessToken": new_data["access_token"],
                    "refreshToken": new_data.get("refresh_token", creds["refreshToken"]),
                    "expiresAt": int((time.time() + new_data["expires_in"]) * 1000),
                })
                return new_data["access_token"]
        except Exception:
            pass
    return creds["accessToken"]


def fetch_usage():
    """사용량 데이터 가져오기"""
    try:
        token = get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "anthropic-beta": "oauth-2025-04-20",
        }
        r = requests.get(API_URL, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        state["five_hour"] = data.get("five_hour")
        state["seven_day"] = data.get("seven_day")
        state["seven_day_sonnet"] = data.get("seven_day_sonnet")
        state["extra_usage"] = data.get("extra_usage")
        state["error"] = None
        state["last_update"] = datetime.now()
        return True
    except Exception as e:
        state["error"] = str(e)
        return False


def util_pct(window):
    """utilization 값을 정수% 반환. None이면 0"""
    if window and window.get("utilization") is not None:
        return int(window["utilization"])
    return 0


def resets_in(window):
    """남은 리셋 시간 문자열 (예: '2h30m')"""
    if not window or not window.get("resets_at"):
        return ""
    try:
        resets_at = datetime.fromisoformat(window["resets_at"])
        now = datetime.now(timezone.utc)
        delta = resets_at - now
        total_sec = int(delta.total_seconds())
        if total_sec <= 0:
            return "리셋됨"
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        if h > 0:
            return f"{h}h{m:02d}m"
        return f"{m}m"
    except Exception:
        return ""


def bg_color(pct, dim=False):
    """사용률에 따른 배경 색 (신호등)"""
    if pct < 50:
        base = (39, 174, 96)    # 초록
    elif pct < 80:
        base = (230, 150, 0)    # 주황
    else:
        base = (200, 40, 40)    # 빨강
    if dim:
        return tuple(int(c * 0.6) for c in base)
    return base


def make_icon(five_pct, seven_pct):
    """세션 숫자를 전체 크기로, 배경색 = 주간 상태"""
    S = ICON_SIZE  # 2x 오버샘플 크기
    img = Image.new("RGB", (S, S), bg_color(seven_pct))
    draw = ImageDraw.Draw(img)

    # 세션이 위험하면 테두리로 경고
    if five_pct >= 80:
        draw.rectangle([0, 0, S - 1, S - 1], outline=(255, 60, 60), width=max(2, S // 16))

    font_size = max(8, int(S * 0.75))
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    # 세션 % 숫자 (흰색, 가운데)
    draw.text((S // 2, S // 2), str(five_pct),
              fill=(255, 255, 255), font=font, anchor="mm")

    # 2x → 1x 다운샘플
    final_size = S // 2
    return img.resize((final_size, final_size), Image.LANCZOS)


def get_tooltip():
    """툴팁 텍스트 생성"""
    if state["error"]:
        return f"Claude Monitor - 오류: {state['error'][:50]}"

    lines = ["Claude Code 사용량"]

    if state["five_hour"]:
        pct = util_pct(state["five_hour"])
        reset = resets_in(state["five_hour"])
        lines.append(f"5시간: {pct}% (리셋 {reset})")

    if state["seven_day"]:
        pct = util_pct(state["seven_day"])
        reset = resets_in(state["seven_day"])
        lines.append(f"7일: {pct}% (리셋 {reset})")

    if state["seven_day_sonnet"]:
        pct = util_pct(state["seven_day_sonnet"])
        lines.append(f"Sonnet 7일: {pct}%")

    extra = state.get("extra_usage")
    if extra and extra.get("is_enabled"):
        used = extra.get("used_credits")
        limit = extra.get("monthly_limit")
        if used is not None and limit:
            lines.append(f"추가 사용: ${used:.2f} / ${limit:.2f}")

    if state["last_update"]:
        lines.append(f"갱신: {state['last_update'].strftime('%H:%M')}")

    return "\n".join(lines)


def update_loop(icon):
    """백그라운드 갱신 루프"""
    while True:
        fetch_usage()
        five_pct = util_pct(state["five_hour"])
        seven_pct = util_pct(state["seven_day"])

        icon.icon = make_icon(five_pct, seven_pct)
        icon.title = get_tooltip()
        time.sleep(_refresh_interval[0])


def on_refresh(icon, item):
    fetch_usage()
    five_pct = util_pct(state["five_hour"])
    seven_pct = util_pct(state["seven_day"])
    icon.icon = make_icon(five_pct, seven_pct)
    icon.title = get_tooltip()


def is_startup_enabled():
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "ClaudeMonitor")
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False


def on_toggle_startup(icon, item):
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    script = os.path.abspath(__file__)
    cmd = f'"{pythonw}" "{script}"'

    if is_startup_enabled():
        winreg.DeleteValue(key, "ClaudeMonitor")
    else:
        winreg.SetValueEx(key, "ClaudeMonitor", 0, winreg.REG_SZ, cmd)
    winreg.CloseKey(key)


def on_quit(icon, item):
    icon.stop()


def set_interval(seconds):
    def _handler(icon, item):
        _refresh_interval[0] = seconds
    return _handler


# ── 상세 팝업 ──────────────────────────────────────────────────────────────────
_popup_open = [False]


def show_popup(icon=None, item=None):
    if _popup_open[0]:
        return

    def _run():
        _popup_open[0] = True
        try:
            import tkinter as tk

            BG = "#1e1e1e"
            FG = "#ffffff"
            FG2 = "#aaaaaa"
            FG3 = "#666666"

            root = tk.Tk()
            root.title("Claude Code 사용량")
            root.resizable(False, False)
            root.attributes("-topmost", True)
            root.configure(bg=BG)

            pad = tk.Frame(root, bg=BG, padx=18, pady=14)
            pad.pack()

            tk.Label(pad, text="Claude Code 사용량", bg=BG, fg=FG,
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 12))

            def add_row(label, pct, reset_str):
                color = "#%02x%02x%02x" % bg_color(pct)
                tk.Label(pad, text=label, bg=BG, fg=FG2,
                         font=("Segoe UI", 9)).pack(anchor="w")
                row = tk.Frame(pad, bg=BG)
                row.pack(fill="x", pady=(3, 10))
                # 프로그레스 바
                canvas = tk.Canvas(row, width=220, height=16,
                                   bg="#333333", highlightthickness=0, bd=0)
                canvas.pack(side="left")
                bar_w = max(1, int(220 * pct / 100)) if pct > 0 else 0
                if bar_w:
                    canvas.create_rectangle(0, 0, bar_w, 16, fill=color, outline="")
                tk.Label(row, text=f"  {pct}%", bg=BG, fg=FG,
                         font=("Segoe UI", 10, "bold"), width=5, anchor="w").pack(side="left")
                if reset_str:
                    tk.Label(row, text=f"리셋 {reset_str}", bg=BG, fg=FG2,
                             font=("Segoe UI", 9)).pack(side="left")

            add_row("세션 (5시간)", util_pct(state["five_hour"]), resets_in(state["five_hour"]))
            add_row("주간 (7일)", util_pct(state["seven_day"]), resets_in(state["seven_day"]))
            if state["seven_day_sonnet"]:
                add_row("Sonnet 주간", util_pct(state["seven_day_sonnet"]),
                        resets_in(state["seven_day_sonnet"]))

            extra = state.get("extra_usage")
            if extra and extra.get("is_enabled"):
                used = extra.get("used_credits", 0)
                limit = extra.get("monthly_limit", 1)
                tk.Label(pad, text=f"추가 사용: ${used:.2f} / ${limit:.2f}",
                         bg=BG, fg=FG2, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 10))

            if state["error"]:
                tk.Label(pad, text=f"오류: {state['error'][:60]}", bg=BG, fg="#ff6666",
                         font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 6))

            if state["last_update"]:
                tk.Label(pad, text=f"갱신: {state['last_update'].strftime('%H:%M:%S')}",
                         bg=BG, fg=FG3, font=("Segoe UI", 8)).pack(anchor="w")

            root.protocol("WM_DELETE_WINDOW", root.destroy)
            root.bind("<Escape>", lambda e: root.destroy())

            # 화면 중앙 배치
            root.update_idletasks()
            w, h = root.winfo_width(), root.winfo_height()
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

            root.mainloop()
        finally:
            _popup_open[0] = False

    threading.Thread(target=_run, daemon=True).start()


def main():
    # 초기 데이터 로드
    fetch_usage()
    five_pct = util_pct(state["five_hour"])
    seven_pct = util_pct(state["seven_day"])

    initial_icon = make_icon(five_pct, seven_pct)
    tooltip = get_tooltip()

    menu = pystray.Menu(
        pystray.MenuItem("상세 보기", show_popup, default=True),
        pystray.MenuItem("지금 갱신", on_refresh),
        pystray.MenuItem(
            "갱신 주기",
            pystray.Menu(
                pystray.MenuItem("30초", set_interval(30),
                                 checked=lambda item: _refresh_interval[0] == 30, radio=True),
                pystray.MenuItem("1분", set_interval(60),
                                 checked=lambda item: _refresh_interval[0] == 60, radio=True),
                pystray.MenuItem("5분", set_interval(300),
                                 checked=lambda item: _refresh_interval[0] == 300, radio=True),
            ),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "시작 프로그램 등록",
            on_toggle_startup,
            checked=lambda item: is_startup_enabled(),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("종료", on_quit),
    )

    icon = pystray.Icon(
        name="claude_monitor",
        icon=initial_icon,
        title=tooltip,
        menu=menu,
    )

    # 백그라운드 갱신 스레드
    t = threading.Thread(target=update_loop, args=(icon,), daemon=True)
    t.start()

    icon.run()


if __name__ == "__main__":
    main()
