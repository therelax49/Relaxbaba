import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID  = 8447839505
API_URL   = "https://waxerweaslue.com/bot/vip_bot.php"

app = Application.builder().token(BOT_TOKEN).build()

def ana_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Hesap Oluştur", callback_data="islem_create")],
        [InlineKeyboardButton("Banla", callback_data="islem_ban")],
        [InlineKeyboardButton("Admin Yap", callback_data="islem_admin")],
        [InlineKeyboardButton("Hesabı Sil", callback_data="islem_delete")]
    ])

def vip_paketleri():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1 Günlük", callback_data="vip_1")],
        [InlineKeyboardButton("Haftalık",  callback_data="vip_2")],
        [InlineKeyboardButton("1 Aylık",   callback_data="vip_3")],
        [InlineKeyboardButton("3 Aylık",   callback_data="vip_4")],
        [InlineKeyboardButton("Sınırsız",  callback_data="vip_5")],
        [InlineKeyboardButton("İptal",     callback_data="iptal")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Yetkisiz erişim.")
        return
    await update.message.reply_text(
        "ADMIN PANELİ AKTİF\n\nİşlem seç:",
        reply_markup=ana_menu()
    )

async def buton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "iptal":
        context.user_data.clear()
        await q.edit_message_text("İptal edildi.", reply_markup=ana_menu())

    elif q.data.startswith("islem_"):
        islem = q.data.split("_")[1]
        context.user_data["islem"] = islem
        await q.edit_message_text(f"{islem.upper()} için kullanıcı adını gir:")

    elif q.data.startswith("vip_"):
        if context.user_data.get("islem") != "create":
            await q.edit_message_text("Önce işlem seç!")
            return

        tip = int(q.data.split("_")[1])
        username = context.user_data["username"]

        payload = {
            "action": "create_account",
            "username": username,
            "type": tip
        }

        try:
            r = requests.post(API_URL, json=payload, timeout=10)
            res = r.json()
        except:
            await q.edit_message_text("Sunucu hatası!", reply_markup=ana_menu())
            return

        if res.get("success"):
            await q.edit_message_text(
                f"HESAP OLUŞTURULDU!\n\n"
                f"Kullanıcı: <b>{res['username']}</b>\n"
                f"E-posta: <code>{res['email']}</code>\n"
                f"Şifre: <code>{res['sifre']}</code>\n"
                f"Paket: <b>{res['paket']}</b>\n"
                f"Bitiş: <b>{res['bitis']}</b>\n\n"
                f"Siteye Giriş Yap: https://relaxvip.shop",
                parse_mode="HTML",
                reply_markup=ana_menu()
            )
        else:
            await q.edit_message_text(f"Hata: {res.get('hata')}", reply_markup=ana_menu())

        context.user_data.clear()

async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return

    text = update.message.text.strip()
    islem = context.user_data.get("islem")

    if not islem:
        await update.message.reply_text("Önce menüden işlem seç!", reply_markup=ana_menu())
        return

    if len(text) < 3:
        await update.message.reply_text("Kullanıcı adı en az 3 karakter olmalı!")
        return

    if islem == "create":
        context.user_data["username"] = text
        await update.message.reply_text(f"Kullanıcı: <b>{text}</b>\nPaket seç:", parse_mode="HTML", reply_markup=vip_paketleri())

    else:
        payload = {
            "action": {
                "ban": "ban_user",
                "admin": "make_admin",
                "delete": "delete_user"
            }[islem],
            "username": text
        }

        try:
            r = requests.post(API_URL, json=payload, timeout=10)
            res = r.json()
        except:
            await update.message.reply_text("Sunucu hatası!")
            return

        mesajlar = {
            "ban": f"@{text} banlandı",
            "admin": f"@{text} artık ADMIN (level 6)",
            "delete": f"@{text} tamamen silindi"
        }
        await update.message.reply_text(mesajlar[islem], reply_markup=ana_menu())
        context.user_data.clear()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buton))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

print("relax baba number one")
app.run_polling()