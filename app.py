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

# 2. 控制面板 (Control Panel) 账号密码 
# (强制修改：取消了对 EMAIL/PASSWORD 的兜底，严格只用这两项登录)
CONTROL_ID       = os.environ.get("CONTROL_ID") or ""       
CONTROL_PASSWORD = os.environ.get("CONTROL_PASSWORD") or "" 

# 3. TG 推送配置
TG_CHAT_ID   = os.environ.get("TG_CHAT_ID") or ""        
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") or ""      

BASE_URL = "https://dashboard.katabump.com"  
CONTROL_URL = "https://control.katabump.com/server/3c771e38" 

# ==========================================
# Telegram 推送模块
# ==========================================
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
                    url, data={"chat_id": TG_CHAT_ID, "caption": text}, files={"photo": f}, timeout=15
                )
            if r.status_code == 200:
                print(f"📩 Telegram 带图通知发送成功！({image_path})")
                return
            else:
                print(f"⚠️ Telegram 带图发送失败: {r.text}，回退为纯文字...")
        except Exception as e:
            print(f"⚠️ Telegram 带图发送异常: {e}，回退为纯文字...")

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

# ==========================================
# JS 脚本注入常量
# ==========================================
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

# ==========================================
# 辅助函数
# ==========================================
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

# ==========================================
# 核心业务逻辑
# ==========================================
def handle_turnstile(sb) -> bool:
    print("🔍 处理 Cloudflare Turnstile 验证...")
    time.sleep(2)

    if sb.execute_script(_SOLVED_JS):
        print("✅ 已静默通过")
        return True

    for _ in range(3):
        try: sb.execute_script(_EXPAND_JS)
        except Exception: pass
        time.sleep(0.5)

    for attempt in range(6):
        if sb.execute_script(_SOLVED_JS):
            print(f"✅ Turnstile 通过（第 {attempt} 次尝试）")
            return True

        print(f"🖱️ 第 {attempt + 1} 次调用 uc_gui_click_captcha...")
        try:
            sb.uc_gui_click_captcha()
        except Exception as e:
            print(f"⚠️ uc_gui_click_captcha 调用异常: {e}")

        for _ in range(16):
            time.sleep(0.5)
            if sb.execute_script(_SOLVED_JS):
                print(f"✅ Turnstile 通过（第 {attempt + 1} 次尝试）")
                return True

        print(f"⚠️ 第 {attempt + 1} 次未通过，重试...")

    print("❌ Turnstile 6 次均失败")
    return False

def login(sb) -> bool:
    print(f"🌐 打开登录页面: {BASE_URL}/auth/login")
    sb.uc_open_with_reconnect(BASE_URL + "/auth/login", reconnect_time=8)
    time.sleep(6)

    print("⏳ 等待 Cloudflare 验证通过...")
    cf_passed = False
    for i in range(30):
        page_src = sb.get_page_source() or ""
        if 'input[name="email"]' in page_src.lower() or 'name="email"' in page_src.lower():
            cf_passed = True
            print(f"✅ Cloudflare 验证已通过（{i+1}s）")
            break
        time.sleep(1)

    try:
        sb.wait_for_element('input[name="email"]', timeout=15)
    except Exception:
        try:
            sb.wait_for_element('input[name="Email"]', timeout=5)
        except Exception:
            print("❌ 页面未加载出登录表单")
            sb.save_screenshot("login_load_fail.png")
            send_tg_message("❌", "登录失败", "页面未加载出登录表单", "login_load_fail.png", EMAIL)
            return False

    try:
        for btn in sb.find_elements("button"):
            if "Accept" in (btn.text or ""):
                btn.click()
                time.sleep(0.5)
                break
    except Exception:
        pass

    print(f"📧 填写邮箱...")
    js_fill_input(sb, 'input[name="email"]', EMAIL)
    time.sleep(0.3)
    
    print("🔑 填写密码...")
    js_fill_input(sb, 'input[name="password"]', PASSWORD)
    time.sleep(1)

    ts_found = False
    for i in range(10):
        if sb.execute_script(_EXISTS_JS):
            ts_found = True
            print(f"✅ 检测到 Turnstile（{i+1}s）")
            break
        time.sleep(1)

    if ts_found:
        if not handle_turnstile(sb):
            print("❌ 登录界面的 Turnstile 验证失败")
            sb.save_screenshot("login_turnstile_fail.png")
            send_tg_message("❌", "登录失败", "Turnstile 验证未通过", "login_turnstile_fail.png", EMAIL)
            return False

    print("🖱️ 敲击回车提交表单...")
    sb.press_keys('input[name="password"]', '\n')

    print("⏳ 等待登录跳转...")
    for _ in range(12):
        time.sleep(1)
        cur_url = sb.get_current_url().split('?')[0].lower()
        if cur_url.startswith(f"{BASE_URL}/dashboard"):
            break

    cur_url = sb.get_current_url().split('?')[0].lower()
    if cur_url.startswith(f"{BASE_URL}/dashboard"):
        print("✅ 登录成功！")
        return True
        
    print("❌ 登录失败，页面未跳转到账户页。")
    sb.save_screenshot("login_failed.png")
    send_tg_message("❌", "登录失败", f"跳转失败 (URL: {sb.get_current_url()})", "login_failed.png", EMAIL)
    return False

def _read_alert(sb):
    try:
        el = sb.find_element("div.alert", timeout=4)
        return (el.text or "").strip()
    except Exception:
        return ""

def _goto_server_detail(sb) -> bool:
    print("\n🖥️ 正在进入服务器续期页...")
    time.sleep(5)

    alert_text = _read_alert(sb)
    if alert_text and "can't renew" in alert_text.lower():
        print(f"ℹ️ 页面顶部提示: {alert_text}")
        sb.save_screenshot("renew_not_time.png")
        send_tg_message("⏳", "未到续期时间", alert_text, "renew_not_time.png", EMAIL)
        return False

    selectors = [
        'a[href*="/servers/edit?id="]',
        'td a[href*="/servers/edit"]',
        'table a[href*="/servers/edit"]',
        'table td a',
    ]

    see_link = None
    for sel in selectors:
        try:
            see_link = sb.find_element(sel, timeout=8)
            break
        except Exception:
            continue

    if see_link is None:
        try:
            for a in sb.find_elements("a"):
                if (a.text or "").strip().lower() == "see":
                    see_link = a
                    break
        except Exception:
            pass

    if see_link is None:
        cur_url = sb.get_current_url()
        print(f"❌ 未找到 'See' 链接")
        sb.save_screenshot("servers_page_fail.png")
        send_tg_message("❌", "未找到服务器列表", f"未找到 See 按钮 ({cur_url})", "servers_page_fail.png", EMAIL)
        return False

    see_link.click()
    time.sleep(5)
    return True

def _open_renew_modal(sb) -> bool:
    print("\n🔄 查找 Renew 按钮...")
    try:
        renew_btn = sb.find_element('button[data-bs-target="#renew-modal"]', timeout=10)
    except Exception:
        try:
            renew_btn = sb.find_element('button.btn.btn-outline-primary', timeout=5)
        except Exception:
            print("   ❌ 未找到 Renew 按钮")
            sb.save_screenshot("renew_btn_not_found.png")
            send_tg_message("⚠️", "未找到 Renew 按钮", "服务器详情页未出现 Renew 按钮", "renew_btn_not_found.png", EMAIL)
            return False

    sb.execute_script("""
        (function(){
            var btn = document.querySelector('button[data-bs-target="#renew-modal"]')
                      || document.querySelector('button.btn.btn-outline-primary');
            if (btn) btn.scrollIntoView({behavior:'smooth',block:'center'});
        })()
    """)
    time.sleep(0.8)
    renew_btn.click()
    time.sleep(3)

    try:
        sb.find_element('div.modal.show', timeout=5)
        return True
    except Exception:
        sb.save_screenshot("renew_modal_failed.png")
        return False

def _solve_altcha(sb) -> bool:
    print("\n🔐 处理 ALTCHA 人机验证...")
    time.sleep(2)

    if sb.execute_script(_ALTCHA_SOLVED_JS):
        return True

    coords = None
    try:
        coords = sb.execute_script(_ALTCHA_EXPAND_JS)
    except Exception: pass

    for attempt in range(3):
        if sb.execute_script(_ALTCHA_SOLVED_JS):
            return True

        if coords:
            try: wi = sb.execute_script(_WININFO_JS)
            except Exception: wi = {"sx": 0, "sy": 0, "oh": 800, "ih": 768}
            bar = wi["oh"] - wi["ih"]
            ax  = coords["cx"] + wi["sx"]
            ay  = coords["cy"] + wi["sy"] + bar
            _xdotool_click(ax, ay)

        try:
            iframes = sb.find_elements('div.modal.show iframe')
            for iframe in iframes:
                try: iframe.click()
                except Exception: pass
        except Exception: pass

        sb.execute_script("""
            (function(){
                var modal = document.querySelector('div.modal.show');
                if (!modal) return;
                var iframes = modal.querySelectorAll('iframe');
                for (var i = 0; i < iframes.length; i++) {
                    iframes[i].click();
                    iframes[i].dispatchEvent(new MouseEvent('click', {bubbles:true}));
                }
                var cbs = modal.querySelectorAll('input[type="checkbox"]');
                for (var k = 0; k < cbs.length; k++) {
                    if (!cbs[k].disabled) {
                        cbs[k].click();
                        cbs[k].dispatchEvent(new MouseEvent('click', {bubbles:true}));
                    }
                }
            })()
        """)

        for _ in range(6):
            time.sleep(1)
            if sb.execute_script(_ALTCHA_SOLVED_JS):
                return True

        try:
            new_coords = sb.execute_script(_ALTCHA_EXPAND_JS)
            if new_coords: coords = new_coords
        except Exception: pass

    return False

def _submit_renew(sb):
    print("🖱️ 点击模态框中的 Renew 按钮...")
    try:
        submit = sb.find_element('div.modal.show button.btn-primary', timeout=5)
        submit.click()
    except Exception:
        sb.execute_script("""
            (function(){
                var m = document.querySelector('div.modal.show');
                if (!m) return;
                var bs = m.querySelectorAll('button');
                for (var i = 0; i < bs.length; i++)
                    if (/renew/i.test(bs[i].textContent)) bs[i].click();
            })()
        """)
    time.sleep(3)

def _check_renew_result(sb):
    print("\n📋 检查续期结果...")
    alert_text = _read_alert(sb)
    if not alert_text:
        time.sleep(3)
        alert_text = _read_alert(sb)

    screenshot_file = "renew_result.png"
    sb.save_screenshot(screenshot_file)

    if alert_text:
        print(f"📩 页面提示: {alert_text}")
        low = alert_text.lower()
        if "can't renew" in low or "unable" in low:
            send_tg_message("⏳", "未到续期时间", alert_text, screenshot_file, EMAIL)
        elif any(kw in low for kw in ("renewed", "success", "extended")):
            send_tg_message("✅", "续期成功", alert_text, screenshot_file, EMAIL)
        else:
            send_tg_message("ℹ️", "续期操作已执行", alert_text, screenshot_file, EMAIL)
    else:
        send_tg_message("ℹ️", "续期操作已执行", "未检测到明确提示", screenshot_file, EMAIL)

def renew_server(sb):
    print("\n" + "#" * 25)
    print("  开始自动续期流程")
    print("#" * 25)

    if not _goto_server_detail(sb):
        return
    if not _open_renew_modal(sb):
        return
    altcha_ok = _solve_altcha(sb)
    if not altcha_ok:
        print("⚠️ ALTCHA 验证未通过，仍尝试提交 Renew...")

    _submit_renew(sb)
    _check_renew_result(sb)

# =======================================================
# 重写后的控制面板逻辑（严格使用 CONTROL_ID/PASSWORD）
# =======================================================
def manage_control_panel(sb):
    print("\n" + "#" * 25)
    print(f"  开始管理控制面板: {CONTROL_URL}")
    print("#" * 25)

    # 严格拦截：如果不设置 CONTROL_ID 和 CONTROL_PASSWORD，则直接跳过，防止使用主账号登录报错
    if not CONTROL_ID or not CONTROL_PASSWORD:
        print("⚠️ 环境变量中未配置 CONTROL_ID 或 CONTROL_PASSWORD，跳过控制面板管理步骤。")
        return

    print("🌐 打开控制面板...")
    sb.uc_open_with_reconnect(CONTROL_URL, reconnect_time=8)
    time.sleep(6)

    current_url = sb.get_current_url().lower()
    
    if "/auth/login" in current_url:
        print("📧 填写控制面板账号...")
        try:
            # 确保 React 输入框加载出来
            sb.wait_for_element('input[type="text"], input[name="user"], input[name="username"]', timeout=10)
            
            # 使用 sb.type 模拟真实的逐字敲击动作，100% 触发 React 底层的 onChange 事件，解决 js_fill_input 表单为空的问题
            if sb.is_element_present('input[name="user"]'):
                sb.type('input[name="user"]', CONTROL_ID)
            elif sb.is_element_present('input[name="username"]'):
                sb.type('input[name="username"]', CONTROL_ID)
            else:
                sb.type('input[type="text"]', CONTROL_ID)
                
            time.sleep(1)
            
            print("🔑 填写控制面板密码...")
            if sb.is_element_present('input[name="password"]'):
                sb.type('input[name="password"]', CONTROL_PASSWORD)
            else:
                sb.type('input[type="password"]', CONTROL_PASSWORD)
            
            time.sleep(1)
            
            if sb.execute_script(_EXISTS_JS):
                print("🔍 控制面板登录页检测到 Turnstile, 尝试处理...")
                handle_turnstile(sb)
            
            print("🖱️ 敲击回车提交登录信息...")
            # 抛弃不可靠的按钮点击，直接对密码输入框触发回车 (Enter) 键，这是对 React 表单成功率最高的方式
            sb.press_keys('input[type="password"], input[name="password"]', '\n')
            
            print("⏳ 等待控制面板登录跳转...")
            login_success = False
            for i in range(15):
                time.sleep(1)
                if "/auth/login" not in sb.get_current_url().lower():
                    login_success = True
                    print(f"✅ 登录成功，页面已跳转 (耗时 {i+1}s)")
                    break
            
            if not login_success:
                print("❌ 控制面板登录失败，页面未跳转。请检查 CONTROL_ID 和 CONTROL_PASSWORD。")
                sb.save_screenshot("control_login_fail.png")
                # 推送时附加上当前使用的 CONTROL_ID，方便核对问题
                send_tg_message("❌", "面板登录失败", "控制面板账号密码不匹配或遇到二次验证", "control_login_fail.png", target_email=CONTROL_ID)
                return
        except Exception as e:
            print(f"⚠️ 控制面板登录过程异常: {e}")
            return

    print("⏳ 检查服务器当前状态...")
    time.sleep(8) 
    
    page_text = sb.get_text("body").lower()
    screenshot_file = "server_status.png"
    sb.save_screenshot(screenshot_file)

    is_offline = "offline" in page_text or "离线" in page_text
    
    if is_offline:
        print("💤 服务器当前处于【离线】状态，准备启动...")
        try:
            sb.click('button:contains("Start"), button:contains("启动"), button[data-action="start"]', timeout=5)
            print("✅ 已点击【启动】按钮")
            time.sleep(3)
            sb.save_screenshot("server_started.png")
            send_tg_message("🚀", "服务器已启动", f"检测到服务器离线，已执行开机操作。\n面板: {CONTROL_URL}", "server_started.png", target_email=CONTROL_ID)
        except Exception as e:
            print(f"⚠️ 无法找到启动按钮: {e}")
            send_tg_message("⚠️", "启动服务器失败", "在控制面板未找到Start/启动按钮", screenshot_file, target_email=CONTROL_ID)
    else:
        print("🟢 服务器当前处于【运行】状态，准备重启...")
        try:
            sb.click('button:contains("Restart"), button:contains("重启"), button[data-action="restart"]', timeout=5)
            print("✅ 已点击【重启】按钮")
            time.sleep(3)
            sb.save_screenshot("server_restarted.png")
            send_tg_message("🔄", "服务器已重启", f"服务器当前在线，已执行重启操作。\n面板: {CONTROL_URL}", "server_restarted.png", target_email=CONTROL_ID)
        except Exception as e:
            print(f"⚠️ 无法找到重启按钮: {e}")
            send_tg_message("⚠️", "重启服务器失败", "在控制面板未找到Restart/重启按钮", screenshot_file, target_email=CONTROL_ID)

# ==========================================
# 脚本入口
# ==========================================
def main():
    print("#" * 25)
    print("   katabump 自动登录续期与管理")
    print("#" * 25)

    IS_PROXY = os.environ.get("IS_PROXY", "false").lower() == "true"
    proxy_str = os.environ.get("PROXY_SERVER", "").strip() or "http://127.0.0.1:1081"
    
    sb_kwargs = {"uc": True, "headless": False}

    if IS_PROXY:
        print(f"🔗 挂载代理: {proxy_str}")
        sb_kwargs["proxy"] = proxy_str
    else:
        print("🌐 未使用代理，直连访问")
    
    print("🚀 启动浏览器...")
    with SB(**sb_kwargs) as sb:
        if login(sb):
            renew_server(sb)   
            manage_control_panel(sb)
        else:
            print("\n❌ 登录失败，终止后续续期及控制面板操作。")

if __name__ == "__main__":
    main()
