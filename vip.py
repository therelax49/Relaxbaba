import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# Ayarlar
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID  = 8447839505
API_URL   = "https://waxerweaslue.com/bot/vip_bot.php"

# Menü Tasarımları
def ana_menu():
    keyboard = [
        [InlineKeyboardButton("👤 Hesap Oluştur", callback_data="islem_create")],
        [InlineKeyboardButton("🚫 Kullanıcıyı Banla", callback_data="islem_ban")],
        [InlineKeyboardButton("⚡ Admin Yetkisi Ver", callback_data="islem_admin")],
        [InlineKeyboardButton("🗑️ Hesabı Tamamen Sil", callback_data="islem_delete")]
    ]
    return InlineKeyboardMarkup(keyboard)

def vip_paketleri():
    keyboard = [
        [InlineKeyboardButton("🕒 1 Günlük", callback_data="vip_1"), InlineKeyboardButton("📅 Haftalık", callback_data="vip_2")],
        [InlineKeyboardButton("🗓️ 1 Aylık", callback_data="vip_3"), InlineKeyboardButton("📊 3 Aylık", callback_data="vip_4")],
        [InlineKeyboardButton("♾️ Sınırsız Paket", callback_data="vip_5")],
        [InlineKeyboardButton("❌ İşlemi İptal Et", callback_data="iptal")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Komutlar
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⚠️ <b>Yetkisiz Erişim!</b>\nBu panel sadece yöneticiye özeldir.", parse_mode="HTML")
        return
    
    await update.message.reply_text(
        "🚀 <b>RELAX BABA VIP PANELİ AKTİF</b>\n\nYapmak istediğiniz işlemi aşağıdan seçin:",
        reply_markup=ana_menu(),
        parse_mode="HTML"
    )

async def buton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "iptal":
        context.user_data.clear()
        await q.edit_message_text("✅ İşlem iptal edildi. Ana menüye dönüldü.", reply_markup=ana_menu())

    elif q.data.startswith("islem_"):
        islem = q.data.split("_")[1]
        context.user_data["islem"] = islem
        
        islem_isimleri = {"create": "Hesap Oluşturma", "ban": "Banlama", "admin": "Admin Yapma", "delete": "Hesap Silme"}
        await q.edit_message_text(f"📝 <b>{islem_isimleri[islem]}</b>\nLütfen hedef kullanıcı adını yazın:", parse_mode="HTML")

    elif q.data.startswith("vip_"):
        if context.user_data.get("islem") != "create":
            await q.edit_message_text("⚠️ Önce bir işlem seçmelisiniz!", reply_markup=ana_menu())
            return

        tip = int(q.data.split("_")[1])
        username = context.user_data["username"]

        payload = {"action": "create_account", "username": username, "type": tip}

        try:
            r = requests.post(API_URL, json=payload, timeout=10)
            res = r.json()
        except:
            await q.edit_message_text("❌ <b>Sunucu Hatası!</b>\nAPI bağlantısı kurulamadı.", reply_markup=ana_menu(), parse_mode="HTML")
            return

        if res.get("success"):
            await q.edit_message_text(
                f"✅ <b>HESAP BAŞARIYLA OLUŞTURULDU!</b>\n\n"
                f"👤 <b>Kullanıcı:</b> <code>{res['username']}</code>\n"
                f"📧 <b>E-posta:</b> <code>{res['email']}</code>\n"
                f"🔑 <b>Şifre:</b> <code>{res['sifre']}</code>\n"
                f"💎 <b>Paket:</b> {res['paket']}\n"
                f"📅 <b>Bitiş:</b> {res['bitis']}\n\n"
                f"🌐 <b>Giriş:</b> <a href='https://waxerweaslue.com'>waxerweaslue.com</a>",
                parse_mode="HTML",
                reply_markup=ana_menu()
            )
        else:
            await q.edit_message_text(f"❌ <b>Hata:</b> {res.get('hata')}", reply_markup=ana_menu(), parse_mode="HTML")

        context.user_data.clear()

async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return

    text = update.message.text.strip()
    islem = context.user_data.get("islem")

    if not islem:
        await update.message.reply_text("👋 <b>Hoş geldin!</b> Lütfen önce menüden bir işlem seçin:", reply_markup=ana_menu(), parse_mode="HTML")
        return

    if len(text) < 3:
        await update.message.reply_text("⚠️ Kullanıcı adı çok kısa! Lütfen geçerli bir isim yazın.")
        return

    if islem == "create":
        context.user_data["username"] = text
        await update.message.reply_text(
            f"👤 Kullanıcı: <b>{text}</b>\n💎 Lütfen VIP süresini seçin:", 
            parse_mode="HTML", 
            reply_markup=vip_paketleri()
        )

    else:
        islem_map = {"ban": "ban_user", "admin": "make_admin", "delete": "delete_user"}
        payload = {"action": islem_map[islem], "username": text}

        try:
            r = requests.post(API_URL, json=payload, timeout=10)
            res = r.json()
        except:
            await update.message.reply_text("❌ Sunucu bağlantı hatası!")
            return

        emojiler = {"ban": "🚫", "admin": "⚡", "delete": "🗑️"}
        mesajlar = {
            "ban": f"🚫 <b>@{text}</b> kullanıcısı banlandı.",
            "admin": f"⚡ <b>@{text}</b> artık bir ADMIN (Level 6).",
            "delete": f"🗑️ <b>@{text}</b> hesabı kalıcı olarak silindi."
        }
        await update.message.reply_text(mesajlar[islem], reply_markup=ana_menu(), parse_mode="HTML")
        context.user_data.clear()

# Botu Başlatma
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("HATA: BOT_TOKEN bulunamadı! Railway Variables kısmına ekleyin.")
    else:
        app = Application.builder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(buton))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj))

        print("--- RELAX BABA BOT AKTİF ---")
        app.run_polling()