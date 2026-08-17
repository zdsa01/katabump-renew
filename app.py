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

# 2. 控制面板 (Control Panel) 账号密码（修改为 ID + PASSWORD）
# 如果你的控制面板密码与财务面板不同，请在环境变量中额外配置这两项
CONTROL_ID       = os.environ.get("CONTROL_ID") or "464a09985b68e31"       # 使用 ID 登录
CONTROL_PASSWORD = os.environ.get("CONTROL_PASSWORD") or PASSWORD 

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

    # 获取北京时间 (UTC+8)
    local_time = time.gmtime(time.time() + 8 * 3600)
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", local_time)

    # 账号脱敏：兼容邮箱和纯ID
    if target_email and '@' in target_email:
        name, domain = target_email.split('@', 1)
        if len(name) > 4:
            masked_email = f"{name[:2]}****{name[-2:]}@{domain}"
        else:
            masked_email = f"{name}@{domain}"
    else:
        # 如果是纯 ID 登录
        masked_email = target_email[:2] + '****' if target_email and len(target_email) >= 2 else target_email

    text = (
        f"🇫🇷 katabump 通知\n\n"
        f"{status_icon} {status_text}\n"
        f"👤 账户: {masked_email}\n"
        f"⏱️ 时间: {current_time_str}"
    )
    if time_left:
        text += f"\nℹ️ 详细说明: {time_left}"

    # 1. 优先尝试发送带图消息
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

    # 2. 回退方案：发送纯文字消息
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("📩 Telegram 文字通知发送成功！")
        else:
            print(f"⚠️ Telegram 通知发送失败: {r.text}")
    except Exception as e:
        print(f"⚠️ Telegram 通知发送异常: {e}")

#  页面注入脚本
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

# ===== 自动续期相关 =====

# 在模态框内查找 iframe 并展开，返回点击坐标
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

# 检测 ALTCHA 是否已验证通过
_ALTCHA_SOLVED_JS = """
(function(){
    var modal = document.querySelector('div.modal.show') || document;
    // hidden input 有值
    var inputs = modal.querySelectorAll('input[type="hidden"]');
    for (var i = 0; i < inputs.length; i++) {
        var n = (inputs[i].name || '').toLowerCase();
        if ((n.includes('altcha') || n.includes('captcha')) &&
            inputs[i].value && inputs[i].value.length > 20) return true;
    }
    // checkbox 变为 disabled
    var cbs = modal.querySelectorAll('input[type="checkbox"]');
    for (var j = 0; j < cbs.length; j++) {
        if (cbs[j].disabled) return true;
    }
    // widget data-state 属性
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

#  人机验证处理
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

    print("  ❌ Turnstile 6 次均失败")
    return False

#  账户登录
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
    if not cf_passed:
        print("⚠️ Cloudflare 验证可能未通过，继续尝试...")

    try:
        sb.wait_for_element('input[name="email"]', timeout=15)
    except Exception:
        try:
            sb.wait_for_element('input[name="Email"]', timeout=5)
        except Exception:
            print("❌ 页面未加载出登录表单")
            cur_url = sb.get_current_url()
            page_title = sb.get_title() or ""
            print(f"  当前 URL: {cur_url}")
            print(f"  当前标题: {page_title}")
            sb.save_screenshot("login_load_fail.png")
            send_tg_message("❌", "登录失败", f"页面未加载出登录表单 ({cur_url})", "login_load_fail.png", EMAIL)
            return False

    print("🍪 关闭可能的 Cookie 弹窗...")
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

    print("⏳ 等待 Turnstile 验证框出现...")
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
    else:
        print("ℹ️ 未检测到 Turnstile")

    print("🖱️ 敲击回车提交表单...")
    sb.press_keys('input[name="password"]', '\n')

    print("⏳ 等待登录跳转...")
    for _ in range(12):
        time.sleep(1)
        cur_url = sb.get_current_url().split('?')[0].lower()
        page_title = sb.get_title() or ""
        if cur_url.startswith(f"{BASE_URL}/dashboard") or "dashboard | katabump" in page_title.lower():
            break

    cur_url = sb.get_current_url().split('?')[0].lower()
    page_title = sb.get_title() or ""
    if cur_url.startswith(f"{BASE_URL}/dashboard") or "dashboard | katabump" in page_title.lower():
        print(f"✅ 登录成功！(URL: {sb.get_current_url()}, Title: {page_title})")
        return True
        
    print(f"❌ 登录失败，页面未跳转到账户页。(URL: {sb.get_current_url()}, Title: {page_title})")
    sb.save_screenshot("login_failed.png")
    send_tg_message("❌", "登录失败", f"跳转失败 (URL: {sb.get_current_url()})", "login_failed.png", EMAIL)
    return False

# ===== 自动续期流程 =====

def _read_alert(sb):
    try:
        el = sb.find_element("div.alert", timeout=4)
        return (el.text or "").strip()
    except Exception:
        return ""

def _goto_server_detail(sb) -> bool:
    print("\n🖥️  正在进入服务器续期页...")
    time.sleep(5)

    alert_text = _read_alert(sb)
    if alert_text and "can't renew" in alert_text.lower():
        print(f"ℹ️  页面顶部提示: {alert_text}")
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
            print(f"✅ 通过选择器找到链接: {sel}")
            break
        except Exception:
            continue

    if see_link is None:
        print("⚠️ 选择器未命中，尝试文本匹配...")
        try:
            for a in sb.find_elements("a"):
                if (a.text or "").strip().lower() == "see":
                    see_link = a
                    print("✅ 通过文本 'See' 找到链接")
                    break
        except Exception:
            pass

    if see_link is None:
        cur_url = sb.get_current_url()
        title = sb.get_title() or ""
        print(f"❌ 未找到 'See' 链接")
        sb.save_screenshot("servers_page_fail.png")
        send_tg_message("❌", "未找到服务器列表", f"未找到 See 按钮 ({cur_url})", "servers_page_fail.png", EMAIL)
        return False

    print("🖱️  点击 'See' 进入服务器详情页...")
    see_link.click()
    time.sleep(5)
    print(f"📄 当前页面: {sb.get_current_url()}")
    return True


def _open_renew_modal(sb) -> bool:
    print("\n🔄 查找 Renew 按钮...")
    try:
        renew_btn = sb.find_element('button[data-bs-target="#renew-modal"]', timeout=10)
    except Exception:
        try:
            renew_btn = sb.find_element('button.btn.btn-outline-primary', timeout=5)
        except Exception:
            print("  ❌ 未找到 Renew 按钮")
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
    print("🖱️ 已点击 Renew 按钮，等待 ALTCHA 验证框...")
    time.sleep(3)

    try:
        sb.find_element('div.modal.show', timeout=5)
        print("✅ Renew 模态框已弹出")
        return True
    except Exception:
        print("⚠️ 模态框未弹出")
        sb.save_screenshot("renew_modal_failed.png")
        return False


def _solve_altcha(sb) -> bool:
    print("\n🔐 处理 ALTCHA 人机验证...")
    time.sleep(2)

    if sb.execute_script(_ALTCHA_SOLVED_JS):
        print("✅ ALTCHA 已自动通过")
        return True

    coords = None
    try:
        coords = sb.execute_script(_ALTCHA_EXPAND_JS)
    except Exception:
        pass

    if coords:
        print(f"  📍 找到模态框内 iframe 坐标: ({coords['cx']}, {coords['cy']})")

    for attempt in range(3):
        if sb.execute_script(_ALTCHA_SOLVED_JS):
            print(f"✅ ALTCHA 验证通过（第 {attempt + 1} 轮）")
            return True

        if coords:
            try:
                wi = sb.execute_script(_WININFO_JS)
            except Exception:
                wi = {"sx": 0, "sy": 0, "oh": 800, "ih": 768}
            bar = wi["oh"] - wi["ih"]
            ax  = coords["cx"] + wi["sx"]
            ay  = coords["cy"] + wi["sy"] + bar
            print(f"🖱️  ALTCHA点击复选框  ({ax}, {ay})")
            _xdotool_click(ax, ay)

        try:
            iframes = sb.find_elements('div.modal.show iframe')
            for iframe in iframes:
                try:
                    iframe.click()
                    print("🖱️  SeleniumBase 点击模态框 iframe")
                except Exception:
                    pass
        except Exception:
            pass

        sb.execute_script("""
            (function(){
                var modal = document.querySelector('div.modal.show');
                if (!modal) return;
                var iframes = modal.querySelectorAll('iframe');
                for (var i = 0; i < iframes.length; i++) {
                    iframes[i].click();
                    iframes[i].dispatchEvent(new MouseEvent('click', {bubbles:true}));
                }
                var labels = modal.querySelectorAll('label');
                for (var j = 0; j < labels.length; j++) {
                    var txt = (labels[j].textContent || '').toLowerCase();
                    if (txt.includes('robot') || txt.includes('captcha') || txt.includes('verify'))
                        labels[j].click();
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
                print(f"✅ ALTCHA 验证通过（第 {attempt + 1} 轮）")
                return True

        print(f"  ⚠️ 第 {attempt + 1} 轮未通过，重试...")
        try:
            new_coords = sb.execute_script(_ALTCHA_EXPAND_JS)
            if new_coords:
                coords = new_coords
        except Exception:
            pass

    print("  ❌ ALTCHA 3 轮均失败")
    return False


def _submit_renew(sb):
    print("🖱️  点击模态框中的 Renew 按钮...")
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
        print("ℹ️ 未检测到明确的提示框，可能续期操作未生效")
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


# ===== 控制面板运行状态管理 =====

def manage_control_panel(sb):
    """检查控制面板的运行状态，离线则启动，在线则重启"""
    print(f"\n" + "#" * 25)
    print(f"  开始管理控制面板: {CONTROL_URL}")
    print("#" * 25)

    print("🌐 打开控制面板...")
    sb.uc_open_with_reconnect(CONTROL_URL, reconnect_time=8)
    time.sleep(6)

    current_url = sb.get_current_url().lower()
    
    # 获取准备使用的 ID
    login_id = CONTROL_ID if CONTROL_ID else EMAIL
    
    if "/auth/login" in current_url:
        print(f"🔑 控制面板需要登录，尝试填入专属账号 ID: {464a09985b68e31} ...")
        
        if not CONTROL_ID:
            print("⚠️ 未配置 CONTROL_ID 环境变量，使用填入专属账号 ID: {464a09985b68e31}...")

        try:
            # 填入账号 ID：适配主流 Pterodactyl 面板
            if sb.is_element_present('input[name="user"]'):
                sb.type('input[name="user"]', login_id)
            elif sb.is_element_present('input[name="username"]'):
                sb.type('input[name="username"]', login_id)
            elif sb.is_element_present('input[type="text"]'):
                sb.type('input[type="text"]', login_id)
                
            time.sleep(0.5)
            
            # 填入密码
            if sb.is_element_present('input[name="password"]'):
                sb.type('input[name="password"]', CONTROL_PASSWORD)
            elif sb.is_element_present('input[type="password"]'):
                sb.type('input[type="password"]', CONTROL_PASSWORD)
            
            time.sleep(1)
            
            if sb.execute_script(_EXISTS_JS):
                print("🔍 控制面板登录页检测到 Turnstile, 尝试处理...")
                handle_turnstile(sb)
            
            print("🖱️ 提交登录信息...")
            try:
                # 优先寻找 button 元素并点击
                sb.click('button[type="submit"], button:contains("Login"), button:contains("登录")', timeout=3)
            except Exception:
                # 找不到明确按钮时回退到敲击回车
                sb.press_keys('input[type="password"]', '\n')
            
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
                # 推送时附带控制面板的 ID，方便核实
                send_tg_message("❌", "面板登录失败", "控制面板账号密码不匹配或遇到二次验证", "control_login_fail.png", target_email=login_id)
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
            send_tg_message("🚀", "服务器已启动", f"检测到服务器离线，已执行开机操作。\n面板: {CONTROL_URL}", "server_started.png", target_email=login_id)
        except Exception as e:
            print(f"⚠️ 无法找到启动按钮: {e}")
            send_tg_message("⚠️", "启动服务器失败", "在控制面板未找到Start/启动按钮", screenshot_file, target_email=login_id)
    else:
        print("🟢 服务器当前处于【运行】状态，准备重启...")
        try:
            sb.click('button:contains("Restart"), button:contains("重启"), button[data-action="restart"]', timeout=5)
            print("✅ 已点击【重启】按钮")
            time.sleep(3)
            sb.save_screenshot("server_restarted.png")
            send_tg_message("🔄", "服务器已重启", f"服务器当前在线，已执行重启操作。\n面板: {CONTROL_URL}", "server_restarted.png", target_email=login_id)
        except Exception as e:
            print(f"⚠️ 无法找到重启按钮: {e}")
            send_tg_message("⚠️", "重启服务器失败", "在控制面板未找到Restart/重启按钮", screenshot_file, target_email=login_id)


#  脚本执行入口 
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
        try:
            sb.open("https://api.ip.sb/ip")
            print(f"📍  当前出口IP: {sb.get_text('body')}")
        except Exception:
            pass

        if login(sb):
            renew_server(sb)   
            manage_control_panel(sb)
        else:
            print("\n❌ 登录失败，终止后续续期及控制面板操作。")

if __name__ == "__main__":
    main()
