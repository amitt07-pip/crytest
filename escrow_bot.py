import os
import random
import asyncio
import json
import nest_asyncio

nest_asyncio.apply()

from telegram import (  # noqa: E402
    Update, ChatJoinRequest, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (  # noqa: E402
    ApplicationBuilder, CommandHandler, ContextTypes,
    ChatJoinRequestHandler, CallbackQueryHandler, MessageHandler, filters
)
from telethon import TelegramClient  # noqa: E402
from telethon.tl.functions.messages import (  # noqa: E402
    CreateChatRequest, ExportChatInviteRequest, MigrateChatRequest,
    EditChatAboutRequest
)
from telethon.tl.functions.channels import (  # noqa: E402
    ToggleJoinRequestRequest, EditAdminRequest
)
from telethon.tl.types import ChatAdminRights, Channel  # noqa: E402


API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
PHONE = os.environ.get("PHONE")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

ESCROW_ADDRESSES_LINK = "https://t.me/c/1469665894/124973/138374"
ALLOWED_USERS_FILE = "allowed_users.json"
GROUP_DATA_FILE = "group_data.json"
DEALS_FILE = "deals.json"

userbot_client = None
allowed_users = {}
group_data = {}
deals = {}


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


def load_group_data():
    global group_data
    try:
        with open(GROUP_DATA_FILE, "r") as f:
            group_data = json.load(f)
    except FileNotFoundError:
        group_data = {}


def save_group_data():
    with open(GROUP_DATA_FILE, "w") as f:
        json.dump(group_data, f)


def load_deals():
    global deals
    try:
        with open(DEALS_FILE, "r") as f:
            deals = json.load(f)
    except FileNotFoundError:
        deals = {}


def save_deals():
    with open(DEALS_FILE, "w") as f:
        json.dump(deals, f)


def generate_deal_id():
    return f"D{random.randint(1000, 9999)}"


def parse_deal_form(text):
    """Parse the filled deal form and extract details."""
    lines = text.strip().split('\n')
    data = {}

    for line in lines:
        line = line.strip()
        if ':' not in line:
            continue

        key, value = line.split(':', 1)
        key = key.strip().lower()
        value = value.strip()

        if 'seller' in key:
            data['seller'] = value
        elif 'buyer' in key:
            data['buyer'] = value
        elif 'amount' in key and 'usdt' in key.lower():
            data['amount_usdt'] = value
        elif 'amount' in key and 'usdc' in key.lower():
            data['amount_usdc'] = value
        elif 'amount' in key and 'inr' in key.lower():
            data['amount_inr'] = value
        elif 'payment' in key:
            data['payment_method'] = value
        elif 'time' in key:
            data['time'] = value

    return data


def get_network_display_name(network):
    """Get display name for network."""
    mapping = {
        'BSC': 'BEP20',
        'POLYGON': 'POLYGON',
        'SOL': 'SOLANA'
    }
    return mapping.get(network, network)


def get_network_buttons(deal_id):
    """Create network selection buttons."""
    keyboard = [
        [
            InlineKeyboardButton(
                "USDT[BSC]", callback_data=f"network_{deal_id}_BSC"
            ),
            InlineKeyboardButton(
                "USDT[POLYGON]", callback_data=f"network_{deal_id}_POLYGON"
            )
        ],
        [
            InlineKeyboardButton(
                "USDT[SOL]", callback_data=f"network_{deal_id}_SOL"
            )
        ],
        [
            InlineKeyboardButton(
                "Cancel", callback_data=f"cancel_{deal_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_only_button(deal_id):
    """Create cancel-only button."""
    keyboard = [[
        InlineKeyboardButton("Cancel", callback_data=f"cancel_{deal_id}")
    ]]
    return InlineKeyboardMarkup(keyboard)


async def init_userbot():
    global userbot_client
    userbot_client = TelegramClient("userbot_session", API_ID, API_HASH)
    await userbot_client.start(phone=PHONE)
    print("Userbot started successfully!")
    return userbot_client


async def create_escrow_group(
    room_number, sender_username, mentioned_username, bot_username
):
    global userbot_client, allowed_users, group_data

    if userbot_client is None:
        await init_userbot()

    group_title = f"Crypto India Escrow Room {room_number}"

    try:
        result = await userbot_client(CreateChatRequest(
            users=[bot_username],
            title=group_title
        ))

        print(f"CreateChatRequest result type: {type(result)}")
        print(f"CreateChatRequest result: {result}")

        chat_id = None
        if hasattr(result, 'chats') and result.chats:
            chat = result.chats[0]
            chat_id = chat.id
        elif hasattr(result, 'updates'):
            updates_obj = result.updates
            if hasattr(updates_obj, 'chats') and updates_obj.chats:
                chat = updates_obj.chats[0]
                chat_id = chat.id
            elif hasattr(updates_obj, 'updates'):
                for update in updates_obj.updates:
                    if hasattr(update, 'chat_id'):
                        chat_id = update.chat_id
                        break
                    elif hasattr(update, 'peer'):
                        if hasattr(update.peer, 'chat_id'):
                            chat_id = update.peer.chat_id
                            break

        if chat_id is None:
            dialogs = await userbot_client.get_dialogs(limit=5)
            for dialog in dialogs:
                if dialog.title == group_title:
                    chat_id = dialog.id
                    break

        if chat_id is None:
            print("Could not find chat_id from response")
            return None, room_number, None

        print(f"Found chat_id: {chat_id}")

        try:
            migrated = await userbot_client(MigrateChatRequest(
                chat_id=chat_id
            ))
            print(f"MigrateChatRequest result: {migrated}")

            channel_id = None
            if hasattr(migrated, 'chats'):
                for chat_obj in migrated.chats:
                    if isinstance(chat_obj, Channel):
                        channel_id = chat_obj.id
                        print(f"Found Channel in migration: {channel_id}")
                        break

            if channel_id is None:
                await asyncio.sleep(1)
                dialogs = await userbot_client.get_dialogs(limit=5)
                for dialog in dialogs:
                    if dialog.title == group_title:
                        entity = dialog.entity
                        if isinstance(entity, Channel):
                            channel_id = entity.id
                            print(f"Found Channel via dialogs: {channel_id}")
                            break

            if channel_id is None:
                print("Migration did not return a Channel, using chat_id")
                channel_id = chat_id
            else:
                print(f"Migrated to supergroup: {channel_id}")
        except Exception as migrate_error:
            print(f"Migration error: {migrate_error}")
            channel_id = chat_id

        try:
            await userbot_client(EditChatAboutRequest(
                peer=channel_id,
                about="Join @CryptoIndiaUnited"
            ))
            print("Group description set")
        except Exception as about_error:
            print(f"Warning: Could not set group description: {about_error}")

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

        full_channel_id = f"-100{channel_id}"
        allowed_users[full_channel_id] = [sender_clean, mentioned_clean]
        save_allowed_users()

        group_data[full_channel_id] = {
            "allowed_users": [sender_clean, mentioned_clean],
            "joined_users": [],
            "mentioned_user": mentioned_username,
            "sender_user": sender_username
        }
        save_group_data()

        return invite_link, room_number, channel_id

    except Exception as e:
        print(f"Error creating group: {e}")
        return None, room_number, None


def get_form_text(currency="USDT"):
    return (
        f"<code>{currency} Seller:\n"
        f"{currency} Buyer:\n"
        f"Amount[{currency}]:\n"
        f"Amount[INR]:\n"
        f"Payment Method:\n"
        f"Time[Minute]:</code>"
    )


def get_form_keyboard(current_currency="USDT"):
    if current_currency == "USDT":
        button_text = "GET FORM FOR USDC DEAL"
        callback_data = "switch_to_usdc"
    else:
        button_text = "GET FORM FOR USDT DEAL"
        callback_data = "switch_to_usdt"

    button = InlineKeyboardButton(button_text, callback_data=callback_data)
    keyboard = [[button]]
    return InlineKeyboardMarkup(keyboard)


async def handle_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    global deals

    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    username = user.username.lower() if user.username else None

    if data == "switch_to_usdc":
        new_text = get_form_text("USDC")
        new_keyboard = get_form_keyboard("USDC")
        await query.edit_message_text(
            text=new_text,
            parse_mode="HTML",
            reply_markup=new_keyboard
        )
        return

    if data == "switch_to_usdt":
        new_text = get_form_text("USDT")
        new_keyboard = get_form_keyboard("USDT")
        await query.edit_message_text(
            text=new_text,
            parse_mode="HTML",
            reply_markup=new_keyboard
        )
        return

    if data.startswith("network_"):
        parts = data.split("_")
        deal_id = parts[1]
        network = parts[2]

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean:
            await query.answer("Only the seller can select the network!")
            return

        deal['network'] = network
        deal['status'] = 'pending_buyer_address'
        save_deals()

        network_name = get_network_display_name(network)
        seller = deal['seller']

        new_text = (
            f"<b><i>Deal</i></b> #{deal_id}\n\n"
            f"<b>{seller}</b> [Seller] has selected "
            f"<b>{network_name}</b> as the deposit network for USDT."
        )

        await query.edit_message_text(
            text=new_text,
            parse_mode="HTML",
            reply_markup=get_cancel_only_button(deal_id)
        )

        buyer = deal['buyer']
        chat_id = query.message.chat_id

        buyer_msg = (
            f"<b><u>Deal</u></b> #{deal_id}\n\n"
            f"{buyer} [Buyer] please <b>QUOTE</b> this message and reply "
            f"with your <b>USDT {network_name}</b> address.\n"
            f"Please be mindful that funds <b>cannot be recovered</b> "
            f"if sent to the wrong network address."
        )

        sent_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=buyer_msg,
            parse_mode="HTML"
        )

        deal['buyer_address_msg_id'] = sent_msg.message_id
        save_deals()
        return

    if data.startswith("cancel_"):
        deal_id = data.split("_")[1]

        if deal_id in deals:
            del deals[deal_id]
            save_deals()

        await query.edit_message_text(
            text="Deal has been cancelled.",
            parse_mode="HTML"
        )
        return


async def handle_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle regular messages - form submissions and address replies."""
    global deals

    message = update.message
    if not message or not message.text:
        return

    chat_id = message.chat_id
    user = message.from_user
    username = user.username.lower() if user.username else None
    text = message.text.strip()

    if message.reply_to_message:
        reply_to_msg_id = message.reply_to_message.message_id
        bot_info = await context.bot.get_me()

        if message.reply_to_message.from_user.id != bot_info.id:
            return

        for deal_id, deal in deals.items():
            if deal.get('buyer_address_msg_id') == reply_to_msg_id:
                buyer_clean = deal['buyer'].lstrip('@').lower()

                if username != buyer_clean:
                    return

                deal['buyer_address'] = text
                deal['status'] = 'pending_seller_address'
                save_deals()

                await message.reply_text(
                    "Release Address Successfully Saved!\n\n"
                    f"⚠️ <b>{deal['seller']}</b> Do <b>NOT</b> send USDT "
                    "to this address!!",
                    parse_mode="HTML"
                )

                network_name = get_network_display_name(deal['network'])
                seller = deal['seller']

                seller_msg = (
                    f"<b><u>Deal</u></b> #{deal_id}\n\n"
                    f"{seller} [Seller] please <b>QUOTE</b> this message "
                    f"and reply with your <b>USDT {network_name}</b> address "
                    f"for a <b>REFUND</b> in case of a dispute.\n"
                    f"Please be mindful that funds <b>cannot be recovered</b> "
                    f"if sent to the wrong network address."
                )

                sent_msg = await context.bot.send_message(
                    chat_id=chat_id,
                    text=seller_msg,
                    parse_mode="HTML"
                )

                deal['seller_address_msg_id'] = sent_msg.message_id
                save_deals()
                return

            if deal.get('seller_address_msg_id') == reply_to_msg_id:
                seller_clean = deal['seller'].lstrip('@').lower()

                if username != seller_clean:
                    return

                deal['seller_address'] = text
                deal['status'] = 'addresses_collected'
                save_deals()

                await message.reply_text(
                    "Refund Address Successfully Saved!",
                    parse_mode="HTML"
                )
                return

        return

    if 'seller' in text.lower() and 'buyer' in text.lower():
        form_data = parse_deal_form(text)

        if not form_data.get('seller') or not form_data.get('buyer'):
            return

        deal_id = generate_deal_id()

        while deal_id in deals:
            deal_id = generate_deal_id()

        currency = 'USDT'
        if form_data.get('amount_usdc'):
            currency = 'USDC'

        amount_crypto = form_data.get('amount_usdt') or form_data.get(
            'amount_usdc', ''
        )

        deals[deal_id] = {
            'chat_id': chat_id,
            'seller': form_data['seller'],
            'buyer': form_data['buyer'],
            'amount_crypto': amount_crypto,
            'amount_inr': form_data.get('amount_inr', ''),
            'payment_method': form_data.get('payment_method', ''),
            'time': form_data.get('time', ''),
            'currency': currency,
            'network': None,
            'buyer_address': None,
            'seller_address': None,
            'status': 'pending_network',
            'buyer_address_msg_id': None,
            'seller_address_msg_id': None
        }
        save_deals()

        seller = form_data['seller']
        buyer = form_data['buyer']

        msg = (
            f"<b><i>Deal</i></b> #{deal_id}\n\n"
            f"<b>{seller}</b> [Seller] Select Deposit Network for "
            f"<b>{currency}</b>\n\n"
            f"🔹<b>Note to Buyer ({buyer}):</b> You will only be able to "
            f"withdraw {currency} on the network selected by the seller."
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode="HTML",
            reply_markup=get_network_buttons(deal_id)
        )


async def send_welcome_messages(context, chat_id, mentioned_user, sender_user):
    msg1 = (
        f"Hii {mentioned_user}, Welcome to the Escrow Group!\n\n"
        f"Please use /clean to free the group after the deal is completed."
    )
    await context.bot.send_message(chat_id=int(chat_id), text=msg1)

    msg2 = (
        f"{mentioned_user} {sender_user}\n"
        f"One of you need to fill the form given below to start the deal!\n\n"
        f"Use /exampleform to check out a filled example to guide you.\n\n"
        f"<b><u>Note</u></b>:- While specifying Amount[USDT/USDC] "
        f"<b>include</b> Escrow Fees in it. "
        f"Escrow fees will be deducted before releasing the amount "
        f"to the buyer."
    )
    await context.bot.send_message(
        chat_id=int(chat_id),
        text=msg2,
        parse_mode="HTML"
    )

    form_text = get_form_text("USDT")
    keyboard = get_form_keyboard("USDT")
    await context.bot.send_message(
        chat_id=int(chat_id),
        text=form_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


async def handle_join_request(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    global group_data

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

            if chat_id in group_data:
                if username not in group_data[chat_id]["joined_users"]:
                    group_data[chat_id]["joined_users"].append(username)
                    save_group_data()

                    if len(group_data[chat_id]["joined_users"]) == 2:
                        mentioned = group_data[chat_id]["mentioned_user"]
                        sender = group_data[chat_id]["sender_user"]
                        await asyncio.sleep(2)
                        await send_welcome_messages(
                            context, chat_id, mentioned, sender
                        )
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
        f"<b>Crypto India Escrow Room {room_num}</b>. "
        f"Please use the following link to join the room:\n\n"
        f"{invite_link}\n\n"
        f"⚠️ Scammers may invite you at some parallel fake escrow room. "
        f"Always double check the correct one by using the above link. "
        f"Please deposit USDT / USDC only when the bot prompts you to do so. "
        f"Do not send anything in advance to avoid issues. "
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
    load_group_data()
    load_deals()
    await init_userbot()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("escrow", escrow))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message
    ))

    print("Bot is running...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
