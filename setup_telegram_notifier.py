# aios/setup_telegram_notifier.py - Telegram Notifier 配置助手
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AIOS_ROOT = Path(__file__).parent
sys.path.insert(0, str(AIOS_ROOT))

print("=" * 60)
print("Telegram Notifier 配置助手")
print("=" * 60)

print("\n📝 步骤1：创建 Telegram Bot")
print("   1. 在 Telegram 中找到 @BotFather")
print("   2. 发送 /newbot 创建新 Bot")
print("   3. 按提示设置 Bot 名称")
print("   4. 获取 Bot Token")

bot_token = input("\n请输入 Bot Token: ").strip()

print("\n📝 步骤2：获取 Chat ID")
print("   方法1: 在 Telegram 中找到 @userinfobot，发送消息获取 ID")
print("   方法2: 先给你的 Bot 发送一条消息，然后访问：")
print(f"   https://api.telegram.org/bot{bot_token}/getUpdates")

chat_id = input("\n请输入 Chat ID: ").strip()

print("\n📝 步骤3：选择通知级别")
print("   info: 所有通知")
print("   warn: 警告及以上（推荐）")
print("   error: 错误及以上")
print("   critical: 仅严重错误")

min_severity = input("\n请选择级别 [warn]: ").strip() or "warn"

print("\n📝 步骤4：设置速率限制")
rate_limit = input("每次通知间隔（秒）[5]: ").strip() or "5"

# 生成配置
config = f"""enabled: true

# Telegram Bot 配置
bot_token: "{bot_token}"
chat_id: "{chat_id}"

# 通知级别
min_severity: {min_severity}

# 速率限制（秒）
rate_limit: {rate_limit}
"""

# 写入配置文件
config_file = AIOS_ROOT / "plugins" / "builtin" / "notifier_telegram" / "config.yaml"
config_file.write_text(config, encoding="utf-8")

print("\n" + "=" * 60)
print("✅ 配置完成！")
print("=" * 60)
print(f"\n配置文件: {config_file}")

# 测试连接
print("\n🔍 测试连接...")
try:
    import requests
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    bot_info = response.json()
    
    if bot_info.get("ok"):
        bot_name = bot_info["result"]["username"]
        print(f"✅ Bot 连接成功: @{bot_name}")
    else:
        print("❌ Bot 连接失败")
except Exception as e:
    print(f"❌ 连接测试失败: {e}")

# 发送测试消息
print("\n📤 发送测试消息...")
try:
    import requests
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": "🎉 AIOS Telegram Notifier 配置成功！",
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=data, timeout=5)
    response.raise_for_status()
    print("✅ 测试消息已发送，请检查 Telegram")
except Exception as e:
    print(f"❌ 发送失败: {e}")
    print("\n💡 提示: 请先给 Bot 发送一条消息，然后重试")

print("\n" + "=" * 60)
print("下一步:")
print("  1. 加载插件: python __main__.py plugin load builtin/notifier_telegram")
print("  2. 测试通知: python -X utf8 demo_quick.py")
print("=" * 60)
