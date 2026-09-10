import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import sqlite3
from datetime import datetime

# ================== تنظیمات از Environment Variables ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN تنظیم نشده است!")

# ================== پلن‌ها ==================
PLANS = {
    "blue_2m": {"name": "آبی ۲ ماهه - ۲۰۰ گیگ", "price": "۱۵۰ تومان", "category": "آبی"},
    "blue_3m": {"name": "آبی ۳ ماهه - ۳۰۰ گیگ", "price": "۱۸۰ تومان", "category": "آبی"},
    "blue_5m": {"name": "آبی ۵ ماهه - ۵۰۰ گیگ", "price": "۳۰۰ تومان", "category": "آبی"},
    "blue_10m": {"name": "آبی ۱۰ ماهه - ۱۰۰۰ گیگ", "price": "۵۰۰ تومان", "category": "آبی"},
    "red_1m": {"name": "قرمز ۱ ماهه - نامحدود", "price": "۱۷۰ تومان", "category": "قرمز"},
    "red_3m": {"name": "قرمز ۳ ماهه - نامحدود", "price": "۳۹۰ تومان", "category": "قرمز"},
    "red_10m": {"name": "قرمز ۱۰ ماهه - نامحدود", "price": "۷۰۰ تومان", "category": "قرمز"},
    "green_1y": {"name": "سبز یکساله - ۵۰۰۰ گیگ", "price": "۱۲۰۰ تومان", "category": "سبز"},
}

# ================== دیتابیس ==================
DB_PATH = "/app/data/vpn_bot.db"   # برای Volume در Railway

def init_db():
    os.makedirs("/app/data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  full_name TEXT,
                  plan_id TEXT,
                  plan_name TEXT,
                  price TEXT,
                  status TEXT DEFAULT 'pending',
                  created_at TEXT)''')
    conn.commit()
    conn.close()

def save_order(user_id, username, full_name, plan_id, plan_name, price):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO orders (user_id, username, full_name, plan_id, plan_name, price, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (user_id, username, full_name, plan_id, plan_name, price, datetime.now().strftime("%Y-%m-%d %H:%M")))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

# ================== هندلرها ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"""سلام {user.first_name} عزیز 👋
به ربات **SpongeBob VPN** خوش اومدی 🧽⚡
ما ارائه‌دهنده سرویس‌های پرسرعت و پایدار V2Ray هستیم.
🔹 سرعت بالا
🔹 امنیت قوی
🔹 مناسب تمام دستگاه‌ها
برای مشاهده پلن‌ها و خرید، روی دکمه زیر بزن:"""
    keyboard = [[InlineKeyboardButton("🛒 برای خرید اینجا بزنید", callback_data="show_plans")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = """📋 **لیست پلن‌های موجود:**
🔵 **حجم و مدت آبی**
🔴 **حجم و مدت قرمز (نامحدود)**
🟢 **حجم و مدت سبز**
یکی از پلن‌های زیر را انتخاب کنید:"""
    keyboard = [
        [InlineKeyboardButton("🔵 آبی ۲ ماهه | ۲۰۰ گیگ | ۱۵۰ ت", callback_data="plan_blue_2m")],
        [InlineKeyboardButton("🔵 آبی ۳ ماهه | ۳۰۰ گیگ | ۱۸۰ ت", callback_data="plan_blue_3m")],
        [InlineKeyboardButton("🔵 آبی ۵ ماهه | ۵۰۰ گیگ | ۳۰۰ ت", callback_data="plan_blue_5m")],
        [InlineKeyboardButton("🔵 آبی ۱۰ ماهه | ۱۰۰۰ گیگ | ۵۰۰ ت", callback_data="plan_blue_10m")],
        [InlineKeyboardButton("🔴 قرمز ۱ ماهه | نامحدود | ۱۷۰ ت", callback_data="plan_red_1m")],
        [InlineKeyboardButton("🔴 قرمز ۳ ماهه | نامحدود | ۳۹۰ ت", callback_data="plan_red_3m")],
        [InlineKeyboardButton("🔴 قرمز ۱۰ ماهه | نامحدود | ۷۰۰ ت", callback_data="plan_red_10m")],
        [InlineKeyboardButton("🟢 سبز یکساله | ۵۰۰۰ گیگ | ۱۲۰۰ ت", callback_data="plan_green_1y")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan_id = query.data.replace("plan_", "")
    plan = PLANS.get(plan_id)
    if not plan:
        await query.edit_message_text("❌ پلن نامعتبر است.")
        return
    user = query.from_user
    order_id = save_order(
        user_id=user.id,
        username=user.username or "-",
        full_name=user.full_name,
        plan_id=plan_id,
        plan_name=plan["name"],
        price=plan["price"]
    )
    user_text = f"""✅ سفارش شما با موفقیت ثبت شد.
📦 پلن انتخابی: **{plan['name']}**
💰 قیمت: **{plan['price']}**
⏳ پس از تأیید ادمین، شماره کارت برای شما ارسال خواهد شد.
لطفاً منتظر بمانید."""
    await query.edit_message_text(user_text, parse_mode="Markdown")

    admin_text = f"""🆕 **سفارش جدید ثبت شد!**
🆔 شماره سفارش: `{order_id}`
👤 کاربر: [{user.full_name}](tg://user?id={user.id})
🔗 یوزرنیم: @{user.username or 'ندارد'}
🆔 آیدی: `{user.id}`
📦 پلن: **{plan['name']}**
💰 قیمت: **{plan['price']}**
🕒 زمان: {datetime.now().strftime("%Y-%m-%d %H:%M")}
لطفاً کاربر را بررسی کرده و در صورت تأیید، شماره کارت را برایش ارسال کنید."""
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"خطا در ارسال به ادمین: {e}")

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, full_name, username, plan_name, price, created_at FROM orders WHERE status='pending' ORDER BY id DESC LIMIT 15")
    rows = c.fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("هیچ سفارش در انتظاری وجود ندارد.")
        return
    text = "📋 **آخرین سفارش‌های در انتظار:**\n\n"
    for row in rows:
        text += f"🆔 `{row[0]}` | {row[1]} | @{row[2] or '-'} | {row[3]} | {row[4]} | {row[5]}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("orders", admin_orders))
    app.add_handler(CallbackQueryHandler(show_plans, pattern="^show_plans$"))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    app.add_handler(CallbackQueryHandler(select_plan, pattern="^plan_"))
    print("ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()