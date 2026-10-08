#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
import subprocess
import requests
from seleniumbase import SB

# ==========================================
# 从环境变量获取账号密码和 TG 配置
# ==========================================
EMAIL = os.environ.get("KATABUMP_EMAIL") or ""
PASSWORD = os.environ.get("KATABUMP_PASSWORD") or ""

CONTROL_ID = os.environ.get("CONTROL_ID") or ""
CONTROL_PASSWORD = os.environ.get("CONTROL_PASSWORD") or PASSWORD

TG_CHAT_ID = os.environ.get("TG_CHAT_ID") or ""
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") or ""

BASE_URL = "https://dashboard.katabump.com"
CONTROL_URL = "https://control.katabump.com/server/3c771e38"   # 可按需修改

# ------------------------------------------------------------------
# Telegram 推送
# ------------------------------------------------------------------
def send_tg_message(status_icon, status_text, time_left="", image_path=None, target_email=EMAIL):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("ℹ️ 未配置 TG_BOT_TOKEN 或 TG_CHAT_ID，跳过 Telegram 推送。")
        return

    local_time = time.gmtime(time.time() + 8 * 3600)
    current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", local_time)

    if target_email and '@' in target_email:
        name, domain = target_email.split('@', 1)
        masked_email = f"{name[:2]}****{name[-2:]}@{domain}" if len(name) > 4 else f"{name}@{domain}"
    else:
        masked_email = (target_email[:2] + '****') if target_email and len(target_email) >= 2 else target_email

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
                r = requests.post(url, data={"chat_id": TG_CHAT_ID, "caption": text},
                                  files={"photo": f}, timeout=15)
            if r.status_code == 200:
                print(f"📩 Telegram 带图通知发送成功！({image_path})")
                return
            print(f"⚠️ Telegram 带图发送失败: {r.text}，回退为纯文字...")
        except Exception as e:
            print(f"⚠️ Telegram 带图发送异常: {e}，回退为纯文字...")

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": text}, timeout=10)
        if r.status_code == 200:
            print("📩 Telegram 文字通知发送成功！")
        else:
            print(f"⚠️ Telegram 通知发送失败: {r.text}")
    except Exception as e:
        print(f"⚠️ Telegram 通知发送异常: {e}")


# ------------------------------------------------------------------
# JS 辅助脚本
# ------------------------------------------------------------------
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
(function(){ return document.querySelector('input[name="cf-turnstile-response"]') !== null; })()
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
            iframes[i].style.width = '300px';
            iframes[i].style.height = '150px';
            iframes[i].style.minWidth = '300px';
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
            r = subprocess.run(["xdotool", "search", "--onlyvisible", "--class", cls],
                               capture_output=True, text=True, timeout=3)
            wids = [w for w in r.stdout.strip().split("\n") if w.strip()]
            if wids:
                subprocess.run(["xdotool", "windowactivate", "--sync", wids[0]],
                               timeout=3, stderr=subprocess.DEVNULL)
                time.sleep(0.2)
                return
        except Exception:
            pass
    try:
        subprocess.run(["xdotool", "getactivewindow", "windowactivate"],
                       timeout=3, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def _xdotool_click(x: int, y: int):
    _activate_window()
    try:
        subprocess.run(["xdotool", "mousemove", "--sync", str(x), str(y)],
                       timeout=3, stderr=subprocess.DEVNULL)
        time.sleep(0.15)
        subprocess.run(["xdotool", "click", "1"], timeout=2, stderr=subprocess.DEVNULL)
    except Exception:
        os.system(f"xdotool mousemove {x} {y} click 1 2>/dev/null")


# ------------------------------------------------------------------
# Cloudflare Turnstile
# ------------------------------------------------------------------
def handle_turnstile(sb) -> bool:
    print("🔍 处理 Cloudflare Turnstile 验证...")
    time.sleep(2)
    if sb.execute_script(_SOLVED_JS):
        print("✅ 已静默通过")
        return True

    for _ in range(3):
        try:
            sb.execute_script(_EXPAND_JS)
        except Exception:
            pass
        time.sleep(0.5)

    for attempt in range(6):
        if sb.execute_script(_SOLVED_JS):
            print(f"✅ Turnstile 通过（第 {attempt + 1} 次尝试）")
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


# ------------------------------------------------------------------
# 登录 Dashboard
# ------------------------------------------------------------------
def login(sb) -> bool:
    print(f"🌐 打开登录页面: {BASE_URL}/auth/login")
    sb.uc_open_with_reconnect(BASE_URL + "/auth/login", reconnect_time=8)
    time.sleep(6)

    print("⏳ 等待 Cloudflare 验证通过...")
    cf_passed = False
    for i in range(30):
        page_src = (sb.get_page_source() or "").lower()
        if 'name="email"' in page_src or 'input[name="email"]' in page_src:
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
            print(f" 当前 URL: {cur_url}")
            print(f" 当前标题: {page_title}")
            sb.save_screenshot("login_load_fail.png")
            send_tg_message("❌", "登录失败", f"页面未加载出登录表单 ({cur_url})",
                            "login_load_fail.png", EMAIL)
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

    print("📧 填写邮箱...")
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
            send_tg_message("❌", "登录失败", "Turnstile 验证未通过",
                            "login_turnstile_fail.png", EMAIL)
            return False
    else:
        print("ℹ️ 未检测到 Turnstile")

    print("🖱️ 敲击回车提交表单...")
    sb.press_keys('input[name="password"]', '\n')

    print("⏳ 等待登录跳转...")
    for _ in range(12):
        time.sleep(1)
        cur_url = sb.get_current_url().split('?')[0].lower()
        page_title = (sb.get_title() or "").lower()
        if cur_url.startswith(f"{BASE_URL}/dashboard") or "dashboard | katabump" in page_title:
            break

    cur_url = sb.get_current_url().split('?')[0].lower()
    page_title = (sb.get_title() or "").lower()
    if cur_url.startswith(f"{BASE_URL}/dashboard") or "dashboard | katabump" in page_title:
        print(f"✅ 登录成功！(URL: {sb.get_current_url()}, Title: {sb.get_title()})")
        return True

    print(f"❌ 登录失败，页面未跳转到账户页。(URL: {sb.get_current_url()}, Title: {sb.get_title()})")
    sb.save_screenshot("login_failed.png")
    send_tg_message("❌", "登录失败", f"跳转失败 (URL: {sb.get_current_url()})",
                    "login_failed.png", EMAIL)
    return False


# ------------------------------------------------------------------
# 自动续期
# ------------------------------------------------------------------
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
        print("❌ 未找到 'See' 链接")
        sb.save_screenshot("servers_page_fail.png")
        send_tg_message("❌", "未找到服务器列表", f"未找到 See 按钮 ({cur_url})",
                        "servers_page_fail.png", EMAIL)
        return False

    print("🖱️ 点击 'See' 进入服务器详情页...")
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
            print("❌ 未找到 Renew 按钮")
            sb.save_screenshot("renew_btn_not_found.png")
            send_tg_message("⚠️", "未找到 Renew 按钮",
                            "服务器详情页未出现 Renew 按钮", "renew_btn_not_found.png", EMAIL)
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
        print(f"📍 找到模态框内 iframe 坐标: ({coords['cx']}, {coords['cy']})")

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
            ax = coords["cx"] + wi["sx"]
            ay = coords["cy"] + wi["sy"] + bar
            print(f"🖱️ ALTCHA点击复选框 ({ax}, {ay})")
            _xdotool_click(ax, ay)

        try:
            for iframe in sb.find_elements('div.modal.show iframe'):
                try:
                    iframe.click()
                    print("🖱️ SeleniumBase 点击模态框 iframe")
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

        print(f"⚠️ 第 {attempt + 1} 轮未通过，重试...")
        try:
            new_coords = sb.execute_script(_ALTCHA_EXPAND_JS)
            if new_coords:
                coords = new_coords
        except Exception:
            pass

    print("❌ ALTCHA 3 轮均失败")
    return False


def _days_until_expiry(expiry_str: str):
    """计算距到期日的天数（北京时间）。负数表示已过期。返回 int 或 None。"""
    if not expiry_str:
        return None
    try:
        from datetime import datetime, timezone, timedelta
        exp = datetime.strptime(expiry_str.strip()[:10], "%Y-%m-%d").date()
        today = (datetime.now(timezone.utc) + timedelta(hours=8)).date()
        return (exp - today).days
    except Exception:
        return None


def _submit_renew(sb):
    """
    提交续期：
    - ALTCHA 通过后按钮常会自动进入 Verifying，此时不要再点
    - 若仍显示 Renew/Confirm 则点击一次
    - 等待模态框关闭（成功）或超时
    """
    print("🖱️ 处理模态框确认按钮...")

    btn_text = sb.execute_script("""
        (function(){
            var m = document.querySelector('div.modal.show');
            if (!m) return '';
            var bs = m.querySelectorAll('button');
            for (var i = 0; i < bs.length; i++) {
                var t = (bs[i].textContent || '').trim();
                if (t && !/close|cancel|取消/i.test(t)) return t;
            }
            return '';
        })()
    """) or ""
    low = btn_text.lower()

    if "verifying" in low or "%" in btn_text:
        print(f"ℹ️ 按钮已在验证中: [{btn_text}]，等待自动完成（不重复点击）")
    elif any(k in low for k in ("renew", "confirm", "确认", "submit", "ok")):
        print(f"🖱️ 点击确认按钮: [{btn_text}]")
        try:
            btns = sb.find_elements('div.modal.show button')
            for b in btns:
                t = (b.text or "").strip().lower()
                if t and "close" not in t and "cancel" not in t and "取消" not in t:
                    b.click()
                    break
        except Exception as e:
            print(f"⚠️ 点击异常: {e}")
            sb.execute_script("""
                (function(){
                    var m = document.querySelector('div.modal.show');
                    if (!m) return;
                    var bs = m.querySelectorAll('button');
                    for (var i = 0; i < bs.length; i++) {
                        var t = (bs[i].textContent || '').toLowerCase();
                        if (t.includes('close') || t.includes('cancel') || t.includes('取消')) continue;
                        bs[i].click(); return;
                    }
                })()
            """)
    else:
        print(f"ℹ️ 当前按钮状态: [{btn_text or '无'}]，尝试 JS 点击主按钮")
        sb.execute_script("""
            (function(){
                var m = document.querySelector('div.modal.show');
                if (!m) return;
                var bs = m.querySelectorAll('button');
                for (var i = 0; i < bs.length; i++) {
                    var t = (bs[i].textContent || '').toLowerCase();
                    if (t.includes('close') || t.includes('cancel') || t.includes('取消')) continue;
                    bs[i].click(); return;
                }
            })()
        """)

    print("⏳ 等待续期提交完成（模态框关闭）...")
    for i in range(25):
        time.sleep(1)
        try:
            modal_visible = sb.execute_script(
                "return !!(document.querySelector('div.modal.show'));"
            )
            if not modal_visible:
                print(f"✅ 模态框已关闭（耗时 {i+1}s），续期请求已提交")
                return True

            cur = sb.execute_script("""
                (function(){
                    var m = document.querySelector('div.modal.show');
                    if (!m) return '';
                    var bs = m.querySelectorAll('button');
                    for (var i = 0; i < bs.length; i++) {
                        var t = (bs[i].textContent || '').trim();
                        if (t && !/close|cancel|取消/i.test(t)) return t;
                    }
                    return '';
                })()
            """) or ""
            if "verifying" in cur.lower() or "%" in cur:
                if i % 5 == 0:
                    print(f"  …验证中: {cur}")
            elif any(k in cur.lower() for k in ("renew", "confirm", "确认")):
                print(f"🖱️ 按钮恢复，再次点击: [{cur}]")
                try:
                    sb.find_element('div.modal.show button.btn-primary').click()
                except Exception:
                    pass
        except Exception:
            pass

    print("⚠️ 等待超时（模态框未关闭），可能未进入续期窗口或验证失败")
    return False


def _extract_expiry(sb) -> str:
    """从服务器详情页 Service information 区域精确提取 Expiry 日期。"""
    try:
        expiry = sb.execute_script("""
        (function(){
            var labels = document.querySelectorAll('div, span, td, th, label, p, dt, dd');
            for (var i = 0; i < labels.length; i++) {
                var t = (labels[i].textContent || '').trim();
                if (/^Expir(?:y|ation|es)?$/i.test(t) || t === '到期' || t === '到期时间') {
                    var sib = labels[i].nextElementSibling;
                    if (sib) {
                        var m = (sib.textContent || '').match(/(\\d{4}-\\d{2}-\\d{2})/);
                        if (m) return m[1];
                    }
                    var parent = labels[i].parentElement;
                    if (parent) {
                        var m2 = (parent.textContent || '').match(/Expir(?:y|ation|es)?\\s*[:：]?\\s*(\\d{4}-\\d{2}-\\d{2})/i);
                        if (m2) return m2[1];
                    }
                }
            }
            var body = document.body.innerText || '';
            var m = body.match(/Expir(?:y|ation|es)?\\s*[:：]?\\s*(\\d{4}-\\d{2}-\\d{2})/i);
            if (m) return m[1];
            return '';
        })()
        """)
        return (expiry or "").strip()
    except Exception:
        return ""


def _get_modal_or_toast_text(sb) -> str:
    """获取模态框正文或页面 toast/alert 中的有效提示（过滤无关 Warning）。"""
    try:
        text = sb.execute_script("""
        (function(){
            var modal = document.querySelector('div.modal.show .modal-body, div.modal.show');
            if (modal) {
                var t = (modal.innerText || '').trim();
                if (t) return t;
            }
            var alerts = document.querySelectorAll('.toast, .alert, [role="alert"], .notification');
            for (var i = 0; i < alerts.length; i++) {
                var a = (alerts[i].innerText || '').trim();
                if (!a) continue;
                if (/changing the server type/i.test(a)) continue;
                if (/startup command and environment/i.test(a)) continue;
                return a;
            }
            return '';
        })()
        """)
        return (text or "").strip()
    except Exception:
        return ""


def _check_renew_result(sb, expiry_before: str = "", skipped_early: bool = False):
    print("\n📋 检查续期结果...")

    try:
        still_open = sb.execute_script("return !!(document.querySelector('div.modal.show'));")
        if still_open:
            print("ℹ️ 模态框仍打开，尝试关闭...")
            try:
                sb.click('div.modal.show button:contains("Close"), div.modal.show .btn-close, div.modal.show button.btn-secondary', timeout=3)
            except Exception:
                sb.execute_script("""
                    var m = document.querySelector('div.modal.show');
                    if (!m) return;
                    var bs = m.querySelectorAll('button');
                    for (var i = 0; i < bs.length; i++) {
                        if (/close|cancel|取消/i.test(bs[i].textContent || '')) { bs[i].click(); return; }
                    }
                    var x = m.querySelector('.btn-close, [data-bs-dismiss="modal"]');
                    if (x) x.click();
                """)
            time.sleep(2)
    except Exception:
        pass

    time.sleep(2)
    try:
        sb.refresh()
        time.sleep(4)
    except Exception:
        pass

    expiry_after = _extract_expiry(sb)
    if expiry_after:
        print(f"📅 当前到期时间: {expiry_after}")
    else:
        print("ℹ️ 未能解析到期时间")

    tip = _get_modal_or_toast_text(sb)
    if tip:
        tip = tip.replace("\n", " ").strip()
        if len(tip) > 180:
            tip = tip[:180] + "…"
        print(f"📩 页面提示: {tip}")

    screenshot_file = "renew_result.png"
    sb.save_screenshot(screenshot_file)

    days_left = _days_until_expiry(expiry_after or expiry_before)

    success = False
    not_yet = skipped_early
    if expiry_before and expiry_after and expiry_after > expiry_before:
        success = True
    if tip:
        low = tip.lower()
        if "can't renew" in low or "unable" in low or "not available" in low or "too early" in low:
            not_yet = True
        elif any(k in low for k in ("renewed", "success", "extended", "extend the life", "已续期", "成功")):
            success = True

    lines = []
    if tip and not re.search(r"changing the server type|startup command", tip, re.I):
        lines.append(tip)

    ref_expiry = expiry_after or expiry_before
    if ref_expiry:
        lines.append(f"📅 当前到期时间: {ref_expiry}")
        if expiry_before and expiry_after and expiry_after != expiry_before:
            lines.append(f"（续期前: {expiry_before} → 续期后: {expiry_after}）")
        if days_left is not None:
            if days_left > 2:
                from datetime import datetime, timedelta
                exp = datetime.strptime(ref_expiry[:10], "%Y-%m-%d")
                window_start = (exp - timedelta(days=2)).strftime("%Y-%m-%d")
                lines.append(f"⏳ 续期窗口: {window_start} ~ {ref_expiry}（仅此 2 天内可续）")
                lines.append(f"建议 cron 设在 {window_start} 或到期当天")
            elif days_left >= 0:
                lines.append(f"✅ 已进入续期窗口（剩余 {days_left} 天）")
            else:
                lines.append(f"⚠️ 已过期 {abs(days_left)} 天，请尽快续期（宽限约 1 天）")

    detail = "\n".join(lines) if lines else "未检测到明确提示"

    if not_yet or (days_left is not None and days_left > 2 and not success):
        send_tg_message("⏳", "未到续期时间", detail, screenshot_file, EMAIL)
    elif success:
        send_tg_message("✅", "续期成功", detail, screenshot_file, EMAIL)
    else:
        send_tg_message("ℹ️", "续期操作已执行", detail, screenshot_file, EMAIL)


def renew_server(sb):
    print("\n" + "#" * 25)
    print(" 开始自动续期流程")
    print("#" * 25)
    if not _goto_server_detail(sb):
        return

    expiry_before = _extract_expiry(sb)
    if expiry_before:
        print(f"📅 续期前到期时间: {expiry_before}")
        days = _days_until_expiry(expiry_before)
        if days is not None:
            print(f"📆 距到期还有 {days} 天")
            # 官方政策：免费服务器仅到期前 2 天内（含到期日）可续期
            if days > 2:
                from datetime import datetime, timedelta
                exp = datetime.strptime(expiry_before[:10], "%Y-%m-%d")
                window_start = (exp - timedelta(days=2)).strftime("%Y-%m-%d")
                print(f"⏳ 未进入续期窗口（仅 {window_start} ~ {expiry_before} 可续），跳过提交")
                sb.save_screenshot("renew_too_early.png")
                detail = (
                    f"📅 当前到期时间: {expiry_before}\n"
                    f"⏳ 续期窗口: {window_start} ~ {expiry_before}（仅此 2 天内可续）\n"
                    f"建议将 GitHub Actions cron 设在 {window_start} 当天或到期前 1 天"
                )
                send_tg_message("⏳", "未到续期时间", detail, "renew_too_early.png", EMAIL)
                return

    if not _open_renew_modal(sb):
        return
    altcha_ok = _solve_altcha(sb)
    if not altcha_ok:
        print("⚠️ ALTCHA 验证未通过，仍尝试提交 Renew...")
    _submit_renew(sb)
    _check_renew_result(sb, expiry_before=expiry_before)


# ------------------------------------------------------------------
# 控制面板管理
# ------------------------------------------------------------------
def manage_control_panel(sb):
    print("\n" + "#" * 35)
    print(f" 初始化控制面板通信序列: {CONTROL_URL}")
    print("#" * 35)

    if not CONTROL_ID:
        print("❌ 核心异常：系统环境未检测到独立挂载的 CONTROL_ID。")
        send_tg_message("⚠️", "面板登录被安全拦截",
                        "未检测到 `CONTROL_ID`（面板用户名）环境变量。\n已主动跳过控制面板监控，以防账号封禁。",
                        target_email=EMAIL)
        return

    if not CONTROL_PASSWORD:
        print("❌ 核心异常：未检测到任何可用的密码 (CONTROL_PASSWORD 或 PASSWORD 均为空)。")
        return

    print("🌐 请求建立控制面板连接...")
    sb.uc_open_with_reconnect(CONTROL_URL, reconnect_time=8)
    time.sleep(6)

    current_url = sb.get_current_url().lower()

    # 登录
    if "/auth/login" in current_url:
        print(f"📧 注入控制面板凭证 (ID: {CONTROL_ID})...")
        try:
            if sb.is_element_present('input[name="user"]'):
                sb.type('input[name="user"]', CONTROL_ID)
            elif sb.is_element_present('input[name="username"]'):
                sb.type('input[name="username"]', CONTROL_ID)
            elif sb.is_element_present('input[type="text"]'):
                sb.type('input[type="text"]', CONTROL_ID)

            time.sleep(1)
            print("🔑 注入密码...")
            if sb.is_element_present('input[name="password"]'):
                sb.type('input[name="password"]', CONTROL_PASSWORD)
            elif sb.is_element_present('input[type="password"]'):
                sb.type('input[type="password"]', CONTROL_PASSWORD)

            time.sleep(1.5)

            if sb.execute_script(_EXISTS_JS):
                print("🔍 检测到 Cloudflare Turnstile...")
                handle_turnstile(sb)

            print("🖱️ 提交登录...")
            try:
                sb.click('button[type="submit"], button:contains("Login"), button:contains("登录")', timeout=3)
            except Exception:
                sb.press_keys('input[type="password"]', '\n')

            login_success = False
            for i in range(15):
                time.sleep(1)
                if "/auth/login" not in sb.get_current_url().lower():
                    login_success = True
                    print(f"✅ 鉴权成功 (耗时 {i+1} 秒)")
                    break

            if not login_success:
                print("❌ 登录失败，会话未跳转")
                sb.save_screenshot("control_login_fail.png")
                send_tg_message("❌", "面板登录失败",
                                f"独立鉴权遭到拒绝。\n传入 ID: {CONTROL_ID}",
                                "control_login_fail.png", target_email=CONTROL_ID)
                return
        except Exception as e:
            print(f"⚠️ 面板登录异常: {e}")
            return

    # 确保进入服务器详情页
    print("⏳ 等待面板加载...")
    time.sleep(6)
    current_url = sb.get_current_url().lower()

    if "/server/" not in current_url:
        print("🔍 当前在列表页，尝试进入服务器控制台...")
        try:
            if sb.is_element_present('a[href*="/server/"]'):
                sb.click('a[href*="/server/"]', timeout=8)
            else:
                sb.click('*:contains("Manage server")', timeout=8)
            print("✅ 已进入服务器控制台")
            time.sleep(6)
        except Exception as e:
            print(f"⚠️ 无法进入服务器详情页: {e}")
    else:
        print("✅ 已在服务器控制台页面")

    # 状态检测 + 操作（只执行一次）
    print("🔍 扫描服务器运行状态...")
    time.sleep(3)
    page_text = sb.get_text("body").lower()
    screenshot_file = "server_status.png"
    sb.save_screenshot(screenshot_file)

    is_offline = "offline" in page_text or "离线" in page_text

    if is_offline:
        print("💤 服务器处于 Offline 状态 → 执行开机")
        try:
            sb.click('button:contains("Start"), button:contains("启动"), button[data-action="start"]', timeout=5)
            print("✅ 开机指令已发送")
            time.sleep(3)
            sb.save_screenshot("server_started.png")
            send_tg_message("🚀", "服务器实例唤醒",
                            f"探针检测到实例离线，已执行强制开机操作。\n节点面板: {CONTROL_URL}",
                            "server_started.png", target_email=CONTROL_ID)
        except Exception as e:
            print(f"⚠️ 未能找到 Start 按钮: {e}")
            send_tg_message("⚠️", "唤醒序列失败",
                            "在控制面板内未能解析出 Start/启动 组件节点",
                            screenshot_file, target_email=CONTROL_ID)
    else:
        # 在线时不执行重启，仅记录状态，避免不必要的中断
        print("🟢 服务器处于 Online 状态 → 跳过重启（仅离线时才启动）")
        sb.save_screenshot(screenshot_file)


# ------------------------------------------------------------------
# 主入口
# ------------------------------------------------------------------
def main():
    print("#" * 25)
    print(" katabump 自动登录续期与管理")
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
            print(f"📍 当前出口IP: {sb.get_text('body')}")
        except Exception:
            pass

        if login(sb):
            renew_server(sb)
            manage_control_panel(sb)
            print("\n✅ 全部流程执行完毕")
        else:
            print("\n❌ 登录失败，终止后续操作。")


if __name__ == "__main__":
    main()
