import os
import sys
import requests
import datetime
from playwright.sync_api import sync_playwright, TimeoutError

def get_beijing_time():
    """获取格式化的当前北京时间 (UTC+8)"""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    beijing_time = utc_now + datetime.timedelta(hours=8)
    return beijing_time.strftime("%Y-%m-%d %H:%M:%S")

def update_readme_time(status_text):
    """自动寻找 README.md 中的占位符并更新运行时间和状态"""
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        print("未找到 README.md 文件，跳过时间更新。")
        return
        
    current_time = get_beijing_time()
    
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    start_tag = ""
    end_tag = ""
    
    if start_tag in content and end_tag in content:
        start_idx = content.find(start_tag) + len(start_tag)
        end_idx = content.find(end_tag)
        
        # 组装写入 README 的新文本
        new_text = f"\n🕒 最近运行时间：<code>{current_time}</code> ({status_text})\n"
        # 拼接新内容
        new_content = content[:start_idx] + new_text + content[end_idx:]
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("README.md 运行时间已成功在本地更新。")
    else:
        print("未在 README.md 中找到指定的时间占位符标签，请检查 README 配置。")

def send_telegram_message(message, image_path=None):
    """发送 Telegram 推送消息（支持可选的图片截图）"""
    bot_token = os.getenv('TG_BOT_TOKEN')
    chat_id = os.getenv('TG_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("提示: 未配置 TG_BOT_TOKEN 或 TG_CHAT_ID，跳过 Telegram 推送。")
        return

    try:
        if image_path and os.path.exists(image_path):
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            data = {"chat_id": chat_id, "caption": message, "parse_mode": "HTML"}
            with open(image_path, "rb") as photo:
                response = requests.post(url, data=data, files={"photo": photo}, timeout=20)
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
            response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("Telegram 推送发送成功！")
        else:
            print(f"Telegram 推送失败，状态码: {response.status_code}, 详情: {response.text}")
    except Exception as e:
        print(f"请求 Telegram API 时发生异常: {e}")

def run(playwright):
    username = os.getenv('VORTEXA_USER')
    password = os.getenv('VORTEXA_PASS')
    
    current_time = get_beijing_time()

    if not username or not password:
        msg = f"❌ <b>执行失败</b>\n未找到 VORTEXA_USER 或 VORTEXA_PASS 环境变量。\n🕒 时间: <code>{current_time}</code>"
        print(msg)
        send_telegram_message(msg)
        update_readme_time("❌ 失败：配置缺失")
        sys.exit(1)

    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={'width': 1280, 'height': 720},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    try:
        print("正在访问目标面板...")
        page.goto("https://www.vortexa.cloud/dashboard", wait_until="networkidle")

        print("正在输入凭据...")
        page.fill('input[type="email"]', username)
        page.fill('input[type="password"]', password)

        print("提交登录...")
        page.click('button[type="submit"]')

        page.wait_for_timeout(5000)
        
        screenshot_path = "success_screenshot.png"
        page.screenshot(path=screenshot_path)
        
        current_time = get_beijing_time()
        success_msg = f"✅ <b>Vortexa 自动登录成功</b>\n任务已按时顺利执行完毕。\n🕒 时间: <code>{current_time}</code>"
        print(success_msg)
        
        # 发送 Tg 并同步更新 README 状态
        send_telegram_message(success_msg, image_path=screenshot_path)
        update_readme_time("✅ 成功")

    except TimeoutError:
        screenshot_path = "timeout_screenshot.png"
        page.screenshot(path=screenshot_path)

        current_time = get_beijing_time()
        error_msg = f"⚠️ <b>Vortexa 自动登录异常</b>\n页面加载或元素定位超时。\n🕒 时间: <code>{current_time}</code>"
        print(error_msg)
        
        send_telegram_message(error_msg, image_path=screenshot_path)
        update_readme_time("⚠️ 异常")
        
    except Exception as e:
        current_time = get_beijing_time()
        error_msg = f"❌ <b>Vortexa 自动登录失败</b>\n发生未知代码异常:\n<code>{str(e)}</code>\n🕒 时间: <code>{current_time}</code>"
        print(error_msg)
        
        send_telegram_message(error_msg)
        update_readme_time("❌ 失败")
        
    finally:
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
