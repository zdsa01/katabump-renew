#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import subprocess
import requests
from seleniumbase import SB

# ==========================================
# 从环境变量获取账号密码和 TG 配置
# ==========================================

# 1. 财务面板 (Dashboard) 账号密码
EMAIL        = os.environ.get("KATABUMP_EMAIL") or ""    
PASSWORD     = os.environ.get("KATABUMP_PASSWORD") or "" 

# ==========================================
# 控制面板 (Control Panel) 独立身份凭证池
# 严格剥离主站邮箱依赖，实现凭证隔离
# ==========================================
CONTROL_ID       = os.environ.get("CONTROL_ID") or ""       # 强制仅使用独立的 CONTROL_ID (面板用户名)
CONTROL_PASSWORD = os.environ.get("CONTROL_PASSWORD") or PASSWORD # 智能降级：若未独立配置面板密码，默认复用主站 PASSWORD

# 3. TG 推送配置
TG_CHAT_ID   = os.environ.get("TG_CHAT_ID") or ""        
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") or ""      

BASE_URL = "https://dashboard.katabump.com"  
CONTROL_URL = "https://control.katabump.com/server/3c771e38" 

#  Telegram 推送模块（支持带截图发送）
def send_tg_message(status_icon, status_text, time_left="", image_path=None, target_email=EMAIL):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("ℹ️ 未配置 TG_BOT_TOKEN 或 TG_CHAT_ID，跳过 Telegram 推送。")
        return

    local_time = time.gmtime(time.time() + 8 * 3600)
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", local_time)

    if target_email and '@' in target_email:
        name, domain = target_email.split('@', 1)
        if len(name) > 4:
            masked_email = f"{name[:2]}****{name[-2:]}@{domain}"
        else:
            masked_email = f"{name}@{domain}"
    else:
        masked_email = target_email[:2] + '****' if target_email and len(target_email) >= 2 else target_email

    text = (
        f"🇫🇷 katabump 通知\n\n"
        f"{status_icon} {status_text}\n"
        f"👤 账户: {masked_email}\n"
        f"⏱️ 时间: {current_time_str}"
    )
    if time_left:
        text += f"\nℹ️ 详细说明: {time_left}"

    if image_path and os.path.exists(image_path):
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
        try:
            with open(image_path, "rb") as f:
                r = requests.post(
                    url,
                    data={"chat_id": TG_CHAT_ID, "caption": text},
                    files={"photo": f},
                    timeout=15
                )
            if r.status_code == 200:
                print(f"📩 Telegram 带图通知发送成功！({image_path})")
                return
            else:
                print(f"⚠️ Telegram 带图发送失败: {r.text}，回退为纯文字发送...")
        except Exception as e:
            print(f"⚠️ Telegram 带图发送异常: {e}，回退为纯文字发送...")

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("📩 Telegram 文字通知发送成功！")
        else:
            print(f"⚠️ Telegram 通知发送失败: {r.text}")
    except Exception as e:
        print(f"⚠️ Telegram 通知发送异常: {e}")

_EXPAND_JS = """
(function() {
    var ts = document.querySelector('input[name="cf-turnstile-response"]');
    if (!ts) return 'no-turnstile';
    var el = ts;
    for (var i = 0; i < 20; i++) {
        el = el.parentElement;
        if (!el) break;
        var s = window.getComputedStyle(el);
        if (s.overflow === 'hidden' || s.overflowX === 'hidden' || s.overflowY === 'hidden')
            el.style.overflow = 'visible';
        el.style.minWidth = 'max-content';
    }
    document.querySelectorAll('iframe').forEach(function(f){
        if (f.src && f.src.includes('challenges.cloudflare.com')) {
            f.style.width = '300px'; f.style.height = '65px';
            f.style.minWidth = '300px';
            f.style.visibility = 'visible'; f.style.opacity = '1';
        }
    });
    return 'done';
})()
"""

_EXISTS_JS = """
(function(){
    return document.querySelector('input[name="cf-turnstile-response"]') !== null;
})()
"""

_SOLVED_JS = """
(function(){
    var i = document.querySelector('input[name="cf-turnstile-response"]');
    return !!(i && i.value && i.value.length > 20);
})()
"""

_WININFO_JS = """
(function(){
    return {
        sx: window.screenX || 0,
        sy: window.screenY || 0,
        oh: window.outerHeight,
        ih: window.innerHeight
    };
})()
"""

_ALTCHA_EXPAND_JS = """
(function() {
    var modal = document.querySelector('div.modal.show') || document;
    var iframes = modal.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {
        var r = iframes[i].getBoundingClientRect();
        if (r.width > 0 && r.height > 0) {
            iframes[i].style.width  = '300px';
            iframes[i].style.height = '150px';
            iframes[i].style.minWidth  = '300px';
            iframes[i].style.minHeight = '150px';
            iframes[i].style.visibility = 'visible';
            iframes[i].style.opacity = '1';
            var el = iframes[i];
            for (var j = 0; j < 10; j++) {
                el = el.parentElement;
                if (!el) break;
                el.style.overflow = 'visible';
            }
            var r2 = iframes[i].getBoundingClientRect();
            return { cx: Math.round(r2.x + 30), cy: Math.round(r2.y + r2.height / 2) };
        }
    }
    return null;
})()
"""

_ALTCHA_SOLVED_JS = """
(function(){
    var modal = document.querySelector('div.modal.show') || document;
    var inputs = modal.querySelectorAll('input[type="hidden"]');
    for (var i = 0; i < inputs.length; i++) {
        var n = (inputs[i].name || '').toLowerCase();
        if ((n.includes('altcha') || n.includes('captcha')) &&
            inputs[i].value && inputs[i].value.length > 20) return true;
    }
    var cbs = modal.querySelectorAll('input[type="checkbox"]');
    for (var j = 0; j < cbs.length; j++) {
        if (cbs[j].disabled) return true;
    }
    var w = modal.querySelector('[data-state="verified"],.altcha--verified,.altcha-verified');
    if (w) return true;
    return false;
})()
"""

def js_fill_input(sb, selector: str, text: str):
    safe_text = text.replace('\\', '\\\\').replace('"', '\\"')
    sb.execute_script(f"""
    (function(){{
        var el = document.querySelector('{selector}');
        if (!el) return;
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        if (nativeInputValueSetter) {{
            nativeInputValueSetter.call(el, "{safe_text}");
        }} else {{
            el.value = "{safe_text}";
        }}
        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    }})()
    """)

def _activate_window():
    for cls in ["chrome", "chromium", "Chromium", "Chrome", "google-chrome"]:
        try:
            r = subprocess.run(["xdotool", "search", "--onlyvisible", "--class", cls], capture_output=True, text=True, timeout=3)
            wids = [w for w in r.stdout.strip().split("\n") if w.strip()]
            if wids:
                subprocess.run(["xdotool", "windowactivate", "--sync", wids[0]], timeout=3, stderr=subprocess.DEVNULL)
                time.sleep(0.2)
                return
        except Exception:
            pass
    try:
        subprocess.run(["xdotool", "getactivewindow", "windowactivate"], timeout=3, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def _xdotool_click(x: int, y: int):
    _activate_window()
    try:
        subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)], timeout=3, stderr=subprocess.DEVNULL)
        time.sleep(0.15)
        subprocess.run(["xdotool", "click", "1"], timeout=2, stderr=subprocess.DEVNULL)
    except Exception:
        os.system(f"xdotool mousemove {x} {y} click 1 2>/dev/null")

def handle_turnstile(sb) -> bool:
    """More robust Cloudflare Turnstile solver."""
    print("🔍 处理 Cloudflare Turnstile 验证...")
    time.sleep(2)

    # Already solved?
    if sb.execute_script(_SOLVED_JS):
        print("✅ Turnstile 已自动通过")
        return True

    # Force the widget visible / expand overflow
    for _ in range(4):
        try:
            sb.execute_script(_EXPAND_JS)
        except Exception:
            pass
        time.sleep(0.4)

    # Try SeleniumBase UC click first
    for attempt in range(5):
        if sb.execute_script(_SOLVED_JS):
            print("✅ Turnstile 已解决")
            return True

        print(f"  → 第 {attempt+1} 次尝试点击验证框...")
        try:
            sb.uc_gui_click_captcha()
        except Exception as e:
            print(f"    uc_gui_click_captcha 异常: {e}")

        # Also try direct coordinate click as fallback
        try:
            # Find the checkbox area
            rect = sb.execute_script("""
                (function(){
                    var iframe = document.querySelector('iframe[src*="challenges.cloudflare.com"]');
                    if (!iframe) return null;
                    var r = iframe.getBoundingClientRect();
                    return {x: Math.round(r.x + 30), y: Math.round(r.y + r.height/2)};
                })()
            """)
            if rect:
                wi = sb.execute_script(_WININFO_JS)
                _xdotool_click(rect["x"] + wi["sx"],
                               rect["y"] + wi["sy"] + (wi["oh"] - wi["ih"]))
        except Exception:
            pass

        # Poll for token
        for _ in range(12):
            time.sleep(0.6)
            if sb.execute_script(_SOLVED_JS):
                print("✅ Turnstile 已解决")
                return True

    print("❌ Turnstile 未能在限定时间内解决")
    return False


def login(sb) -> bool:
    print(f"🌐 打开登录页面: {BASE_URL}/auth/login")
    sb.uc_open_with_reconnect(BASE_URL + "/auth/login", reconnect_time=10)
    time.sleep(5)

    # Wait until the real login form appears (email input)
    form_ready = False
    for i in range(35):
        try:
            if sb.is_element_present('input[name="email"]') or \
               sb.is_element_present('input[type="email"]'):
                form_ready = True
                break
        except Exception:
            pass
        time.sleep(1)

    if not form_ready:
        sb.save_screenshot("login_load_fail.png")
        send_tg_message("❌", "登录失败", "页面未加载出登录表单", "login_load_fail.png", EMAIL)
        return False

    # Dismiss cookie banner if present
    try:
        for btn in sb.find_elements("button"):
            txt = (btn.text or "").lower()
            if "accept" in txt or "同意" in txt or "accept all" in txt:
                btn.click()
                time.sleep(0.5)
                break
    except Exception:
        pass

    print("📧 填写邮箱与密码...")
    # Prefer name=email, fall back to type=email
    email_sel = 'input[name="email"]'
    if not sb.is_element_present(email_sel):
        email_sel = 'input[type="email"]'
    js_fill_input(sb, email_sel, EMAIL)

    pass_sel = 'input[name="password"]'
    if not sb.is_element_present(pass_sel):
        pass_sel = 'input[type="password"]'
    js_fill_input(sb, pass_sel, PASSWORD)
    time.sleep(1.2)

    # Handle Turnstile if the widget exists
    if sb.execute_script(_EXISTS_JS):
        if not handle_turnstile(sb):
            sb.save_screenshot("login_failed.png")
            send_tg_message("❌", "登录失败", "Turnstile 验证未通过", "login_failed.png", EMAIL)
            return False
    else:
        print("ℹ️ 未检测到 Turnstile 控件，直接提交")

    # Extra safety: make sure token is present before submit
    for _ in range(8):
        if sb.execute_script(_SOLVED_JS):
            break
        time.sleep(0.5)

    # Submit
    try:
        # Prefer clicking the Login button
        login_btn = None
        for btn in sb.find_elements("button"):
            if "login" in (btn.text or "").lower() or "登录" in (btn.text or ""):
                login_btn = btn
                break
        if login_btn:
            login_btn.click()
        else:
            sb.press_keys(pass_sel, "\n")
    except Exception:
        sb.press_keys(pass_sel, "\n")

    print("⏳ 等待跳转...")
    for _ in range(18):
        time.sleep(1)
        cur = sb.get_current_url().split("?")[0].lower()
        title = (sb.get_title() or "").lower()
        if "dashboard" in cur or "dashboard" in title or "/servers" in cur:
            print("✅ 登录成功！")
            return True

        # Detect explicit captcha error again
        try:
            page = sb.get_page_source().lower()
            if "please complete captcha" in page or "complete the captcha" in page:
                print("⚠️ 页面仍提示需要完成验证码，尝试再次处理...")
                handle_turnstile(sb)
                # re-submit once
                try:
                    sb.press_keys(pass_sel, "\n")
                except Exception:
                    pass
        except Exception:
            pass

    sb.save_screenshot("login_failed.png")
    send_tg_message("❌", "登录失败", "跳转失败 / 仍停留在登录页", "login_failed.png", EMAIL)
    return False

def _read_alert(sb):
    try: return (sb.find_element("div.alert", timeout=4).text or "").strip()
    except Exception: return ""

def _goto_server_detail(sb) -> bool:
    print("\n🖥️  正在进入服务器续期页...")
    time.sleep(5)
    alert_text = _read_alert(sb)
    if alert_text and "can't renew" in alert_text.lower():
        send_tg_message("⏳", "未到续期时间", alert_text, None, EMAIL)
        return False

    see_link = None
    selectors = ['a[href*="/servers/edit?id="]', 'td a[href*="/servers/edit"]', 'table a[href*="/servers/edit"]']
    for sel in selectors:
        try:
            see_link = sb.find_element(sel, timeout=8)
            break
        except Exception: continue

    if see_link is None:
        try:
            for a in sb.find_elements("a"):
                if (a.text or "").strip().lower() == "see":
                    see_link = a
                    break
        except Exception: pass

    if see_link is None:
        send_tg_message("❌", "未找到服务器列表", "未找到 See 按钮", None, EMAIL)
        return False

    see_link.click()
    time.sleep(5)
    return True

def _open_renew_modal(sb) -> bool:
    print("\n🔄 查找 Renew 按钮...")
    try: renew_btn = sb.find_element('button[data-bs-target="#renew-modal"], button.btn.btn-outline-primary', timeout=5)
    except Exception:
        send_tg_message("⚠️", "未找到 Renew 按钮", "未出现 Renew 按钮", None, EMAIL)
        return False

    sb.execute_script("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", renew_btn)
    time.sleep(0.8)
    renew_btn.click()
    time.sleep(3)
    try:
        sb.find_element('div.modal.show', timeout=5)
        return True
    except Exception: return False

def _solve_altcha(sb) -> bool:
    print("\n🔐 处理 ALTCHA 人机验证...")
    time.sleep(2)
    if sb.execute_script(_ALTCHA_SOLVED_JS): return True
    coords = None
    try: coords = sb.execute_script(_ALTCHA_EXPAND_JS)
    except Exception: pass

    for attempt in range(3):
        if sb.execute_script(_ALTCHA_SOLVED_JS): return True
        if coords:
            try: wi = sb.execute_script(_WININFO_JS)
            except Exception: wi = {"sx": 0, "sy": 0, "oh": 800, "ih": 768}
            _xdotool_click(coords["cx"] + wi["sx"], coords["cy"] + wi["sy"] + (wi["oh"] - wi["ih"]))

        sb.execute_script("""
            (function(){
                var m = document.querySelector('div.modal.show'); if(!m) return;
                var fs = m.querySelectorAll('iframe'); for(var i=0;i<fs.length;i++) fs[i].click();
                var cbs = m.querySelectorAll('input[type="checkbox"]');
                for(var k=0;k<cbs.length;k++) if(!cbs[k].disabled) cbs[k].click();
            })()
        """)
        for _ in range(6):
            time.sleep(1)
            if sb.execute_script(_ALTCHA_SOLVED_JS): return True
    return False

def _submit_renew(sb):
    print("🖱️  点击 Renew...")
    sb.execute_script("""
        (function(){
            var m = document.querySelector('div.modal.show'); if(!m) return;
            var bs = m.querySelectorAll('button');
            for(var i=0;i<bs.length;i++) if(/renew/i.test(bs[i].textContent)) bs[i].click();
        })()
    """)
    time.sleep(3)

def _check_renew_result(sb):
    print("\n📋 检查续期结果...")
    alert_text = _read_alert(sb)
    if not alert_text:
        time.sleep(3)
        alert_text = _read_alert(sb)

    sb.save_screenshot("renew_result.png")
    if alert_text:
        low = alert_text.lower()
        if "can't renew" in low or "unable" in low:
            send_tg_message("⏳", "未到续期时间", alert_text, "renew_result.png", EMAIL)
        elif any(kw in low for kw in ("renewed", "success", "extended")):
            send_tg_message("✅", "续期成功", alert_text, "renew_result.png", EMAIL)
        else:
            send_tg_message("ℹ️", "续期已执行", alert_text, "renew_result.png", EMAIL)
    else:
        send_tg_message("ℹ️", "续期已执行", "未检测到明确提示", "renew_result.png", EMAIL)

def renew_server(sb):
    print("\n" + "#" * 25 + "\n  开始自动续期\n" + "#" * 25)
    if not _goto_server_detail(sb): return
    if not _open_renew_modal(sb): return
    _solve_altcha(sb)
    _submit_renew(sb)
    _check_renew_result(sb)

def manage_control_panel(sb):
    print("\n" + "#" * 35 + f"\n  初始化面板通信: {CONTROL_URL}\n" + "#" * 35)

    if not CONTROL_ID:
        send_tg_message("⚠️", "登录被拦截", "未检测到 CONTROL_ID", target_email=EMAIL)
        return
        
    if not CONTROL_PASSWORD:
        return

    sb.uc_open_with_reconnect(CONTROL_URL, reconnect_time=8)
    time.sleep(6)

    if "/auth/login" in sb.get_current_url().lower():
        print(f"📧 注入凭证: {CONTROL_ID}...")
        try:
            # 兼容多种常见的输入框命名方案
            user_sel = 'input[name="user"], input[name="username"], input[type="text"]'
            pass_sel = 'input[name="password"], input[type="password"]'
            
            sb.type(user_sel, CONTROL_ID)
            time.sleep(1)
            sb.type(pass_sel, CONTROL_PASSWORD)
            time.sleep(1.5) 
            
            if sb.execute_script(_EXISTS_JS): handle_turnstile(sb)
            
            try: sb.click('button[type="submit"], button:contains("Login"), button:contains("登录")', timeout=3)
            except Exception: sb.press_keys(pass_sel, '\n')
            
            login_success = False
            for i in range(15):
                time.sleep(1)
                if "/auth/login" not in sb.get_current_url().lower():
                    login_success = True
                    break
            
            if not login_success:
                sb.save_screenshot("control_login_fail.png")
                send_tg_message("❌", "面板登录失败", f"鉴权遭到拒绝", "control_login_fail.png", target_email=CONTROL_ID)
                return
        except Exception as e:
            print(f"⚠️ 执行器异常: {e}")
            return

    time.sleep(6) 
    
    if "/server/" not in sb.get_current_url().lower():
        try:
            if sb.is_element_present('a[href*="/server/"]'):
                sb.click('a[href*="/server/"]', timeout=8)
            else:
                sb.click('*:contains("Manage server")', timeout=8)
            time.sleep(6) 
        except Exception as e:
            print(f"⚠️ 无法进入详情页: {e}")

    # ==========================================
    # 修复核心：移除了下方原本冗余且破坏状态的重复代码段
    # ==========================================
    print("🔍 同步运行指标...")
    page_text = sb.get_text("body").lower()
    screenshot_file = "server_status.png"
    sb.save_screenshot(screenshot_file)

    is_offline = "offline" in page_text or "离线" in page_text
    is_starting = "starting" in page_text or "启动中" in page_text
    
    # 增加状态保护：防止在“启动中”状态下错误地触发重启
    if is_starting:
        print("⏳ 服务器当前正处于【启动中】(Starting) 状态，跳过电源控制操作避免状态死锁。")
        return
        
    if is_offline:
        print("💤 服务器【离线】(Offline)，执行开机...")
        try:
            sb.click('button:contains("Start"), button:contains("启动"), button[data-action="start"]', timeout=5)
            time.sleep(3)
            sb.save_screenshot("server_started.png")
            send_tg_message("🚀", "实例唤醒", f"已执行开机。", "server_started.png", target_email=CONTROL_ID)
        except Exception as e:
            send_tg_message("⚠️", "唤醒失败", "未能解析 Start 组件", screenshot_file, target_email=CONTROL_ID)
    else:
        print("🟢 服务器【运行】(Online)，执行刷新...")
        try:
            sb.click('button:contains("Restart"), button:contains("重启"), button[data-action="restart"]', timeout=5)
            time.sleep(3)
            sb.save_screenshot("server_restarted.png")
            send_tg_message("🔄", "实例刷新", f"已执行续命重启。", "server_restarted.png", target_email=CONTROL_ID)
        except Exception as e:
            send_tg_message("⚠️", "重启失败", "未能解析 Restart 组件", screenshot_file, target_email=CONTROL_ID)

def main():
    print("#" * 25 + "\n   katabump 自动管理\n" + "#" * 25)
    IS_PROXY = os.environ.get("IS_PROXY", "false").lower() == "true"
    proxy_str = os.environ.get("PROXY_SERVER", "").strip() or "http://127.0.0.1:1081"
    
    # 优化点：利用 xvfb=True 代替外部依赖，提升 GitHub Actions 兼容性
    sb_kwargs = {"uc": True, "headless": False, "xvfb": True}

    if IS_PROXY: sb_kwargs["proxy"] = proxy_str
    
    with SB(**sb_kwargs) as sb:
        if login(sb):
            renew_server(sb)   
            manage_control_panel(sb)
        else:
            print("\n❌ 登录失败终止操作。")

if __name__ == "__main__":
    main()
