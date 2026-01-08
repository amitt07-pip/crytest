import os
import random
import asyncio
import json
from telegram import Update, ChatJoinRequest
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ChatJoinRequestHandler
)
from telethon import TelegramClient
from telethon.tl.functions.messages import (
    CreateChatRequest, ExportChatInviteRequest, MigrateChatRequest
)
from telethon.tl.functions.channels import (
    ToggleJoinRequestRequest, EditAdminRequest
)
from telethon.tl.types import ChatAdminRights


API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
PHONE = os.environ.get("PHONE")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

ESCROW_ADDRESSES_LINK = "https://t.me/c/1469665894/124973/138374"
ALLOWED_USERS_FILE = "allowed_users.json"

userbot_client = None
allowed_users = {}


def load_allowed_users():
    global allowed_users
    try:
        with open(ALLOWED_USERS_FILE, "r") as f:
            allowed_users = json.load(f)
    except FileNotFoundError:
        allowed_users = {}


def save_allowed_users():
    with open(ALLOWED_USERS_FILE, "w") as f:
        json.dump(allowed_users, f)


async def init_userbot():
    global userbot_client
    userbot_client = TelegramClient("userbot_session", API_ID, API_HASH)
    await userbot_client.start(phone=PHONE)
    print("Userbot started successfully!")
    return userbot_client


async def create_escrow_group(
    room_number, sender_username, mentioned_username, bot_username
):
    global userbot_client, allowed_users

    if userbot_client is None:
        await init_userbot()

    group_title = f"Crypto India Escrow Room {room_number}"

    try:
        result = await userbot_client(CreateChatRequest(
            users=[bot_username],
            title=group_title
        ))

        chat = result.chats[0]
        chat_id = chat.id

        try:
            migrated = await userbot_client(MigrateChatRequest(
                chat_id=chat_id
            ))
            channel = migrated.chats[0]
            channel_id = channel.id
            print(f"Migrated to supergroup: {channel_id}")
        except Exception as migrate_error:
            print(f"Migration error: {migrate_error}")
            channel_id = chat_id

        try:
            admin_rights = ChatAdminRights(
                change_info=True,
                post_messages=True,
                edit_messages=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                add_admins=False,
                anonymous=False,
                manage_call=True,
                other=True
            )
            await userbot_client(EditAdminRequest(
                channel=channel_id,
                user_id=bot_username,
                admin_rights=admin_rights,
                rank="Escrow Bot"
            ))
            print(f"Bot promoted to admin in supergroup {channel_id}")
        except Exception as admin_error:
            print(f"Warning: Could not promote bot to admin: {admin_error}")

        try:
            await userbot_client(ToggleJoinRequestRequest(
                channel=channel_id,
                enabled=True
            ))
            print("Join request approval enabled")
        except Exception as toggle_error:
            print(f"Warning: Could not enable join requests: {toggle_error}")

        invite = await userbot_client(ExportChatInviteRequest(
            peer=channel_id,
            expire_date=None,
            usage_limit=0,
            request_needed=True
        ))

        invite_link = invite.link

        sender_clean = sender_username.lstrip("@").lower()
        mentioned_clean = mentioned_username.lstrip("@").lower()
        allowed_users[str(channel_id)] = [sender_clean, mentioned_clean]
        save_allowed_users()

        return invite_link, room_number, channel_id

    except Exception as e:
        print(f"Error creating group: {e}")
        return None, room_number, None


async def handle_join_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    join_request: ChatJoinRequest = update.chat_join_request
    chat_id = str(join_request.chat.id)
    user = join_request.from_user
    username = user.username.lower() if user.username else None

    print(f"Join request from {username} for chat {chat_id}")

    if chat_id in allowed_users:
        allowed = allowed_users[chat_id]
        if username and username in allowed:
            await join_request.approve()
            print(f"Approved join request from {username}")
        else:
            await join_request.decline()
            print(f"Declined join request from {username}")
    else:
        await join_request.decline()
        print(f"Declined join request - chat {chat_id} not in allowed list")


async def escrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user.username
    chat_id = update.effective_chat.id

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Usage: /escrow @username"
        )
        return

    mentioned_user = context.args[0]

    if not mentioned_user.startswith("@"):
        mentioned_user = "@" + mentioned_user

    sender_username = f"@{sender}" if sender else "User"

    room_number = random.randint(1, 20)

    bot_info = await context.bot.get_me()
    bot_username = bot_info.username

    invite_link, room_num, channel_id = await create_escrow_group(
        room_number,
        sender_username,
        mentioned_user,
        bot_username
    )

    if invite_link is None:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Failed to create escrow room. Please try again later."
        )
        return

    message = (
        f"{mentioned_user} & {sender_username} are requested to join "
        f"<b>Crypto India Escrow Room {room_num}</b>.\n\n"
        f"Please use the following link to join the room 👇\n\n"
        f"{invite_link}\n\n"
        f"⚠️ Scammers may invite you at some parallel fake escrow room. "
        f"Always double check the correct one by using the above link.\n\n"
        f"Please deposit USDT / USDC only when the bot prompts you to do so. "
        f"Do not send anything in advance to avoid issues.\n\n"
        f"Always verify the deposit address provided by Bot with the ones "
        f"mentioned @ <a href=\"{ESCROW_ADDRESSES_LINK}\">"
        f"List of Escrow Addresses</a>."
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def main():
    load_allowed_users()
    await init_userbot()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("escrow", escrow))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))

    print("Bot is running...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
