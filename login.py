import os
import sys
from playwright.sync_api import sync_playwright, TimeoutError

def run(playwright):
    # 从环境变量获取账号密码
    username = os.getenv('VORTEXA_USER')
    password = os.getenv('VORTEXA_PASS')

    if not username or not password:
        print("错误: 未找到 VORTEXA_USER 或 VORTEXA_PASS 环境变量。")
        sys.exit(1)

    # 启动 Chromium，headless=True 表示无界面后台运行
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        # 模拟常规浏览器 User-Agent，降低被识别为 Bot 的概率
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    try:
        print("正在访问目标面板: https://www.vortexa.cloud/dashboard")
        # 访问网页，等待网络空闲
        page.goto("https://www.vortexa.cloud/dashboard", wait_until="networkidle")

        print("正在输入凭据...")
        # 注意：这里的 'input[type="email"]' 和 'input[type="password"]' 
        # 需要你通过浏览器的 F12 开发者工具，检查实际网页元素的属性来替换
        page.fill('input[type="email"]', username)
        page.fill('input[type="password"]', password)

        print("提交登录...")
        # 替换为实际登录按钮的定位器
        page.click('button[type="submit"]')

        # 等待页面跳转或特定元素出现，确认登录成功
        # page.wait_for_selector('text="Welcome"', timeout=10000)
        
        # 简单等待 5 秒让后端处理请求
        page.wait_for_timeout(5000)
        print("操作执行完毕。")

    except TimeoutError:
        print("页面加载或元素定位超时，可能遇到了验证码或网络波动。")
    except Exception as e:
        print(f"执行过程中发生异常: {e}")
    finally:
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
