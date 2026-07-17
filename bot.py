import discord
import os
import logging
import asyncio
from flask import Flask
from threading import Thread

# ============ إعداد اللوق ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
log = logging.getLogger("discord_voice_selfbot")

# ============ إعدادات من متغيرات البيئة ============
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
VOICE_CHANNEL_ID = os.environ.get('VOICE_CHANNEL_ID')
GUILD_ID = os.environ.get('GUILD_ID')

SELF_MUTE = os.environ.get('SELF_MUTE', 'false').lower() == 'true'
SELF_DEAF = os.environ.get('SELF_DEAF', 'false').lower() == 'true'

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN مفقود! أضفه بـ Environment Variables على Render.")
if not VOICE_CHANNEL_ID:
    raise RuntimeError("VOICE_CHANNEL_ID مفقود! أضفه بـ Environment Variables على Render.")

VOICE_CHANNEL_ID = int(VOICE_CHANNEL_ID)
GUILD_ID = int(GUILD_ID) if GUILD_ID else None

# ============ Flask Keep-Alive ============
app = Flask('')
bot_status = {
    "connected": False,
    "channel": None,
    "reconnects": 0,
    "user": None,
    "guild": None
}

@app.route('/')
def home():
    state = "متصل ✅" if bot_status["connected"] else "غير متصل ❌"
    return {
        "status": state,
        "user": bot_status["user"],
        "guild": bot_status["guild"],
        "channel": bot_status["channel"],
        "reconnect_count": bot_status["reconnects"],
        "self_mute": SELF_MUTE,
        "self_deaf": SELF_DEAF,
    }

@app.route('/health')
def health():
    return {"status": "OK", "connected": bot_status["connected"]}, 200

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

def keep_alive():
    t = Thread(target=run_web, daemon=True)
    t.start()

# ============ إعداد البوت (Selfbot) ============
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True

client = discord.Client(intents=intents)

RECONNECT_DELAY = 10
MAX_RECONNECT_DELAY = 120
MAX_RECONNECT_ATTEMPTS = 10


async def join_voice_channel():
    delay = RECONNECT_DELAY
    attempts = 0

    while True:
        await asyncio.sleep(2)

        channel = client.get_channel(VOICE_CHANNEL_ID)

        if channel is None:
            log.error("لم يتم العثور على الروم الصوتي! تأكد من VOICE_CHANNEL_ID")
            await asyncio.sleep(delay)
            continue

        existing = discord.utils.get(client.voice_clients, guild=channel.guild)
        if existing and existing.is_connected():
            if existing.channel.id == channel.id:
                bot_status["connected"] = True
                bot_status["channel"] = channel.name
                bot_status["guild"] = channel.guild.name
                await asyncio.sleep(15)
                continue
            else:
                log.info("موجود بروم مختلف، جاري قطع الاتصال...")
                await existing.disconnect(force=True)
                await asyncio.sleep(3)

        try:
            log.info(f"محاولة الاتصال بالروم: {channel.name} (Mute: {SELF_MUTE}, Deaf: {SELF_DEAF})")

            vc = await channel.connect(
                reconnect=True,
                timeout=30,
                self_mute=SELF_MUTE,
                self_deaf=SELF_DEAF
            )

            bot_status["connected"] = True
            bot_status["channel"] = channel.name
            bot_status["guild"] = channel.guild.name
            log.info(f"✅ تم الانضمام للروم الصوتي: {channel.name}")

            delay = RECONNECT_DELAY
            attempts = 0

            while vc.is_connected():
                await asyncio.sleep(10)

            log.warning("⚠️ انقطع الاتصال بالروم الصوتي، جاري إعادة المحاولة...")
            bot_status["connected"] = False
            bot_status["reconnects"] += 1

        except discord.errors.ClientException as e:
            log.error(f"خطأ عميل: {e}")
            bot_status["connected"] = False
            await asyncio.sleep(delay)

        except Exception as e:
            log.error(f"❌ فشل الاتصال: {e}")
            bot_status["connected"] = False
            bot_status["reconnects"] += 1
            attempts += 1

            if attempts >= MAX_RECONNECT_ATTEMPTS:
                log.error(f"🚫 وصلنا للحد الأقصى ({MAX_RECONNECT_ATTEMPTS}) محاولات. انتظار 5 دقائق...")
                await asyncio.sleep(300)
                attempts = 0
                delay = RECONNECT_DELAY
            else:
                await asyncio.sleep(delay)
                delay = min(delay * 2, MAX_RECONNECT_DELAY)


@client.event
async def on_ready():
    log.info(f"✅ تم تسجيل الدخول باسم {client.user}")
    bot_status["user"] = str(client.user)
    client.loop.create_task(join_voice_channel())


@client.event
async def on_disconnect():
    log.warning("🔌 انقطع اتصال البوت بديسكورد")
    bot_status["connected"] = False


@client.event
async def on_resumed():
    log.info("🔄 تم استئناف الاتصال بديسكورد")


@client.event
async def on_voice_state_update(member, before, after):
    if member.id == client.user.id:
        if after.channel is None and before.channel is not None:
            log.warning("👤 تم طرد الحساب من الروم الصوتي!")
            bot_status["connected"] = False
        elif after.channel is not None:
            log.info(f"🎙️ حالة الصوت: {after.channel.name} | Mute: {after.self_mute} | Deaf: {after.self_deaf}")


def main():
    keep_alive()
    log.info("🚀 بدء تشغيل خادم Flask + السيلف بوت...")
    log.info(f"🔧 الإعدادات: Mute={SELF_MUTE}, Deaf={SELF_DEAF}")
    client.run(DISCORD_TOKEN, reconnect=True)


if __name__ == "__main__":
    main()
