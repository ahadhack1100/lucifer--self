import asyncio
import json
import os
import re

from datetime import datetime

from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError
)

from telethon.tl.functions.account import UpdateProfileRequest


from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)


# ======================
# CONFIG
# ======================

API_ID = 37527867
API_HASH = "9b95b5e4afc72c1969e9fb08553b33dc"

BOT_TOKEN = "8553182461:AAFCVhK4xk8CVo3R2ZvuwZgBQJBk27GMIQw"

ADMIN_ID = 1903403132

DATA_FILE = "users.json"


# ======================
# DATABASE
# ======================

if os.path.exists(DATA_FILE):

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        users = json.load(f)

else:

    users = {}


def save():

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            users,
            f,
            ensure_ascii=False,
            indent=4
        )


# ======================
# CLIENTS
# ======================

clients = {}

clock_tasks = {}


# ======================
# MAIN MENU
# ======================

def menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🔐 اتصال اکانت",
                callback_data="login"
            )
        ],

        [
            InlineKeyboardButton(
                "🕒 مدیریت ساعت",
                callback_data="clock_menu"
            )
        ],

        [
            InlineKeyboardButton(
                "👤 درخواست عضویت",
                callback_data="request_access"
            )
        ]

    ])



# ======================
# CLOCK MENU
# ======================

def clock_menu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "⚡ فعال کردن ساعت",
                callback_data="clock_on"
            )
        ],

        [
            InlineKeyboardButton(
                "🌙 خاموش کردن ساعت",
                callback_data="clock_off"
            )
        ],

        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back"
            )
        ]

    ])



# ======================
# ADMIN APPROVE MENU
# ======================

def approve_menu(user_id):

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "✅ تایید",
                callback_data=f"approve_{user_id}"
            ),

            InlineKeyboardButton(
                "❌ رد",
                callback_data=f"reject_{user_id}"
            )
        ]

    ])
# ======================
# START
# ======================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = str(
        update.message.from_user.id
    )

    if user_id not in users:

        users[user_id] = {
            "approved": False,
            "login": False,
            "step": None,
            "clock": "off"
        }

        save()


    await update.message.reply_text(

        "🔥 Lucifer | self\n\n"

        "━━━━━━━━━━━━━━\n"
        "⚡ پنل مدیریت شخصی\n"
        "🕒 ساعت هوشمند پروفایل\n"
        "🔐 اتصال امن اکانت\n"
        "━━━━━━━━━━━━━━\n\n"

        "وضعیت دسترسی را از منو بررسی کنید.",

        reply_markup=menu()

    )



# ======================
# ACCESS REQUEST
# ======================

async def request_access(
    update,
    context
):

    query = update.callback_query

    await query.answer()


    user_id = str(
        query.from_user.id
    )


    if user_id not in users:

        users[user_id] = {
            "approved": False,
            "login": False,
            "step": None,
            "clock": "off"
        }



    if users[user_id].get(
        "approved"
    ):

        await query.edit_message_text(

            "✅ شما قبلاً تایید شده‌اید.",

            reply_markup=menu()

        )

        return



    if users[user_id].get(
        "pending"
    ):

        await query.edit_message_text(

            "⏳ درخواست شما قبلاً ارسال شده.\n"
            "منتظر تایید مدیریت باشید.",

            reply_markup=menu()

        )

        return



    users[user_id]["pending"] = True

    save()



    await query.edit_message_text(

        "📨 درخواست عضویت ارسال شد.\n\n"
        "⏳ بعد از تایید مدیریت می‌توانید استفاده کنید.",

        reply_markup=menu()

    )



    await context.bot.send_message(

        ADMIN_ID,

        "🔔 درخواست عضویت جدید\n\n"

        f"👤 User ID:\n"
        f"{user_id}\n\n"

        "آیا اجازه دسترسی داده شود؟",

        reply_markup=approve_menu(
            user_id
        )

    )



# ======================
# LOGIN BUTTON
# ======================

async def login_button(
    update,
    context
):

    query = update.callback_query

    await query.answer()


    user_id = str(
        query.from_user.id
    )


    if not users.get(
        user_id,
        {}
    ).get(
        "approved"
    ):

        await query.edit_message_text(

            "⛔ دسترسی ندارید.\n\n"
            "ابتدا درخواست عضویت ارسال کنید.",

            reply_markup=menu()

        )

        return



    users[user_id]["step"] = "phone"

    save()



    await query.edit_message_text(

        "📱 شماره تلگرام را ارسال کنید.\n\n"
        "مثال:\n"
        "+989xxxxxxxxx"

    )
# ======================
# TEXT HANDLER
# ======================

async def text_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = str(
        update.message.from_user.id
    )


    if user_id not in users:
        return


    step = users[user_id].get(
        "step"
    )


    # ======================
    # PHONE
    # ======================

    if step == "phone":

        phone = update.message.text.strip()


        if not phone.startswith("+"):

            await update.message.reply_text(
                "❌ شماره نامعتبر است.\n"
                "شماره را با + و کد کشور ارسال کنید."
            )

            return


        os.makedirs(
            "sessions",
            exist_ok=True
        )


        session = f"sessions/{user_id}"


        client = TelegramClient(
            session,
            API_ID,
            API_HASH
        )


        try:

            await client.connect()


            await client.send_code_request(
                phone
            )


            clients[user_id] = client


            users[user_id]["phone"] = phone

            users[user_id]["step"] = "code"


            save()


            await update.message.reply_text(

                "📩 کد ورود تلگرام را ارسال کنید."

            )


        except PhoneNumberInvalidError:


            await update.message.reply_text(

                "❌ شماره تلگرام اشتباه است."

            )


        except Exception as e:


            await update.message.reply_text(

                f"⚠️ خطا در اتصال:\n{e}"

            )



    # ======================
    # CODE
    # ======================

    elif step == "code":


        code = update.message.text.strip()


        client = clients.get(
            user_id
        )


        if not client:

            await update.message.reply_text(

                "❌ نشست ورود پیدا نشد.\n"
                "دوباره تلاش کنید."

            )

            return



        try:


            await client.sign_in(

                users[user_id]["phone"],

                code

            )


            users[user_id]["login"] = True

            users[user_id]["step"] = None


            save()


            await update.message.reply_text(

                "✅ اکانت با موفقیت وصل شد.\n\n"
                "🔥 آماده استفاده از Lucifer | self",

                reply_markup=menu()

            )



        except PhoneCodeInvalidError:


            await update.message.reply_text(

                "❌ کد ورود اشتباه است."

            )



        except SessionPasswordNeededError:


            users[user_id]["step"] = "password"

            save()


            await update.message.reply_text(

                "🔐 رمز دو مرحله‌ای تلگرام را ارسال کنید."

            )



    # ======================
    # PASSWORD
    # ======================

    elif step == "password":


        password = update.message.text.strip()


        client = clients.get(
            user_id
        )


        try:


            await client.sign_in(
                password=password
            )


            users[user_id]["login"] = True

            users[user_id]["step"] = None


            save()


            await update.message.reply_text(

                "✅ ورود با رمز دو مرحله‌ای موفق بود.",

                reply_markup=menu()

            )


        except Exception:


            await update.message.reply_text(

                "❌ رمز دو مرحله‌ای اشتباه است."

            )



# ======================
# CLOCK SYSTEM
# ======================

async def clock_loop(
    user_id
):


    client = clients.get(
        user_id
    )


    if not client:
        return



    while users.get(
        user_id,
        {}
    ).get(
        "clock"
    ) == "on":


        try:


            me = await client.get_me()


            name = me.first_name or ""


            name = re.sub(

                r"\s*\|\s*\d{2}:\d{2}$",

                "",

                name

            )


            clock = datetime.now().strftime(
                "%H:%M"
            )


            await client(
                UpdateProfileRequest(
                    first_name=f"{name} | {clock}"
                )
            )


        except Exception as e:

            print(
                "CLOCK ERROR:",
                e
            )



        await asyncio.sleep(
            2
        )
# ======================
# BUTTON HANDLER
# ======================

async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()


    user_id = str(
        query.from_user.id
    )


    data = query.data



    # ======================
    # LOGIN
    # ======================

    if data == "login":

        await login_button(
            update,
            context
        )


    # ======================
    # REQUEST ACCESS
    # ======================

    elif data == "request_access":

        await request_access(
            update,
            context
        )



    # ======================
    # ADMIN APPROVE
    # ======================

    elif data.startswith(
        "approve_"
    ):


        if query.from_user.id != ADMIN_ID:

            return


        target = data.split(
            "_"
        )[1]


        if target in users:


            users[target]["approved"] = True

            users[target]["pending"] = False

            save()



            await query.edit_message_text(

                "✅ کاربر تایید شد."

            )


            await context.bot.send_message(

                int(target),

                "🎉 عضویت شما تایید شد.\n"
                "اکنون می‌توانید از Lucifer | self استفاده کنید.",

                reply_markup=menu()

            )



    elif data.startswith(
        "reject_"
    ):


        if query.from_user.id != ADMIN_ID:

            return



        target = data.split(
            "_"
        )[1]


        if target in users:

            users[target]["pending"] = False

            save()



        await query.edit_message_text(

            "❌ درخواست رد شد."

        )



    # ======================
    # CLOCK MENU
    # ======================

    elif data == "clock_menu":


        await query.edit_message_text(

            "🕒 مدیریت ساعت پروفایل\n\n"

            "━━━━━━━━━━━━━━\n"
            "⏰ بروزرسانی هر دقیقه\n"
            "⚡ مستقل برای هر اکانت\n"
            "━━━━━━━━━━━━━━",

            reply_markup=clock_menu()

        )



    # ======================
    # CLOCK ON
    # ======================

    elif data == "clock_on":


        if not users.get(
            user_id,
            {}
        ).get(
            "approved"
        ):

            await query.edit_message_text(

                "⛔ عضویت شما تایید نشده.",

                reply_markup=menu()

            )

            return



        if not users[user_id].get(
            "login"
        ):

            await query.edit_message_text(

                "❌ ابتدا اکانت را وصل کنید.",

                reply_markup=menu()

            )

            return



        users[user_id]["clock"] = "on"

        save()



        if user_id not in clock_tasks:


            clock_tasks[user_id] = asyncio.create_task(

                clock_loop(
                    user_id
                )

            )



        await query.edit_message_text(

            "🔥 Lucifer | self\n\n"

            "🕒 ساعت فعال شد ✅\n"
            "⏰ بروزرسانی هر دقیقه",

            reply_markup=clock_menu()

        )



    # ======================
    # CLOCK OFF
    # ======================

    elif data == "clock_off":


        users[user_id]["clock"] = "off"

        save()



        await query.edit_message_text(

            "🌙 ساعت خاموش شد.",

            reply_markup=clock_menu()

        )



    # ======================
    # BACK
    # ======================

    elif data == "back":


        await query.edit_message_text(

            "🔥 Lucifer | self\n\n"
            "پنل مدیریت",

            reply_markup=menu()

        )



# ======================
# MAIN
# ======================

def main():


    app = Application.builder().token(
        BOT_TOKEN
    ).build()



    app.add_handler(

        CommandHandler(
            "start",
            start
        )

    )


    app.add_handler(

        CallbackQueryHandler(
            buttons
        )

    )


    app.add_handler(

        MessageHandler(

            filters.TEXT & ~filters.COMMAND,

            text_handler

        )

    )


    print(
        "🔥 Lucifer | self Started"
    )


    app.run_polling()



if __name__ == "__main__":

    main()
