# Discord Voice Selfbot

بوت يتصل بحساب Discord ويبقيه في روم صوتي باستمرار، مع إعادة الاتصال التلقائي عند الانقطاع.

## المكدس التقني
- Python 3.11
- discord.py-self (مكتبة selfbot)
- Flask (خادم keep-alive)

## الاستضافة
هذا المشروع مُعد للنشر على **Render** كـ Web Service.

## متغيرات البيئة المطلوبة
| المتغير | الوصف | مطلوب |
|---|---|---|
| `DISCORD_TOKEN` | توكن حساب Discord | ✅ |
| `VOICE_CHANNEL_ID` | ID الروم الصوتي | ✅ |
| `GUILD_ID` | ID السيرفر | اختياري |
| `SELF_MUTE` | صامت (true/false) | اختياري (افتراضي: false) |
| `SELF_DEAF` | صم (true/false) | اختياري (افتراضي: false) |

## إعدادات Render الموصى بها
- **Port:** 10000
- **Health Check Path:** /health
- **Build Command:** `pip install --no-cache-dir -r requirements.txt`
- **Start Command:** `python bot.py`

## User preferences
- اللغة: العربية
