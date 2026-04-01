import os
import random
import asyncio
import json
import time
import aiohttp
import nest_asyncio
import logging
from datetime import datetime

nest_asyncio.apply()

# Configure logging - suppress HTTP request spam from libraries
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Suppress noisy HTTP loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.Application").setLevel(logging.WARNING)
logging.getLogger("telegram.ext._application").setLevel(logging.WARNING)


def log_info(message):
    """Log info message."""
    logger.info(message)


def log_error(message):
    """Log error message."""
    logger.error(message)


def log_warning(message):
    """Log warning message."""
    logger.warning(message)

from telegram import (  # noqa: E402
    Update, ChatJoinRequest, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (  # noqa: E402
    ApplicationBuilder, CommandHandler, ContextTypes,
    ChatJoinRequestHandler, CallbackQueryHandler, MessageHandler, filters,
    ChatMemberHandler
)
from telethon import TelegramClient  # noqa: E402
from telethon.tl.functions.messages import (  # noqa: E402
    CreateChatRequest, ExportChatInviteRequest, MigrateChatRequest,
    EditChatAboutRequest
)
from telethon.tl.functions.channels import (  # noqa: E402
    ToggleJoinRequestRequest, EditAdminRequest, InviteToChannelRequest,
    EditBannedRequest
)
from telethon.tl.functions.contacts import ResolveUsernameRequest  # noqa: E402
from telethon.tl.types import ChatAdminRights, Channel, ChatBannedRights, ChannelParticipantsAdmins  # noqa: E402


API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
PHONE = os.environ.get("PHONE")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

ESCROW_ADDRESSES_LINK = "https://t.me/c/1469665894/124973/138374"
ALLOWED_USERS_FILE = "allowed_users.json"
GROUP_DATA_FILE = "group_data.json"
DEALS_FILE = "deals.json"
ROOMS_FILE = "rooms.json"
BANNED_USERS_FILE = "banned_users.json"
USER_2FA_FILE = "user_2fa.json"
# QR Images for USDT addresses
BSC_QR_IMAGES = [
    "bsc_address1_qr.jpg",    # QR for Address 1
    "bsc_address2_qr.jpg"     # QR for Address 2
]
POLYGON_QR_IMAGES = [
    "polygon_address1_qr.jpg",  # QR for Address 1
    "polygon_address2_qr.jpg"   # QR for Address 2
]
SOL_QR_IMAGES = [
    "sol_address1_qr.jpg",    # QR for Address 1
    "sol_address2_qr.jpg"     # QR for Address 2
]

# USDT Deposit Addresses
BSC_DEPOSIT_ADDRESSES = [
    "0x9b4F87471a1648CAA3Cf8D87594a8eE321077FF7",  # Address 1
    "0xf282e789e835ed379aea84ece204d2d643e6774f"   # Address 2
]

POLYGON_DEPOSIT_ADDRESSES = [
    "0x6a2757F5987a845D77f3DB441a3d0aB50a3A3A98",  # Address 1
    "0xf282e789e835ed379aea84ece204d2d643e6774f"   # Address 2
]

SOL_DEPOSIT_ADDRESSES = [
    "9AHM8xU6rW6sC4hZJcpciaT64tqstcw5o7cWW31eKZB5",  # Address 1
    "5KDFAQ6p1ofPWZBGaxWTSu2EziyX9GyQ36H547zxBou3"   # Address 2
]

# USDC Deposit Addresses
USDC_BSC_QR_IMAGES = [
    "usdc_bsc_address1_qr.jpg",  # QR for Address 1
    "usdc_bsc_address2_qr.jpg"   # QR for Address 2
]
USDC_BSC_DEPOSIT_ADDRESSES = [
    "0x9b4F87471a1648CAA3Cf8D87594a8eE321077FF7",  # Address 1
    "0xf282e789e835ed379aea84ece204d2d643e6774f"   # Address 2
]

# USDC Polygon - Address 1 only (Address 2 = same as Address 1)
USDC_POLYGON_DEPOSIT_ADDRESS = "0x6a2757F5987a845D77f3DB441a3d0aB50a3A3A98"  # Address 1
USDC_POLYGON_QR_IMAGE = "usdc_polygon_address1_qr.jpg"  # QR for Address 1

# USDC Solana - Address 1 only (Address 2 = same as Address 1)
USDC_SOL_DEPOSIT_ADDRESS = "9AHM8xU6rW6sC4hZJcpciaT64tqstcw5o7cWW31eKZB5"  # Address 1
USDC_SOL_QR_IMAGE = "usdc_sol_address1_qr.jpg"  # QR for Address 1

DEPOSIT_ADDRESSES = {
    "BSC": BSC_DEPOSIT_ADDRESSES[0],
    "POLYGON": POLYGON_DEPOSIT_ADDRESSES[0],
    "SOL": SOL_DEPOSIT_ADDRESSES[0],
    "USDC_BSC": USDC_BSC_DEPOSIT_ADDRESSES[0],
    "USDC_POLYGON": USDC_POLYGON_DEPOSIT_ADDRESS,
    "USDC_SOL": USDC_SOL_DEPOSIT_ADDRESS
}

bsc_address_index = 0
polygon_address_index = 0
sol_address_index = 0
usdc_bsc_address_index = 0

ADMIN_USER_IDS = [7338429782, 8346781181, 6662820986, 7090417167]

DEAL_LOG_CHANNEL_ID = -1003266978268

BSCSCAN_API_KEY = os.environ.get("BSCSCAN_API_KEY", "")
POLYGONSCAN_API_KEY = os.environ.get("POLYGONSCAN_API_KEY", "")
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY", "")

USDT_CONTRACTS = {
    "BSC": "0x55d398326f99059fF775485246999027B3197955",
    "POLYGON": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "SOL": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
}

USDC_CONTRACTS = {
    "BSC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
    "POLYGON": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    "SOL": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
}

BLOCKCHAIN_APIS = {
    "BSC": "https://api.bscscan.com/api",
    "POLYGON": "https://api.polygonscan.com/api",
    "SOL": "https://api.solscan.io"
}

# BSC RPC endpoints (with fallbacks)
BSC_RPC_ENDPOINTS = [
    "https://bsc-mainnet.nodereal.io/v1/64a9df0874fb4a93b9d0a3849de012d3",
    "https://bsc-dataseed.binance.org/",
    "https://bsc-dataseed1.binance.org/",
    "https://bsc-dataseed2.binance.org/",
    "https://bsc-dataseed3.binance.org/",
    "https://bsc-dataseed4.binance.org/",
]
NODEREAL_BSC_RPC = BSC_RPC_ENDPOINTS[0]  # Primary endpoint

# Polygon RPC endpoints (with fallbacks)
POLYGON_RPC_ENDPOINTS = [
    "https://polygon-rpc.com/",
    "https://rpc-mainnet.matic.network",
    "https://rpc-mainnet.maticvigil.com/",
    "https://polygon-mainnet.public.blastapi.io",
    "https://polygon.llamarpc.com",
]

# ERC20 Transfer event topic (keccak256 of "Transfer(address,address,uint256)")
TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

active_monitors = {}

userbot_client = None
allowed_users = {}
group_data = {}
deals = {}
rooms = {}
banned_users = {}
user_2fa = {}


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


def load_rooms():
    global rooms
    try:
        with open(ROOMS_FILE, "r") as f:
            rooms = json.load(f)
    except FileNotFoundError:
        rooms = {}


def save_rooms():
    with open(ROOMS_FILE, "w") as f:
        json.dump(rooms, f)


def load_banned_users():
    global banned_users
    try:
        with open(BANNED_USERS_FILE, "r") as f:
            banned_users = json.load(f)
    except FileNotFoundError:
        banned_users = {}


def save_banned_users():
    with open(BANNED_USERS_FILE, "w") as f:
        json.dump(banned_users, f)


def load_user_2fa():
    global user_2fa
    try:
        with open(USER_2FA_FILE, "r") as f:
            user_2fa = json.load(f)
    except FileNotFoundError:
        user_2fa = {}


def save_user_2fa():
    with open(USER_2FA_FILE, "w") as f:
        json.dump(user_2fa, f)


def is_user_banned(user_id, username):
    """Check if a user is banned by ID or username."""
    if str(user_id) in banned_users:
        return True
    if username:
        username_clean = username.lstrip('@').lower()
        for banned_key, banned_data in banned_users.items():
            banned_username = banned_data.get('username') or ''
            if banned_username.lower() == username_clean:
                return True
    return False


def get_user_active_deal(username):
    """Check if a user has an active escrow deal. Returns (username, message_link) if found, else (None, None)."""
    if not username:
        return None, None
    
    username_clean = username.lstrip('@').lower()
    
    for channel_id, data in group_data.items():
        sender_user = data.get('sender_user', '').lstrip('@').lower()
        mentioned_user = data.get('mentioned_user', '').lstrip('@').lower()
        escrow_message_id = data.get('escrow_message_id')
        escrow_chat_id = data.get('escrow_chat_id')
        
        if username_clean in [sender_user, mentioned_user]:
            if escrow_message_id and escrow_chat_id:
                chat_id_str = str(escrow_chat_id)
                if chat_id_str.startswith('-100'):
                    chat_id_for_link = chat_id_str[4:]
                elif chat_id_str.startswith('-'):
                    chat_id_for_link = chat_id_str[1:]
                else:
                    chat_id_for_link = chat_id_str
                message_link = f"https://t.me/c/{chat_id_for_link}/{escrow_message_id}"
                
                if username_clean == sender_user:
                    return data.get('sender_user', username), message_link
                else:
                    return data.get('mentioned_user', username), message_link
    
    return None, None


def truncate_address(address):
    """Truncate address to first 3 and last 4 characters."""
    if not address or len(address) < 8:
        return address or "N/A"
    return f"{address[:3]}...{address[-4:]}"


def build_deal_log_message(deal_id, buyer, seller, room_num, status, deposit_address=None, amount=None, token=None, escrow_sender=None, initiator_joined=False, counterparty_joined=False, mentioned_user=None):
    """Build the deal log message for the log channel."""
    # Format token display (e.g., USDT/USDC)
    token_display = token if token else "N/A"
    
    # Format amount display
    amount_display = amount if amount else "N/A"
    
    # Determine initiator and counterparty
    # escrow_sender is always the initiator (person who used /escrow)
    # mentioned_user is always the counterparty (person mentioned in /escrow @username)
    initiator = escrow_sender if escrow_sender else buyer
    counterparty = mentioned_user if mentioned_user else seller
    
    # Join status indicators
    initiator_status = "Joined" if initiator_joined else "Not Joined"
    counterparty_status = "Joined" if counterparty_joined else "Not Joined"
    
    msg = (
        f"<b>ESCROW ROOM {room_num}</b>\n\n"
        f"• <b>Initiator ({initiator}) Status</b> - {initiator_status}\n"
        f"• <b>CounterParty ({counterparty}) Status</b> - {counterparty_status}\n"
        f"• <b>Deal Amount[{token_display}]</b> - {amount_display}\n"
        f"• <b>Deal Status</b> - {status}"
    )
    return msg


async def send_deal_log(bot, deal_id, buyer, seller, room_num, status="Deal Started", token=None, amount=None, escrow_sender=None, initiator_joined=False, counterparty_joined=False, mentioned_user=None):
    """Send initial deal log message to the log channel."""
    try:
        msg = build_deal_log_message(deal_id, buyer, seller, room_num, status, None, amount, token, escrow_sender, initiator_joined, counterparty_joined, mentioned_user)
        sent_msg = await bot.send_message(
            chat_id=DEAL_LOG_CHANNEL_ID,
            text=msg,
            parse_mode="HTML"
        )
        # Store the log message ID in the deal for future updates
        if deal_id in deals:
            deals[deal_id]['log_message_id'] = sent_msg.message_id
            save_deals()
        log_info(f"Deal log sent for #{deal_id}")
        return sent_msg.message_id
    except Exception as e:
        log_error(f"Failed to send deal log: {e}")
        return None


async def send_initial_deal_log(bot, room_num, initiator, counterparty, channel_id, initiator_joined=False, counterparty_joined=False):
    """Send initial deal log when /escrow command is used."""
    try:
        initiator_status = "Joined" if initiator_joined else "Not Joined"
        counterparty_status = "Joined" if counterparty_joined else "Not Joined"
        
        if initiator_joined and counterparty_joined:
            deal_status = "Both Users Joined"
        elif initiator_joined or counterparty_joined:
            deal_status = "Waiting for Users"
        else:
            deal_status = "Room Assigned"
        
        msg = (
            f"<b>ESCROW ROOM {room_num}</b>\n\n"
            f"• <b>Initiator ({initiator}) Status</b> - {initiator_status}\n"
            f"• <b>CounterParty ({counterparty}) Status</b> - {counterparty_status}\n"
            f"• <b>Deal Amount[N/A]</b> - N/A\n"
            f"• <b>Deal Status</b> - {deal_status}"
        )
        sent_msg = await bot.send_message(
            chat_id=DEAL_LOG_CHANNEL_ID,
            text=msg,
            parse_mode="HTML"
        )
        # Store the log message ID in group_data for future updates
        full_channel_id = f"-100{channel_id}" if not str(channel_id).startswith("-100") else str(channel_id)
        if full_channel_id in group_data:
            group_data[full_channel_id]['log_message_id'] = sent_msg.message_id
            save_group_data()
        log_info(f"Initial deal log sent for room {room_num}")
        return sent_msg.message_id
    except Exception as e:
        log_error(f"Failed to send initial deal log: {e}")
        return None


async def update_initial_deal_log(bot, channel_id, initiator, counterparty, room_num, initiator_joined=False, counterparty_joined=False):
    """Update the initial deal log when users join."""
    try:
        full_channel_id = f"-100{channel_id}" if not str(channel_id).startswith("-100") else str(channel_id)
        if full_channel_id not in group_data:
            return
        
        log_message_id = group_data[full_channel_id].get('log_message_id')
        if not log_message_id:
            return
        
        initiator_status = "Joined" if initiator_joined else "Not Joined"
        counterparty_status = "Joined" if counterparty_joined else "Not Joined"
        
        if initiator_joined and counterparty_joined:
            deal_status = "Both Users Joined"
        elif initiator_joined or counterparty_joined:
            deal_status = "Waiting for Users"
        else:
            deal_status = "Room Assigned"
        
        msg = (
            f"<b>ESCROW ROOM {room_num}</b>\n\n"
            f"• <b>Initiator ({initiator}) Status</b> - {initiator_status}\n"
            f"• <b>CounterParty ({counterparty}) Status</b> - {counterparty_status}\n"
            f"• <b>Deal Amount[N/A]</b> - N/A\n"
            f"• <b>Deal Status</b> - {deal_status}"
        )
        
        await bot.edit_message_text(
            chat_id=DEAL_LOG_CHANNEL_ID,
            message_id=log_message_id,
            text=msg,
            parse_mode="HTML"
        )
        log_info(f"Updated deal log for room {room_num}: {deal_status}")
    except Exception as e:
        log_error(f"Failed to update initial deal log: {e}")


async def update_deal_log(bot, deal_id, status):
    """Update the deal log message with new status."""
    try:
        if deal_id not in deals:
            return
        
        deal = deals[deal_id]
        log_message_id = deal.get('log_message_id')
        if not log_message_id:
            return
        
        buyer = deal.get('buyer_username', 'N/A')
        seller = deal.get('seller_username', 'N/A')
        room_num = deal.get('room_number', 'N/A')
        escrow_sender = deal.get('sender_user', 'N/A')
        
        # Include deposit address in log once it's set
        deposit_address = deal.get('deposit_address')
        
        # Get deal amount (USDT or USDC) - just the number
        amount = deal.get('amount_usdt') or deal.get('amount_usdc')
        
        # Build token display (e.g., USDT/USDC)
        currency = deal.get('currency', 'USDT')
        token = currency
        
        # Get join status from deal or group_data
        initiator_joined = deal.get('initiator_joined', False)
        counterparty_joined = deal.get('counterparty_joined', False)
        
        # Get mentioned_user (counterparty) from deal or group_data
        mentioned_user = deal.get('mentioned_user', '')
        
        # Try to get join status from group_data if available
        channel_id = deal.get('channel_id')
        if channel_id:
            full_channel_id = f"-100{channel_id}" if not str(channel_id).startswith("-100") else str(channel_id)
            if full_channel_id in group_data:
                joined_users = group_data[full_channel_id].get('joined_users', [])
                sender_clean = escrow_sender.lstrip("@").lower() if escrow_sender else ""
                if not mentioned_user:
                    mentioned_user = group_data[full_channel_id].get('mentioned_user', '')
                mentioned_clean = mentioned_user.lstrip("@").lower() if mentioned_user else ""
                
                initiator_joined = sender_clean in [u.lower() for u in joined_users]
                counterparty_joined = mentioned_clean in [u.lower() for u in joined_users]
        
        msg = build_deal_log_message(deal_id, buyer, seller, room_num, status, deposit_address, amount, token, escrow_sender, initiator_joined, counterparty_joined, mentioned_user)
        
        await bot.edit_message_text(
            chat_id=DEAL_LOG_CHANNEL_ID,
            message_id=log_message_id,
            text=msg,
            parse_mode="HTML"
        )
        log_info(f"Deal log updated for #{deal_id}: {status}")
    except Exception as e:
        log_error(f"Failed to update deal log: {e}")


async def check_user_banned_in_room(user_id, channel_id):
    """Check if a user is banned in a specific room."""
    global userbot_client
    if userbot_client is None:
        await init_userbot()
    
    try:
        full_channel_id = int(f"-100{channel_id}")
        from telethon.tl.functions.channels import GetParticipantRequest
        from telethon.tl.types import ChannelParticipantBanned
        try:
            participant = await userbot_client(GetParticipantRequest(
                channel=full_channel_id,
                participant=user_id
            ))
            if isinstance(participant.participant, ChannelParticipantBanned):
                return True
            return False
        except Exception:
            return False
    except Exception:
        return False


async def get_free_room_for_users(sender_user_id, mentioned_user_id):
    """Get a free room where both users are not banned and the group still exists."""
    global userbot_client
    if userbot_client is None:
        await init_userbot()
    
    for room_num, room_data in rooms.items():
        if room_data.get('status') == 'free':
            channel_id = room_data.get('channel_id')
            if channel_id:
                # First verify the group still exists
                try:
                    full_channel_id = int(f"-100{channel_id}")
                    await userbot_client.get_entity(full_channel_id)
                except Exception:
                    # Group doesn't exist, skip this room
                    log_warning(f"Room {room_num} group not accessible, skipping")
                    continue
                
                sender_banned = await check_user_banned_in_room(sender_user_id, channel_id)
                mentioned_banned = await check_user_banned_in_room(mentioned_user_id, channel_id)
                if not sender_banned and not mentioned_banned:
                    return room_num, room_data
    return None, None


def get_free_room():
    """Get a free room from the pool."""
    for room_num, room_data in rooms.items():
        if room_data.get('status') == 'free':
            return room_num, room_data
    return None, None


def mark_room_busy(room_num, deal_id, sender_username, mentioned_username):
    """Mark a room as busy with a deal."""
    if room_num in rooms:
        rooms[room_num]['status'] = 'busy'
        rooms[room_num]['current_deal_id'] = deal_id
        rooms[room_num]['sender_user'] = sender_username
        rooms[room_num]['mentioned_user'] = mentioned_username
        save_rooms()


def mark_room_free(room_num):
    """Mark a room as free after deal completion."""
    if room_num in rooms:
        rooms[room_num]['status'] = 'free'
        rooms[room_num]['current_deal_id'] = None
        rooms[room_num]['sender_user'] = None
        rooms[room_num]['mentioned_user'] = None
        save_rooms()


def get_room_by_channel_id(channel_id):
    """Find room number by channel ID."""
    channel_str = str(channel_id)
    for room_num, room_data in rooms.items():
        if str(room_data.get('channel_id')) == channel_str:
            return room_num
        full_id = f"-100{room_data.get('channel_id')}"
        if full_id == channel_str:
            return room_num
    return None


def generate_deal_id():
    return f"D{random.randint(1000, 9999)}"


def parse_deal_form(text):
    """Parse the filled deal form and extract details.
    Returns None if the form format is not matched properly."""
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
            # Strip $ sign from amount (e.g., "1000$" or "$1000" -> "1000")
            data['amount_usdt'] = value.replace('$', '').strip()
        elif 'amount' in key and 'usdc' in key.lower():
            # Strip $ sign from amount (e.g., "1000$" or "$1000" -> "1000")
            data['amount_usdc'] = value.replace('$', '').strip()
        elif 'amount' in key and 'inr' in key.lower():
            data['amount_inr'] = value
        elif 'payment' in key:
            data['payment_method'] = value
        elif 'time' in key:
            data['time'] = value

    # Strict validation: ALL fields must be present and non-empty
    # Required: seller, buyer, crypto amount (USDT or USDC), INR amount,
    # payment method, and time
    if not data.get('seller') or not data.get('buyer'):
        return None

    # Crypto amount (USDT or USDC) must be present and a valid positive number
    amount_usdt = data.get('amount_usdt', '')
    amount_usdc = data.get('amount_usdc', '')
    has_valid_crypto_amount = False
    for amount_str in [amount_usdt, amount_usdc]:
        if amount_str:
            try:
                amount_val = float(amount_str.replace(',', ''))
                if amount_val > 0:
                    has_valid_crypto_amount = True
                    break
            except (ValueError, TypeError):
                continue

    if not has_valid_crypto_amount:
        return None

    # INR amount must be present and non-empty
    if not data.get('amount_inr'):
        return None

    # Payment method must be present and non-empty
    if not data.get('payment_method'):
        return None

    # Time must be present and non-empty
    if not data.get('time'):
        return None

    return data


def get_network_display_name(network):
    """Get display name for network."""
    mapping = {
        'BSC': 'BEP20',
        'POLYGON': 'POLYGON',
        'SOL': 'SOLANA',
        'USDC_BSC': 'BEP20',
        'USDC_POLYGON': 'POLYGON',
        'USDC_SOL': 'SOLANA'
    }
    return mapping.get(network, network)


def get_network_buttons(deal_id, currency="USDT"):
    """Create network selection buttons based on currency."""
    if currency == "USDC":
        keyboard = [
            [
                InlineKeyboardButton(
                    "USDC[BSC]", callback_data=f"network_{deal_id}_USDC_BSC",
                    style="primary"
                ),
                InlineKeyboardButton(
                    "USDC[POLYGON]", callback_data=f"network_{deal_id}_USDC_POLYGON",
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    "USDC[SOL]", callback_data=f"network_{deal_id}_USDC_SOL",
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    "Cancel", callback_data=f"cancel_{deal_id}",
                    style="danger"
                )
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "USDT[BSC]", callback_data=f"network_{deal_id}_BSC",
                    style="primary"
                ),
                InlineKeyboardButton(
                    "USDT[POLYGON]", callback_data=f"network_{deal_id}_POLYGON",
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    "USDT[SOL]", callback_data=f"network_{deal_id}_SOL",
                    style="primary"
                )
            ],
            [
                InlineKeyboardButton(
                    "Cancel", callback_data=f"cancel_{deal_id}",
                    style="danger"
                )
            ]
        ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_only_button(deal_id):
    """Create cancel-only button."""
    keyboard = [[
        InlineKeyboardButton("Cancel", callback_data=f"cancel_{deal_id}", style="danger")
    ]]
    return InlineKeyboardMarkup(keyboard)


def calculate_escrow_fee(amount_str):
    """Calculate escrow fee: 0.5 or 0.2% of amount, whichever higher."""
    try:
        amount = float(amount_str.replace(',', '').strip())
        percentage_fee = amount * 0.002
        return max(0.5, percentage_fee)
    except (ValueError, AttributeError):
        return 0.5


def get_confirm_buttons(deal_id):
    """Create confirmation buttons for seller and buyer."""
    keyboard = [
        [
            InlineKeyboardButton(
                "Confirm[Seller]", callback_data=f"confirm_{deal_id}_seller"
            ),
            InlineKeyboardButton(
                "Confirm[Buyer]", callback_data=f"confirm_{deal_id}_buyer"
            )
        ],
        [
            InlineKeyboardButton(
                "Cancel", callback_data=f"cancel_{deal_id}",
                style="danger"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_deposit_buttons(deal_id):
    """Create buttons for deposit message."""
    keyboard = [
        [
            InlineKeyboardButton(
                "I HAVE PAID", callback_data=f"ihavepaid_{deal_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "CONFIRM[ADMIN]", callback_data=f"adminconfirm_{deal_id}"
            ),
            InlineKeyboardButton(
                "CANCEL", callback_data=f"depositcancel_{deal_id}",
                style="danger"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_payment_check_buttons(deal_id):
    """Create buttons for payment checking message."""
    keyboard = [
        [
            InlineKeyboardButton(
                "Confirm[Admin]", callback_data=f"adminconfirm_{deal_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "Cancel", callback_data=f"admincancel_{deal_id}",
                style="danger"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_bsc_deposit_info():
    """Get rotating BSC deposit address and QR image."""
    global bsc_address_index
    address = BSC_DEPOSIT_ADDRESSES[bsc_address_index]
    qr_image = BSC_QR_IMAGES[bsc_address_index]
    bsc_address_index = (bsc_address_index + 1) % len(BSC_DEPOSIT_ADDRESSES)
    return address, qr_image


def get_polygon_deposit_info():
    """Get rotating Polygon deposit address and QR image."""
    global polygon_address_index
    address = POLYGON_DEPOSIT_ADDRESSES[polygon_address_index]
    qr_image = POLYGON_QR_IMAGES[polygon_address_index]
    polygon_address_index = (polygon_address_index + 1) % len(POLYGON_DEPOSIT_ADDRESSES)
    return address, qr_image


def get_sol_deposit_info():
    """Get rotating Solana deposit address and QR image."""
    global sol_address_index
    address = SOL_DEPOSIT_ADDRESSES[sol_address_index]
    qr_image = SOL_QR_IMAGES[sol_address_index]
    sol_address_index = (sol_address_index + 1) % len(SOL_DEPOSIT_ADDRESSES)
    return address, qr_image


def get_usdc_bsc_deposit_info():
    """Get rotating USDC BSC deposit address and QR image."""
    global usdc_bsc_address_index
    address = USDC_BSC_DEPOSIT_ADDRESSES[usdc_bsc_address_index]
    qr_image = USDC_BSC_QR_IMAGES[usdc_bsc_address_index]
    usdc_bsc_address_index = (usdc_bsc_address_index + 1) % len(USDC_BSC_DEPOSIT_ADDRESSES)
    return address, qr_image


def build_deposit_message(deal, deal_id):
    """Build the deposit message for seller."""
    currency = deal['currency']
    network = deal.get('network', 'BSC')
    network_name = get_network_display_name(network)
    amount = deal.get('amount_crypto', '0')
    seller = deal['seller']

    # Check if deal already has deposit address assigned (avoid re-rotation)
    if deal.get('deposit_address'):
        deposit_address = deal['deposit_address']
        qr_image = deal.get('qr_image')
        
        # If qr_image is missing, try to look it up based on the address
        if not qr_image:
            fixed_index = deal.get('fixed_address_index')
            if fixed_index is not None:
                if network == "BSC" and fixed_index < len(BSC_QR_IMAGES):
                    qr_image = BSC_QR_IMAGES[fixed_index]
                elif network == "POLYGON" and fixed_index < len(POLYGON_QR_IMAGES):
                    qr_image = POLYGON_QR_IMAGES[fixed_index]
                elif network == "SOL" and fixed_index < len(SOL_QR_IMAGES):
                    qr_image = SOL_QR_IMAGES[fixed_index]
                elif network == "USDC_BSC" and fixed_index < len(USDC_BSC_QR_IMAGES):
                    qr_image = USDC_BSC_QR_IMAGES[fixed_index]
            # If still no qr_image, try to find it by matching deposit address
            if not qr_image:
                if network == "BSC":
                    for i, addr in enumerate(BSC_DEPOSIT_ADDRESSES):
                        if addr.lower() == deposit_address.lower():
                            qr_image = BSC_QR_IMAGES[i]
                            break
                elif network == "POLYGON":
                    for i, addr in enumerate(POLYGON_DEPOSIT_ADDRESSES):
                        if addr.lower() == deposit_address.lower():
                            qr_image = POLYGON_QR_IMAGES[i]
                            break
                elif network == "SOL":
                    for i, addr in enumerate(SOL_DEPOSIT_ADDRESSES):
                        if addr.lower() == deposit_address.lower():
                            qr_image = SOL_QR_IMAGES[i]
                            break
                elif network == "USDC_BSC":
                    for i, addr in enumerate(USDC_BSC_DEPOSIT_ADDRESSES):
                        if addr.lower() == deposit_address.lower():
                            qr_image = USDC_BSC_QR_IMAGES[i]
                            break
                elif network == "USDC_POLYGON":
                    qr_image = USDC_POLYGON_QR_IMAGE
                elif network == "USDC_SOL":
                    qr_image = USDC_SOL_QR_IMAGE
            if qr_image:
                deal['qr_image'] = qr_image
    else:
        # Check if admin has pre-fixed an address index
        fixed_index = deal.get('fixed_address_index')
        
        if network == "BSC":
            if fixed_index is not None and fixed_index < len(BSC_DEPOSIT_ADDRESSES):
                deposit_address = BSC_DEPOSIT_ADDRESSES[fixed_index]
                qr_image = BSC_QR_IMAGES[fixed_index]
            else:
                deposit_address, qr_image = get_bsc_deposit_info()
            deal['deposit_address'] = deposit_address
            deal['qr_image'] = qr_image
        elif network == "POLYGON":
            if fixed_index is not None and fixed_index < len(POLYGON_DEPOSIT_ADDRESSES):
                deposit_address = POLYGON_DEPOSIT_ADDRESSES[fixed_index]
                qr_image = POLYGON_QR_IMAGES[fixed_index]
            else:
                deposit_address, qr_image = get_polygon_deposit_info()
            deal['deposit_address'] = deposit_address
            deal['qr_image'] = qr_image
        elif network == "SOL":
            if fixed_index is not None and fixed_index < len(SOL_DEPOSIT_ADDRESSES):
                deposit_address = SOL_DEPOSIT_ADDRESSES[fixed_index]
                qr_image = SOL_QR_IMAGES[fixed_index]
            else:
                deposit_address, qr_image = get_sol_deposit_info()
            deal['deposit_address'] = deposit_address
            deal['qr_image'] = qr_image
        elif network == "USDC_BSC":
            if fixed_index is not None and fixed_index < len(USDC_BSC_DEPOSIT_ADDRESSES):
                deposit_address = USDC_BSC_DEPOSIT_ADDRESSES[fixed_index]
                qr_image = USDC_BSC_QR_IMAGES[fixed_index]
            else:
                deposit_address, qr_image = get_usdc_bsc_deposit_info()
            deal['deposit_address'] = deposit_address
            deal['qr_image'] = qr_image
        elif network == "USDC_POLYGON":
            deposit_address = USDC_POLYGON_DEPOSIT_ADDRESS
            qr_image = USDC_POLYGON_QR_IMAGE
            deal['deposit_address'] = deposit_address
            deal['qr_image'] = qr_image
        elif network == "USDC_SOL":
            deposit_address = USDC_SOL_DEPOSIT_ADDRESS
            qr_image = USDC_SOL_QR_IMAGE
            deal['deposit_address'] = deposit_address
            deal['qr_image'] = qr_image
        else:
            deposit_address = DEPOSIT_ADDRESSES.get(network, '')
            qr_image = None
            deal['deposit_address'] = deposit_address
            deal['qr_image'] = qr_image

    msg = (
        f"Deal [#{deal_id}]\n"
        f"NOTE: {seller} [Seller] <b>DEPOSIT EXACT</b> "
        f"<b><u>{amount}</u></b> <b>{currency}</b>. "
        f"DO NOT INCLUDE NETWORK FEE, make sure the amount received is "
        f"exact!\n"
        f"<b>Example</b>: If your withdrawal fee is 0.2 {currency} then send "
        f"<b><u>{float(str(amount).replace(',', '')) + 0.2:.1f}</u></b>{currency} so the received "
        f"amount is <b><u>{amount}</u></b> {currency}\n\n"
        f"Deposit Address: <code>{deposit_address}</code>\n"
        f"Chain: <code>{network_name}</code>\n\n"
        f"Please click 'I Have Paid' <b>ONLY</b> when you have made the "
        f"Payment."
    )

    return msg


def build_deal_summary(deal, deal_id, both_confirmed=False):
    """Build the deal summary message."""
    currency = deal['currency']
    network_name = get_network_display_name(deal.get('network', ''))
    escrow_fee = calculate_escrow_fee(deal.get('amount_crypto', '0'))

    seller_check = "✅" if deal.get('seller_confirmed') else ""
    buyer_check = "✅" if deal.get('buyer_confirmed') else ""

    if deal.get('seller_confirmed') and deal.get('buyer_confirmed'):
        confirm_status = "Both Confirmed!!"
    elif deal.get('seller_confirmed'):
        confirm_status = "Seller Confirmed!! Waiting for Buyer confirmation..."
    elif deal.get('buyer_confirmed'):
        confirm_status = "Buyer Confirmed!! Waiting for Seller confirmation..."
    else:
        confirm_status = ""

    payment_details = deal.get('payment_details', '')
    payment_type = deal.get('payment_details_type', 'text')

    msg = (
        f"Deal [ID #{deal_id}]. Both parties, please review the deal details "
        f"below carefully and confirm if everything is correct.\n\n"
        f"⚠️BOTH of you <b>DO NOT MAKE ANY PAYMENT</b> until both parties "
        f"have confirmed the details below and the bot prompts you to do so."
        f"\n\n"
        f"➤ <b>{currency} Seller:</b> {deal['seller']} {seller_check}\n"
        f"➤ <b>{currency} Buyer:</b> {deal['buyer']} {buyer_check}\n"
        f"➤ <b>Token:</b> {currency}\n"
        f"➤ <b>Chain:</b> {network_name}\n"
        f"➤ <b>Amount[{currency}]:</b> {deal.get('amount_crypto', '')}\n"
        f"➤ <b>Amount[INR]:</b> {deal.get('amount_inr', '')}\n"
        f"➤ <b>Payment Method:</b> {deal.get('payment_method', '')}\n"
        f"➤ <b>Total Escrow Fees[{currency}]:</b> {escrow_fee:.2f}\n"
        f"➤ <b>Release Address:</b> {deal.get('buyer_address', '')}\n"
        f"➤ <b>Refund Address:</b> {deal.get('seller_address', '')}\n"
        f"➤ <b>Time[Minute]:</b> {deal.get('time', '')}\n"
        f"➤ <b>Payment Details:</b>\n"
    )

    if payment_type == 'text':
        msg += f"{payment_details}\n\n"
    else:
        msg += "[See attached image]\n\n"

    if confirm_status:
        msg += f"{confirm_status}"

    if not both_confirmed:
        msg += (
            f"\n\n🚫 <b>IMPORTANT:</b> {deal['seller']}, do <u>NOT</u> deposit "
            f"any {currency}s to the addresses above.\n"
            f"You will receive a separate <b>Escrow Deposit</b> Address after "
            f"confirming the deal details.\n\n"
            f"🔹 <b>Note to Buyer</b> ({deal['buyer']}): You can only withdraw "
            f"{currency} on the <b>{network_name}</b> network as selected by "
            f"the seller."
        )

    return msg


async def check_bsc_transactions(deposit_address, usdt_contract, monitoring_start_time=None):
    """Check BSC blockchain for USDT transactions to deposit address using RPC.
    
    Uses eth_getLogs to query ERC20 Transfer events to the deposit address.
    Tries multiple RPC endpoints with timeouts for reliability.
    
    Args:
        monitoring_start_time: Unix timestamp when monitoring started. Only transactions
                              after this time will be considered.
    """
    timeout = aiohttp.ClientTimeout(total=15)  # 15 second timeout
    
    for rpc_endpoint in BSC_RPC_ENDPOINTS:
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # First get the latest block number
                block_payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1
                }
                async with session.post(
                    rpc_endpoint,
                    json=block_payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        log_warning(f"BSC RPC {rpc_endpoint} error getting block number: {response.status}")
                        continue  # Try next endpoint
                    data = await response.json()
                    if "error" in data:
                        log_warning(f"BSC RPC {rpc_endpoint} error: {data['error']}")
                        continue  # Try next endpoint
                    latest_block = int(data["result"], 16)
                
                # Calculate from_block based on monitoring_start_time
                # BSC has ~3 second block time
                if monitoring_start_time:
                    seconds_ago = int(time.time()) - monitoring_start_time
                    blocks_ago = max(10, seconds_ago // 3 + 100)  # Add 100 blocks buffer
                    from_block = hex(latest_block - blocks_ago)
                else:
                    # Fallback: Query last 10000 blocks (~8 hours on BSC with 3s block time)
                    from_block = hex(latest_block - 10000)
                
                # Pad deposit address to 32 bytes for topic filter
                padded_address = "0x" + deposit_address[2:].lower().zfill(64)
                
                # Query for Transfer events TO the deposit address
                logs_payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getLogs",
                    "params": [{
                        "fromBlock": from_block,
                        "toBlock": "latest",
                        "address": usdt_contract,
                        "topics": [
                            TRANSFER_EVENT_TOPIC,
                            None,  # from address (any)
                            padded_address  # to address (our deposit address)
                        ]
                    }],
                    "id": 2
                }
                
                async with session.post(
                    rpc_endpoint,
                    json=logs_payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        log_warning(f"BSC RPC {rpc_endpoint} error getting logs: {response.status}")
                        continue  # Try next endpoint
                    data = await response.json()
                    if "error" in data:
                        log_warning(f"BSC RPC {rpc_endpoint} error: {data['error']}")
                        continue  # Try next endpoint
                    
                    logs = data.get("result", [])
                    if logs:
                        log_info(f"BSC RPC found {len(logs)} transactions for {deposit_address[:6]}...")
                        # Convert logs to a format similar to BSCScan API response
                        transactions = []
                        for log in logs:
                            # Extract amount from data (uint256)
                            amount_hex = log.get("data", "0x0")
                            amount_wei = int(amount_hex, 16) if amount_hex else 0
                            # USDT/USDC on BSC has 18 decimals
                            amount = amount_wei / (10 ** 18)
                            
                            # Extract from address from topics[1]
                            from_addr = "0x" + log["topics"][1][-40:] if len(log.get("topics", [])) > 1 else ""
                            
                            transactions.append({
                                "hash": log.get("transactionHash", ""),
                                "from": from_addr,
                                "to": deposit_address,
                                "value": str(amount_wei),
                                "tokenDecimal": "18",
                                "blockNumber": str(int(log.get("blockNumber", "0x0"), 16))
                            })
                        return transactions
                    return []  # Successfully queried but no transactions found
        except asyncio.TimeoutError:
            log_warning(f"BSC RPC {rpc_endpoint} timeout")
            continue  # Try next endpoint
        except Exception as e:
            log_warning(f"BSC RPC {rpc_endpoint} error: {e}")
            continue  # Try next endpoint
    
    log_error("All BSC RPC endpoints failed")
    return []


async def check_polygon_transactions(deposit_address, usdt_contract, monitoring_start_time=None):
    """Check Polygon blockchain for USDT/USDC transactions using RPC.
    
    Uses eth_getLogs to query ERC20 Transfer events to the deposit address.
    Tries multiple RPC endpoints with timeouts for reliability.
    
    Args:
        monitoring_start_time: Unix timestamp when monitoring started. Only transactions
                              after this time will be considered.
    """
    timeout = aiohttp.ClientTimeout(total=15)
    
    for rpc_endpoint in POLYGON_RPC_ENDPOINTS:
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                block_payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1
                }
                async with session.post(
                    rpc_endpoint,
                    json=block_payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        log_warning(f"Polygon RPC {rpc_endpoint} error getting block number: {response.status}")
                        continue
                    data = await response.json()
                    if "error" in data:
                        log_warning(f"Polygon RPC {rpc_endpoint} error: {data['error']}")
                        continue
                    latest_block = int(data["result"], 16)
                
                if monitoring_start_time:
                    seconds_ago = int(time.time()) - monitoring_start_time
                    blocks_ago = max(10, seconds_ago // 2 + 100)
                    from_block = hex(latest_block - blocks_ago)
                else:
                    from_block = hex(latest_block - 10000)
                
                padded_address = "0x" + deposit_address[2:].lower().zfill(64)
                
                logs_payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getLogs",
                    "params": [{
                        "fromBlock": from_block,
                        "toBlock": "latest",
                        "address": usdt_contract,
                        "topics": [
                            TRANSFER_EVENT_TOPIC,
                            None,
                            padded_address
                        ]
                    }],
                    "id": 2
                }
                
                async with session.post(
                    rpc_endpoint,
                    json=logs_payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        log_warning(f"Polygon RPC {rpc_endpoint} error getting logs: {response.status}")
                        continue
                    data = await response.json()
                    if "error" in data:
                        log_warning(f"Polygon RPC {rpc_endpoint} error: {data['error']}")
                        continue
                    
                    logs = data.get("result", [])
                    if logs:
                        log_info(f"Polygon RPC found {len(logs)} transactions for {deposit_address[:10]}...")
                        transactions = []
                        for log in logs:
                            amount_hex = log.get("data", "0x0")
                            amount_wei = int(amount_hex, 16) if amount_hex else 0
                            amount = amount_wei / (10 ** 6)
                            
                            from_addr = "0x" + log["topics"][1][-40:] if len(log.get("topics", [])) > 1 else ""
                            
                            transactions.append({
                                "hash": log.get("transactionHash", ""),
                                "from": from_addr,
                                "to": deposit_address,
                                "value": str(amount_wei),
                                "tokenDecimal": "6",
                                "blockNumber": str(int(log.get("blockNumber", "0x0"), 16))
                            })
                        return transactions
                    return []
        except asyncio.TimeoutError:
            log_warning(f"Polygon RPC {rpc_endpoint} timeout")
            continue
        except Exception as e:
            log_warning(f"Polygon RPC {rpc_endpoint} error: {e}")
            continue
    
    log_error("All Polygon RPC endpoints failed")
    return []


async def check_solana_transactions(deposit_address, monitoring_start_time=None):
    """Check Solana blockchain for USDT transactions using Helius API.
    
    Args:
        monitoring_start_time: Unix timestamp when monitoring started. Only transactions
                              after this time will be considered.
    """
    if HELIUS_API_KEY:
        rpc_url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    else:
        rpc_url = "https://api.mainnet-beta.solana.com"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [deposit_address, {"limit": 10}]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                rpc_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    signatures = data.get("result", [])
                    
                    # Filter signatures by blockTime if monitoring_start_time is set
                    if monitoring_start_time:
                        signatures = [sig for sig in signatures if sig.get("blockTime", 0) >= monitoring_start_time]

                    transactions = []
                    for sig in signatures:
                        tx_payload = {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getTransaction",
                            "params": [
                                sig.get("signature"),
                                {"encoding": "jsonParsed",
                                 "maxSupportedTransactionVersion": 0}
                            ]
                        }
                        async with session.post(
                            rpc_url,
                            json=tx_payload,
                            headers={"Content-Type": "application/json"}
                        ) as tx_resp:
                            if tx_resp.status == 200:
                                tx_data = await tx_resp.json()
                                if tx_data.get("result"):
                                    transactions.append(tx_data["result"])

                    return transactions
    except Exception as e:
        log_error(f"Solana/Helius API error: {e}")

    return []


async def get_transactions_for_network(network, deposit_address, monitoring_start_time=None):
    """Get transactions based on network type.
    
    Args:
        monitoring_start_time: Unix timestamp when monitoring started. Only transactions
                              after this time will be considered.
    """
    if network.startswith("USDC_"):
        base_network = network.replace("USDC_", "")
        contract = USDC_CONTRACTS.get(base_network, "")
    else:
        base_network = network
        contract = USDT_CONTRACTS.get(network, "")

    log_info(f"Checking {base_network} for deposits to {deposit_address[:10]}... contract: {contract[:10]}...")

    if base_network == "BSC":
        txs = await check_bsc_transactions(deposit_address, contract, monitoring_start_time)
        log_info(f"BSC check returned {len(txs)} transactions")
        return txs
    elif base_network == "POLYGON":
        txs = await check_polygon_transactions(deposit_address, contract, monitoring_start_time)
        log_info(f"Polygon check returned {len(txs)} transactions")
        return txs
    elif base_network == "SOL":
        txs = await check_solana_transactions(deposit_address, monitoring_start_time)
        log_info(f"Solana check returned {len(txs)} transactions")
        return txs

    log_warning(f"Unknown network: {network}")
    return []


def parse_transaction_amount(tx, network):
    """Parse transaction amount from API response."""
    # Get base network for USDC networks
    base_network = network.replace("USDC_", "") if network.startswith("USDC_") else network

    if base_network in ["BSC", "POLYGON"]:
        value = tx.get("value", "0")
        decimals = int(tx.get("tokenDecimal", "18"))
        amount = int(value) / (10 ** decimals)
        return amount
    elif base_network == "SOL":
        try:
            meta = tx.get("meta", {})
            pre_balances = meta.get("preBalances", [])
            post_balances = meta.get("postBalances", [])
            if pre_balances and post_balances and len(post_balances) > 1:
                received = post_balances[1] - pre_balances[1]
                if received > 0:
                    return received / 1e9

            post_token = meta.get("postTokenBalances", [])
            for post in post_token:
                token_amount = post.get("uiTokenAmount", {})
                amount = float(token_amount.get("uiAmount", 0) or 0)
                if amount > 0:
                    return amount
        except Exception:
            pass
        return 0

    return 0


def get_deal_buttons(deal_id):
    """Create buttons for deal completion message."""
    keyboard = [
        [
            InlineKeyboardButton(
                "Release Payment", callback_data=f"release_{deal_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "Partial Release Payment", callback_data=f"partial_{deal_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "Dispute", callback_data=f"dispute_{deal_id}"
            ),
            InlineKeyboardButton(
                "CANCEL", callback_data=f"dealcancel_{deal_id}",
                style="danger"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_payment_detected_message(deal_id, amount, total, deal_amount, curr):
    """Build payment detected message."""
    confirmations = "48/30"

    msg = (
        f"<b><i>Deal</i></b> #{deal_id}\n\n"
        f"<b>Payment Detected Successfully</b>\n\n"
        f"Amount: <b>{amount:.2f} {curr}</b>\n"
        f"Total Amount Received: <b>{total:.2f} {curr}</b>\n"
        f"Current Confirmations: {confirmations}\n"
    )

    if total > float(deal_amount):
        excess = total - float(deal_amount)
        msg += (
            f"\n⚠️ <b>Overpayment Detected!</b>\n"
            f"Excess Amount: <b>{excess:.2f} {curr}</b>\n"
        )

    msg += (
        "\nNOTE: Please be advised that if you send INR before the payment "
        "is confirmed, you are solely responsible for your loss!"
    )

    return msg


def build_usdt_received_message(deal, deal_id, received_amount):
    """Build USDT received message."""
    currency = deal['currency']
    deal_amount = float(deal.get('amount_crypto', '0'))
    escrow_fee = calculate_escrow_fee(str(deal_amount))
    to_release = received_amount - escrow_fee
    inr_amount = deal.get('amount_inr', '0')
    buyer = deal['buyer']
    seller = deal['seller']

    msg = (
        f"<b><u>Deal</u></b> #{deal_id}\n\n"
        f"<b>USDT RECEIVED | SEND INR.</b>\n"
        f"Amount Received: <b><u>{received_amount:.2f} {currency}</u></b>\n"
        f"Deal Amount: <b><u>{deal_amount:.2f} {currency}</u></b>\n"
        f"To Be Released: <b><u>{to_release:.2f} {currency}</u></b>\n"
        f"Amount to be Sent: <b><u>{inr_amount} INR</u></b>\n"
        f"Escrow Fee: <b><u>{escrow_fee:.2f} {currency}</u></b>\n\n"
        f"{buyer} & {seller} proceed with your deal.\n\n"
        f"{seller} release payment <b><u>ONLY</u></b> after Deal Completion.\n"
        f"Please note that this process is irreversible."
    )

    return msg


def build_payment_details_message(deal, deal_id):
    """Build payment details message for buyer."""
    payment_details = deal.get('payment_details', '')
    payment_type = deal.get('payment_details_type', 'text')
    buyer = deal['buyer']

    msg = (
        f"<b>Deal</b> #{deal_id}\n\n"
        f"<b>Payment Details:</b>\n"
    )

    if payment_type == 'text':
        msg += f"{payment_details}\n\n"
    else:
        msg += "[See image above]\n\n"

    msg += (
        f"{buyer} pay INR to the above details to complete the deal.\n\n"
        f"⚠️ Only use payment details provided in this Escrow Group for the "
        f"transaction! Do <b>NOT</b> trust any payment requests or details "
        f"sent by the seller via DM."
    )

    return msg


async def update_current_stage_button(bot, deal, chat_id, new_msg_id):
    """Update the CURRENT STAGE button on the pinned message to point to the latest message."""
    summary_msg_id = deal.get('summary_msg_id')
    if not summary_msg_id:
        return

    try:
        channel_id_str = str(chat_id).replace("-100", "")
        msg_link = f"https://t.me/c/{channel_id_str}/{new_msg_id}"
        current_stage_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("CURRENT STAGE", url=msg_link)]
        ])
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=summary_msg_id,
            reply_markup=current_stage_keyboard
        )
    except Exception:
        pass


async def monitor_blockchain(deal_id, chat_id, bot):
    """Monitor blockchain for incoming transactions."""
    global deals, active_monitors

    if deal_id not in deals:
        log_warning(f"Deal {deal_id} not found in deals")
        return

    deal = deals[deal_id]
    network = deal.get('network', 'BSC')
    deposit_address = deal.get('deposit_address', DEPOSIT_ADDRESSES.get(network, ''))
    deal_amount = deal.get('amount_crypto', '0')
    currency = deal['currency']
    monitoring_start_time = deal.get('monitoring_start_time')
    start_time = asyncio.get_event_loop().time()
    check_interval = 30
    max_duration = 300

    log_info(f"Starting blockchain monitoring for deal {deal_id}: network={network}, address={deposit_address}, amount={deal_amount} {currency}")

    while deal_id in active_monitors:
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > max_duration:
            break

        transactions = await get_transactions_for_network(
            network, deposit_address, monitoring_start_time
        )

        total_received = 0
        latest_amount = 0

        for tx in transactions:
            if tx.get("to", "").lower() == deposit_address.lower():
                amount = parse_transaction_amount(tx, network)
                total_received += amount
                if amount > latest_amount:
                    latest_amount = amount

        if total_received > 0:
            deal['received_amount'] = total_received
            deal['status'] = 'payment_received'
            save_deals()

            # Update deal log - Deposit Detected with amount
            await update_deal_log(bot, deal_id, f"Deposit Detected [ {total_received} {currency} ]")

            detected_msg = build_payment_detected_message(
                deal_id, latest_amount, total_received, deal_amount, currency
            )
            await bot.send_message(
                chat_id=chat_id,
                text=detected_msg,
                parse_mode="HTML"
            )

            # Update deal log - Payment Received
            await update_deal_log(bot, deal_id, "Payment Received")

            received_msg = build_usdt_received_message(
                deal, deal_id, total_received
            )
            await bot.send_message(
                chat_id=chat_id,
                text=received_msg,
                parse_mode="HTML",
                reply_markup=get_deal_buttons(deal_id)
            )

            payment_type = deal.get('payment_details_type', 'text')
            if payment_type == 'photo':
                photo_id = deal.get('payment_details')
                details_msg = build_payment_details_message(deal, deal_id)
                sent_details = await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_id,
                    caption=details_msg,
                    parse_mode="HTML"
                )
            else:
                details_msg = build_payment_details_message(deal, deal_id)
                sent_details = await bot.send_message(
                    chat_id=chat_id,
                    text=details_msg,
                    parse_mode="HTML"
                )

            await update_current_stage_button(bot, deal, chat_id, sent_details.message_id)

            if deal_id in active_monitors:
                del active_monitors[deal_id]
            break

        await asyncio.sleep(check_interval)

    if deal_id in active_monitors:
        del active_monitors[deal_id]


async def init_userbot():
    global userbot_client
    userbot_client = TelegramClient("userbot_session", API_ID, API_HASH)
    await userbot_client.start(phone=PHONE)
    log_info("Userbot connected")
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
            log_error(f"Room {room_number}: Could not find chat_id")
            return None, room_number, None

        try:
            migrated = await userbot_client(MigrateChatRequest(
                chat_id=chat_id
            ))

            channel_id = None
            if hasattr(migrated, 'chats'):
                for chat_obj in migrated.chats:
                    if isinstance(chat_obj, Channel):
                        channel_id = chat_obj.id
                        break

            if channel_id is None:
                await asyncio.sleep(1)
                dialogs = await userbot_client.get_dialogs(limit=5)
                for dialog in dialogs:
                    if dialog.title == group_title:
                        entity = dialog.entity
                        if isinstance(entity, Channel):
                            channel_id = entity.id
                            break

            if channel_id is None:
                channel_id = chat_id
        except Exception as migrate_error:
            log_warning(f"Room {room_number}: Migration error - {migrate_error}")
            channel_id = chat_id

        try:
            await userbot_client(EditChatAboutRequest(
                peer=channel_id,
                about="Join @CryptoIndiaUnited"
            ))
        except Exception as about_error:
            log_warning(f"Room {room_number}: Could not set description - {about_error}")

        try:
            from telethon.tl.functions.channels import EditChatDefaultBannedRightsRequest
            default_banned_rights = ChatBannedRights(
                until_date=None,
                view_messages=False,
                send_messages=False,
                send_media=False,
                send_stickers=False,
                send_gifs=False,
                send_games=False,
                send_inline=False,
                embed_links=False,
                send_polls=False,
                change_info=True,
                invite_users=True,
                pin_messages=True
            )
            await userbot_client(EditChatDefaultBannedRightsRequest(
                peer=channel_id,
                banned_rights=default_banned_rights
            ))
        except Exception as perm_error:
            log_warning(f"Room {room_number}: Could not set default permissions - {perm_error}")

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
        except Exception as admin_error:
            log_warning(f"Room {room_number}: Could not promote bot - {admin_error}")

        try:
            founder_rights = ChatAdminRights(
                change_info=True,
                post_messages=True,
                edit_messages=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                add_admins=True,
                anonymous=False,
                manage_call=True,
                other=True
            )
            resolved = await userbot_client(
                ResolveUsernameRequest(username='TheTigerCubs')
            )
            if resolved.users:
                founder_user = resolved.users[0]
                try:
                    await userbot_client(InviteToChannelRequest(
                        channel=channel_id,
                        users=[founder_user]
                    ))
                except Exception:
                    pass
                await userbot_client(EditAdminRequest(
                    channel=channel_id,
                    user_id=founder_user.id,
                    admin_rights=founder_rights,
                    rank="Founder"
                ))
        except Exception as founder_error:
            log_warning(f"Room {room_number}: Could not add Founder - {founder_error}")

        try:
            userbot_rights = ChatAdminRights(
                change_info=True,
                post_messages=True,
                edit_messages=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                add_admins=True,
                anonymous=False,
                manage_call=True,
                other=True
            )
            me = await userbot_client.get_me()
            await userbot_client(EditAdminRequest(
                channel=channel_id,
                user_id=me.id,
                admin_rights=userbot_rights,
                rank="Admin"
            ))
        except Exception as userbot_error:
            log_warning(f"Room {room_number}: Could not set userbot role - {userbot_error}")

        try:
            await userbot_client(ToggleJoinRequestRequest(
                channel=channel_id,
                enabled=True
            ))
        except Exception as toggle_error:
            log_warning(f"Room {room_number}: Could not enable join requests - {toggle_error}")

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
        log_error(f"Room {room_number}: Error creating group - {e}")
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
    global deals, group_data

    query = update.callback_query
    data = query.data
    user = query.from_user
    user_id = user.id
    username = user.username.lower() if user.username else None

    # Handle review fix callbacks (admin only)
    if data.startswith("review_"):
        if user_id not in ADMIN_USER_IDS:
            await query.answer("Admin only!")
            return
        await handle_review_fix(query, data)
        return

    # Handle 2FA check callback - show user's 2FA code as popup
    if data.startswith("check2fa_"):
        parts = data.split("_")
        if len(parts) >= 3:
            target_user_id = parts[2]
            # Only the user who the button is for can check their 2FA
            if str(user_id) != target_user_id:
                await query.answer()
                return
            # Check if user has 2FA set
            if str(user_id) in user_2fa:
                code = user_2fa[str(user_id)].get("code", "")
                if code:
                    await query.answer(code, show_alert=True)
                else:
                    await query.answer()
            else:
                # No 2FA set - just acknowledge the button (shows loading then stops)
                await query.answer()
        else:
            await query.answer()
        return

    # Handle 2FA verification callback - grant message permission
    if data.startswith("verify2fa_"):
        parts = data.split("_")
        if len(parts) >= 3:
            chat_id = parts[1]
            target_user_id = parts[2]
            # Only the user who the button is for can verify
            if str(user_id) != target_user_id:
                await query.answer("This button is not for you!")
                return
            
            # Check if user has already verified - if so, ignore the button
            if chat_id in group_data:
                if "verified_2fa_users" in group_data[chat_id]:
                    if str(user_id) in group_data[chat_id]["verified_2fa_users"]:
                        await query.answer()
                        return
            
            await query.answer()
            
            # Grant message permission to the user using userbot
            try:
                # Convert chat_id to proper format for Telethon
                channel_id = int(chat_id)
                if channel_id < 0:
                    channel_id = int(str(channel_id).replace("-100", ""))
                
                # Grant send message permission
                unban_rights = ChatBannedRights(
                    until_date=None,
                    view_messages=False,
                    send_messages=False,
                    send_media=False,
                    send_stickers=False,
                    send_gifs=False,
                    send_games=False,
                    send_inline=False,
                    embed_links=False
                )
                await userbot_client(EditBannedRequest(
                    channel=channel_id,
                    participant=user_id,
                    banned_rights=unban_rights
                ))
                log_info(f"User {user_id} (@{username}) verified 2FA and granted message permission in {chat_id}")
            except Exception as e:
                log_error(f"Failed to grant message permission: {e}")
            
            # Track 2FA verification in group_data
            if chat_id in group_data:
                if "verified_2fa_users" not in group_data[chat_id]:
                    group_data[chat_id]["verified_2fa_users"] = []
                if str(user_id) not in group_data[chat_id]["verified_2fa_users"]:
                    group_data[chat_id]["verified_2fa_users"].append(str(user_id))
                    save_group_data()
        return

    # Handle show banned list callback - show banned users as popup
    if data == "show_banned_list":
        if user_id not in ADMIN_USER_IDS:
            await query.answer()
            return
        
        if not banned_users:
            await query.answer("No users are currently banned.", show_alert=True)
            return
        
        # Build the banned users list
        banned_list = []
        for ban_id, ban_data in banned_users.items():
            username = ban_data.get('username')
            if username:
                banned_list.append(f"@{username} ({ban_id})")
            else:
                banned_list.append(f"ID: {ban_id}")
        
        popup_text = "\n".join(banned_list)
        # Telegram popup has a character limit, truncate if needed
        if len(popup_text) > 200:
            popup_text = popup_text[:197] + "..."
        
        await query.answer(popup_text, show_alert=True)
        return

    await query.answer()

    if data == "switch_to_usdc":
        new_text = get_form_text("USDC")
        new_keyboard = get_form_keyboard("USDC")
        try:
            await query.edit_message_text(
                text=new_text,
                parse_mode="HTML",
                reply_markup=new_keyboard
            )
        except Exception:
            pass
        return

    if data == "switch_to_usdt":
        new_text = get_form_text("USDT")
        new_keyboard = get_form_keyboard("USDT")
        try:
            await query.edit_message_text(
                text=new_text,
                parse_mode="HTML",
                reply_markup=new_keyboard
            )
        except Exception:
            pass
        return

    if data.startswith("network_"):
        parts = data.split("_")
        deal_id = parts[1]
        network = parts[2]

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean and user_id not in ADMIN_USER_IDS:
            await query.answer("Only the seller can select the network!")
            return

        deal['network'] = network
        deal['status'] = 'pending_buyer_address'
        save_deals()

        # Update deal log
        await update_deal_log(context.bot, deal_id, "Network Selected")

        network_name = get_network_display_name(network)
        seller = deal['seller']
        buyer = deal['buyer']
        currency = deal['currency']

        new_text = (
            f"<b><i>Deal</i></b> #{deal_id}\n\n"
            f"<b>{seller}</b> [Seller] has selected "
            f"<b>{network_name}</b> as the deposit network for {currency}.\n\n"
            f"🔹<b>Note to Buyer ({buyer}):</b> You will only be able to "
            f"withdraw {currency} on the <b>{network_name}</b> network "
            f"as selected by the seller."
        )

        try:
            await query.edit_message_text(
                text=new_text,
                parse_mode="HTML",
                reply_markup=get_cancel_only_button(deal_id)
            )
        except Exception:
            pass

        chat_id = query.message.chat_id

        buyer_msg = (
            f"<b><u>Deal</u></b> #{deal_id}\n\n"
            f"{buyer} [Buyer] please <b>QUOTE</b> this message and reply "
            f"with your <b>{currency} {network_name}</b> address.\n"
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

    if data.startswith("confirm_"):
        parts = data.split("_")
        deal_id = parts[1]
        confirm_type = parts[2]

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()
        buyer_clean = deal['buyer'].lstrip('@').lower()

        if confirm_type == "seller":
            if username != seller_clean and user_id not in ADMIN_USER_IDS:
                await query.answer("Only the seller can confirm!")
                return
            deal['seller_confirmed'] = True
        elif confirm_type == "buyer":
            if username != buyer_clean and user_id not in ADMIN_USER_IDS:
                await query.answer("Only the buyer can confirm!")
                return
            deal['buyer_confirmed'] = True

        save_deals()

        both_confirmed = (
            deal.get('seller_confirmed') and deal.get('buyer_confirmed')
        )
        summary_text = build_deal_summary(deal, deal_id, both_confirmed)

        if both_confirmed:
            chat_id = query.message.chat_id
            payment_type = deal.get('payment_details_type', 'text')
            summary_msg_id = None

            if payment_type == 'photo':
                photo_id = deal.get('payment_details')
                await query.message.delete()
                sent = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_id,
                    caption=summary_text,
                    parse_mode="HTML"
                )
                summary_msg_id = sent.message_id
                deal['summary_msg_id'] = summary_msg_id
            else:
                try:
                    await query.edit_message_text(
                        text=summary_text,
                        parse_mode="HTML"
                    )
                    summary_msg_id = query.message.message_id
                    deal['summary_msg_id'] = summary_msg_id
                except Exception as edit_error:
                    log_warning(f"Could not edit message: {edit_error}")
                    summary_msg_id = query.message.message_id

            try:
                msg_to_pin = deal.get('summary_msg_id', summary_msg_id)
                await context.bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=msg_to_pin,
                    disable_notification=True
                )
            except Exception as pin_error:
                log_warning(f"Could not pin message: {pin_error}")

            deposit_text = build_deposit_message(deal, deal_id)
            save_deals()  # Save deposit_address immediately to prevent rotation issues
            network = deal.get('network', 'BSC')

            # Debug logging for QR image
            log_info(f"Deal #{deal_id} deposit: network={network}, qr_image={deal.get('qr_image')}, fixed_index={deal.get('fixed_address_index')}, deposit_address={deal.get('deposit_address')}")

            if network in ['BSC', 'POLYGON', 'SOL', 'USDC_BSC', 'USDC_POLYGON', 'USDC_SOL']:
                import os
                qr_image = deal.get('qr_image')
                sent_deposit = None
                if qr_image:
                    qr_path = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        qr_image
                    )
                    log_info(f"Deal #{deal_id} trying to send QR image: {qr_path}")
                    try:
                        with open(qr_path, 'rb') as qr_file:
                            sent_deposit = await context.bot.send_photo(
                                chat_id=chat_id,
                                photo=qr_file,
                                caption=deposit_text,
                                parse_mode="HTML",
                                reply_markup=get_deposit_buttons(deal_id)
                            )
                            log_info(f"Deal #{deal_id} QR image sent successfully")
                    except FileNotFoundError as e:
                        log_error(f"Deal #{deal_id} QR image not found: {qr_path}")
                else:
                    log_warning(f"Deal #{deal_id} no qr_image set in deal")
                if sent_deposit is None:
                    sent_deposit = await context.bot.send_message(
                        chat_id=chat_id,
                        text=deposit_text,
                        parse_mode="HTML",
                        reply_markup=get_deposit_buttons(deal_id)
                    )
            else:
                sent_deposit = await context.bot.send_message(
                    chat_id=chat_id,
                    text=deposit_text,
                    parse_mode="HTML",
                    reply_markup=get_deposit_buttons(deal_id)
                )

            deal['deposit_msg_id'] = sent_deposit.message_id
            deal['status'] = 'pending_deposit'
            deal['latest_msg_id'] = sent_deposit.message_id
            save_deals()

            # Update deal log
            await update_deal_log(context.bot, deal_id, "Deposit Address Sent")

            # Add CURRENT STAGE button to Both Confirmed message
            channel_id_str = str(chat_id).replace("-100", "")
            msg_link = f"https://t.me/c/{channel_id_str}/{sent_deposit.message_id}"
            current_stage_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("CURRENT STAGE", url=msg_link)]
            ])

            if payment_type == 'photo':
                try:
                    await context.bot.edit_message_reply_markup(
                        chat_id=chat_id,
                        message_id=summary_msg_id,
                        reply_markup=current_stage_keyboard
                    )
                except Exception:
                    pass
            else:
                try:
                    await context.bot.edit_message_reply_markup(
                        chat_id=chat_id,
                        message_id=summary_msg_id,
                        reply_markup=current_stage_keyboard
                    )
                except Exception:
                    pass
        else:
            payment_type = deal.get('payment_details_type', 'text')
            if payment_type == 'photo':
                photo_id = deal.get('payment_details')
                try:
                    await query.message.delete()
                except Exception:
                    pass
                sent = await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo_id,
                    caption=summary_text,
                    parse_mode="HTML",
                    reply_markup=get_confirm_buttons(deal_id)
                )
                deal['summary_msg_id'] = sent.message_id
                save_deals()
            else:
                try:
                    await query.edit_message_text(
                        text=summary_text,
                        parse_mode="HTML",
                        reply_markup=get_confirm_buttons(deal_id)
                    )
                except Exception:
                    pass
        return

    if data.startswith("ihavepaid_"):
        parts = data.split("_")
        deal_id = parts[1]

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean and user_id not in ADMIN_USER_IDS:
            await query.answer("Only the seller can click this button!")
            return

        deposit_text = build_deposit_message(deal, deal_id)
        try:
            if query.message.photo:
                await query.edit_message_caption(
                    caption=deposit_text,
                    parse_mode="HTML"
                )
            else:
                await query.edit_message_text(
                    text=deposit_text,
                    parse_mode="HTML"
                )
        except Exception:
            pass

        payment_check_msg = (
            f"<b><u>Deal</u></b> [#{deal_id}]\n\n"
            f"Payment will Be checked on Blockchain for next 5 mins. "
            f"You will be notified once payment is confirmed. Thanks!"
        )

        sent_check = await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=payment_check_msg,
            parse_mode="HTML",
            reply_markup=get_payment_check_buttons(deal_id)
        )

        deal['status'] = 'payment_checking'
        deal['monitoring_start_time'] = int(time.time())
        save_deals()

        # Update deal log
        await update_deal_log(context.bot, deal_id, "Payment Checking")

        await update_current_stage_button(
            context.bot, deal, query.message.chat_id, sent_check.message_id
        )

        active_monitors[deal_id] = True
        asyncio.create_task(
            monitor_blockchain(deal_id, query.message.chat_id, context.bot)
        )
        return

    if data.startswith("partial_"):
        parts = data.split("_")
        deal_id = parts[1]

        if deal_id not in deals:
            return

        await query.answer("Partial Release - Coming soon!")
        return

    if data.startswith("dispute_"):
        parts = data.split("_")
        deal_id = parts[1]

        if deal_id not in deals:
            return

        await query.answer("Dispute - Coming soon!")
        return

    if data.startswith("dealcancel_"):
        parts = data.split("_")
        deal_id = parts[1]

        if deal_id not in deals:
            try:
                await query.edit_message_text(
                    text="Deal has been cancelled.",
                    parse_mode="HTML"
                )
            except Exception:
                pass
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean and user_id not in ADMIN_USER_IDS:
            await query.answer("Only the seller can cancel the deal!")
            return

        if deal_id in active_monitors:
            del active_monitors[deal_id]

        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

        del deals[deal_id]
        save_deals()

        try:
            await query.edit_message_text(
                text="Deal has been cancelled.",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    if data.startswith("adminconfirm_"):
        parts = data.split("_")
        deal_id = parts[1]

        user_id = query.from_user.id
        if ADMIN_USER_IDS and user_id not in ADMIN_USER_IDS:
            await query.answer("Only admins can confirm!")
            return

        if deal_id not in deals:
            return

        deal = deals[deal_id]

        if deal_id in active_monitors:
            del active_monitors[deal_id]

        # Get deal amount with fallback to amount_usdt/amount_usdc if amount_crypto is empty
        amount_str = deal.get('amount_crypto') or deal.get('amount_usdt') or deal.get('amount_usdc') or '0'
        deal_amount = float(amount_str) if amount_str else 0.0
        currency = deal.get('currency', 'USDT')

        deal['received_amount'] = deal_amount
        deal['admin_confirmed'] = True
        deal['status'] = 'payment_received'
        save_deals()

        try:
            await query.message.delete()
        except Exception:
            pass

        detected_msg = build_payment_detected_message(
            deal_id, deal_amount, deal_amount, str(deal_amount), currency
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=detected_msg,
            parse_mode="HTML"
        )

        received_msg = build_usdt_received_message(deal, deal_id, deal_amount)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=received_msg,
            parse_mode="HTML",
            reply_markup=get_deal_buttons(deal_id)
        )

        payment_type = deal.get('payment_details_type', 'text')
        if payment_type == 'photo':
            photo_id = deal.get('payment_details')
            details_msg = build_payment_details_message(deal, deal_id)
            sent_details = await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=photo_id,
                caption=details_msg,
                parse_mode="HTML"
            )
        else:
            details_msg = build_payment_details_message(deal, deal_id)
            sent_details = await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=details_msg,
                parse_mode="HTML"
            )

        await update_current_stage_button(
            context.bot, deal, query.message.chat_id, sent_details.message_id
        )
        return

    if data.startswith("admincancel_"):
        parts = data.split("_")
        deal_id = parts[1]

        user_id = query.from_user.id
        if ADMIN_USER_IDS and user_id not in ADMIN_USER_IDS:
            await query.answer("Only admins can cancel!")
            return

        if deal_id not in deals:
            return

        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

        del deals[deal_id]
        save_deals()

        try:
            await query.edit_message_text(
                text="Deal cancelled by admin.",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    if data.startswith("depositcancel_"):
        parts = data.split("_")
        deal_id = parts[1]

        user_id = query.from_user.id
        if ADMIN_USER_IDS and user_id not in ADMIN_USER_IDS:
            await query.answer("Only admins can cancel!")
            return

        if deal_id not in deals:
            return

        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

        del deals[deal_id]
        save_deals()

        try:
            await query.edit_message_text(
                text="Deal cancelled by admin.",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    if data.startswith("release_") and not data.startswith("release_confirm_"):
        parts = data.split("_")
        deal_id = parts[1]

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean and user_id not in ADMIN_USER_IDS:
            await query.answer("Only the seller can release payment!")
            return

        seller = deal['seller']
        buyer = deal['buyer']
        currency = deal['currency']

        confirm_msg = (
            f"<b><u>Deal</u></b> #{deal_id}\n\n"
            f"{seller} Are you really Really REALLY Sure???\n"
            f"<b>Your {currency}</b> will be sent to {buyer} and if you have "
            f"not received your INR, then you yourself are responsible for "
            f"your LOSS!"
        )

        # Remove buttons from original message
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass

        keyboard = [
            [InlineKeyboardButton(
                "Yes, I am Responsible!",
                callback_data=f"release_confirm_{deal_id}"
            )],
            [InlineKeyboardButton(
                "Dispute",
                callback_data=f"dispute_{deal_id}"
            )]
        ]

        sent_confirm = await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=confirm_msg,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update_current_stage_button(
            context.bot, deal, query.message.chat_id, sent_confirm.message_id
        )
        return

    if data.startswith("release_confirm_"):
        parts = data.split("_")
        deal_id = parts[2]

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean and user_id not in ADMIN_USER_IDS:
            await query.answer("Only the seller can confirm release!")
            return

        # Remove buttons from confirmation message
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass

        seller = deal['seller']
        buyer = deal['buyer']
        currency = deal['currency']
        amount = deal.get('amount_crypto', '0')
        escrow_fee = calculate_escrow_fee(float(amount))
        withdrawal_amount = float(amount) - escrow_fee
        buyer_address = deal.get('buyer_address', 'N/A')

        # Update deal log - Deal Completed (before deleting deal)
        await update_deal_log(context.bot, deal_id, "Deal Completed")

        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

        # Store completion info in group_data before deleting deal
        import time as time_module
        full_channel_id = str(query.message.chat_id)
        if full_channel_id in group_data:
            group_data[full_channel_id]["deal_completed"] = True
            group_data[full_channel_id]["deal_release_time"] = time_module.time()
            save_group_data()

        del deals[deal_id]
        save_deals()

        finished_msg = (
            f"<b><u>Deal</u></b> (#{deal_id}) FINISHED\n\n"
            f"{buyer} [Buyer] | {seller} [Seller]\n"
            f"Withdrawl of {withdrawal_amount:.2f} {currency} Finished!\n"
            f"Tx Hash: {buyer_address}\n\n"
            f"<b><i>We are thankful to you for using our Escrow service and "
            f"we have a request. Please quote the invitation post by Bot in "
            f"OTC section of @CryptoIndiaUnited and write a vouch for us. "
            f"Below is a sample format which you may copy-paste and include "
            f"buyer/seller name...</i></b>\n\n"
            f"<code>Deal done successfully with @Username using escrow "
            f"@CryptoIndiaUnited.</code>\n\n"
            f"Please use /clean before leaving the group.\n\n"
            f"<i>Have a Nice Day!</i>"
        )

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=finished_msg,
            parse_mode="HTML"
        )
        return

    if data.startswith("cancel_"):
        parts = data.split("_")
        deal_id = parts[1]

        if deal_id not in deals:
            try:
                await query.edit_message_text(
                    text="Deal has been cancelled.",
                    parse_mode="HTML"
                )
            except Exception:
                pass
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean and user_id not in ADMIN_USER_IDS:
            await query.answer("Only the seller can cancel the deal!")
            return

        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

        del deals[deal_id]
        save_deals()

        try:
            await query.edit_message_text(
                text="Deal has been cancelled.",
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    # Handle setaddy callback (admin setting specific address for a deal)
    if data.startswith("setaddy_"):
        user_id = query.from_user.id
        if user_id not in ADMIN_USER_IDS:
            await query.answer("Only admins can use this!")
            return

        parts = data.split("_")
        if len(parts) < 3:
            return

        deal_id = parts[1]
        action = parts[2]

        if action == "cancel":
            await query.edit_message_text(
                "Address change cancelled.",
                parse_mode="HTML"
            )
            return

        if deal_id not in deals:
            await query.edit_message_text(
                f"Deal <code>{deal_id}</code> no longer exists.",
                parse_mode="HTML"
            )
            return

        deal = deals[deal_id]
        network = deal.get('network')
        currency = deal.get('currency', 'USDT')

        # Determine which address index to fix
        address_index = int(action) - 1  # 1 -> 0, 2 -> 1

        # Set the fixed address index (this will be used when network is selected)
        deal['fixed_address_index'] = address_index
        
        # If network is already selected, also update the deposit_address and qr_image immediately
        if network:
            new_address = None
            new_qr_image = None
            if currency == 'USDT':
                if network == 'BSC' and address_index < len(BSC_DEPOSIT_ADDRESSES):
                    new_address = BSC_DEPOSIT_ADDRESSES[address_index]
                    new_qr_image = BSC_QR_IMAGES[address_index]
                elif network == 'POLYGON' and address_index < len(POLYGON_DEPOSIT_ADDRESSES):
                    new_address = POLYGON_DEPOSIT_ADDRESSES[address_index]
                    new_qr_image = POLYGON_QR_IMAGES[address_index]
                elif network == 'SOL' and address_index < len(SOL_DEPOSIT_ADDRESSES):
                    new_address = SOL_DEPOSIT_ADDRESSES[address_index]
                    new_qr_image = SOL_QR_IMAGES[address_index]
            elif currency == 'USDC':
                if network == 'BSC' and address_index < len(USDC_BSC_DEPOSIT_ADDRESSES):
                    new_address = USDC_BSC_DEPOSIT_ADDRESSES[address_index]
                    new_qr_image = USDC_BSC_QR_IMAGES[address_index]
                elif network == 'POLYGON':
                    new_address = USDC_POLYGON_DEPOSIT_ADDRESS
                    new_qr_image = USDC_POLYGON_QR_IMAGE
                elif network == 'SOL':
                    new_address = USDC_SOL_DEPOSIT_ADDRESS
                    new_qr_image = USDC_SOL_QR_IMAGE

            if new_address:
                old_address = deal.get('deposit_address', 'Not set')
                deal['deposit_address'] = new_address
                if new_qr_image:
                    deal['qr_image'] = new_qr_image
                save_deals()
                
                await query.edit_message_text(
                    f"<b>Address Fixed for Deal #{deal_id}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"<b>Currency:</b> {currency}\n"
                    f"<b>Network:</b> {network}\n\n"
                    f"<b>Old Address:</b>\n<code>{old_address}</code>\n\n"
                    f"<b>New Address (Address {action}):</b>\n<code>{new_address}</code>",
                    parse_mode="HTML"
                )
                log_info(f"Deal #{deal_id} address changed to Address {action} by admin {user_id}")
            else:
                save_deals()
                await query.edit_message_text(
                    f"<b>Address Index Fixed for Deal #{deal_id}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"<b>Fixed to:</b> Address {action}\n"
                    f"<b>Currency:</b> {currency}\n"
                    f"<b>Network:</b> {network}\n\n"
                    f"<i>Note: Could not find Address {action} for this network.</i>",
                    parse_mode="HTML"
                )
        else:
            # Network not selected yet - just save the fixed index
            save_deals()
            await query.edit_message_text(
                f"<b>Address Pre-Fixed for Deal #{deal_id}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>Fixed to:</b> Address {action}\n"
                f"<b>Currency:</b> {currency}\n"
                f"<b>Network:</b> Not selected yet\n\n"
                f"<i>When the user selects a network, Address {action} will be used instead of rotating.</i>",
                parse_mode="HTML"
            )
            log_info(f"Deal #{deal_id} pre-fixed to Address {action} by admin {user_id}")
        return


async def handle_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle photo messages - for payment details QR codes."""
    global deals

    message = update.message
    if not message or not message.photo:
        return

    chat_id = message.chat_id
    user = message.from_user
    username = user.username.lower() if user.username else None

    if not message.reply_to_message:
        return

    reply_to_msg_id = message.reply_to_message.message_id
    bot_info = await context.bot.get_me()

    if message.reply_to_message.from_user.id != bot_info.id:
        return

    for deal_id, deal in deals.items():
        if (deal.get('payment_details_msg_id') == reply_to_msg_id and
                deal.get('chat_id') == chat_id):
            seller_clean = deal['seller'].lstrip('@').lower()

            if username != seller_clean and user.id not in ADMIN_USER_IDS:
                continue

            photo_file_id = message.photo[-1].file_id
            deal['payment_details'] = photo_file_id
            deal['payment_details_type'] = 'photo'
            deal['status'] = 'pending_confirmation'
            deal['seller_confirmed'] = False
            deal['buyer_confirmed'] = False
            save_deals()

            buyer = deal['buyer']
            await message.reply_text(
                "Payment Details Successfully Saved!\n\n"
                f"⚠️ {buyer} Do <b>NOT</b> send INR to the details "
                f"given by the seller yet. Please wait for the Escrow Bot "
                f"to prompt you before making any payment.",
                parse_mode="HTML"
            )

            summary_text = build_deal_summary(deal, deal_id)
            sent = await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo_file_id,
                caption=summary_text,
                parse_mode="HTML",
                reply_markup=get_confirm_buttons(deal_id)
            )
            deal['summary_msg_id'] = sent.message_id
            save_deals()
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

        reply_from_user = message.reply_to_message.from_user
        if reply_from_user is None or reply_from_user.id != bot_info.id:
            return

        for deal_id, deal in deals.items():
            if (deal.get('buyer_address_msg_id') == reply_to_msg_id and
                    deal.get('chat_id') == chat_id):
                buyer_clean = deal['buyer'].lstrip('@').lower()

                if username != buyer_clean and user.id not in ADMIN_USER_IDS:
                    continue

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
                currency = deal.get('currency', 'USDT')

                seller_msg = (
                    f"<b><u>Deal</u></b> #{deal_id}\n\n"
                    f"{seller} [Seller] please <b>QUOTE</b> this message "
                    f"and reply with your <b>{currency} {network_name}</b> address "
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

            if (deal.get('seller_address_msg_id') == reply_to_msg_id and
                    deal.get('chat_id') == chat_id):
                seller_clean = deal['seller'].lstrip('@').lower()

                if username != seller_clean and user.id not in ADMIN_USER_IDS:
                    continue

                deal['seller_address'] = text
                deal['status'] = 'pending_payment_details'
                save_deals()

                await message.reply_text(
                    "Refund Address Successfully Saved!",
                    parse_mode="HTML"
                )

                seller = deal['seller']
                payment_msg = (
                    f"<b><u>Deal</u></b> #{deal_id}\n\n"
                    f"{seller} [Seller], please <b>QUOTE</b> this message "
                    f"and reply with your <b>Payment Details</b>.\n\n"
                    f"Please make sure that all details are correct to avoid "
                    f"any payment issues."
                )

                sent_msg = await context.bot.send_message(
                    chat_id=chat_id,
                    text=payment_msg,
                    parse_mode="HTML"
                )

                deal['payment_details_msg_id'] = sent_msg.message_id
                save_deals()
                return

            if (deal.get('payment_details_msg_id') == reply_to_msg_id and
                    deal.get('chat_id') == chat_id):
                seller_clean = deal['seller'].lstrip('@').lower()

                if username != seller_clean and user.id not in ADMIN_USER_IDS:
                    continue

                deal['payment_details'] = text
                deal['payment_details_type'] = 'text'
                deal['status'] = 'pending_confirmation'
                deal['seller_confirmed'] = False
                deal['buyer_confirmed'] = False
                save_deals()

                buyer = deal['buyer']
                await message.reply_text(
                    "Payment Details Successfully Saved!\n\n"
                    f"⚠️ {buyer} Do <b>NOT</b> send INR to the details "
                    f"given by the seller yet. Please wait for the Escrow Bot "
                    f"to prompt you before making any payment.",
                    parse_mode="HTML"
                )

                summary_text = build_deal_summary(deal, deal_id)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=summary_text,
                    parse_mode="HTML",
                    reply_markup=get_confirm_buttons(deal_id)
                )
                return

        return

    if 'seller' in text.lower() and 'buyer' in text.lower():
        form_data = parse_deal_form(text)

        # Ignore completely if deal info format is not matched properly
        if form_data is None:
            return

        # Handle "me/Me/ME" in seller/buyer fields - replace with submitter's username
        submitter_username = f"@{user.username}" if user.username else None
        if submitter_username:
            if form_data.get('seller', '').lower() == 'me':
                form_data['seller'] = submitter_username
            if form_data.get('buyer', '').lower() == 'me':
                form_data['buyer'] = submitter_username

        # Send corrected form back with "Form filled by @username"
        currency = 'USDT'
        if form_data.get('amount_usdc'):
            currency = 'USDC'
        amount_crypto = form_data.get('amount_usdt') or form_data.get('amount_usdc', '')
        corrected_form = (
            f"<b>{currency} Seller:</b> {form_data['seller']}\n"
            f"<b>{currency} Buyer:</b> {form_data['buyer']}\n"
            f"<b>Amount[{currency}]:</b> {amount_crypto}\n"
            f"<b>Amount[INR]:</b> {form_data.get('amount_inr', '')}\n"
            f"<b>Payment Method:</b> {form_data.get('payment_method', '')}\n"
            f"<b>Time[Minute]:</b> {form_data.get('time', '')}\n"
            f"\n"
            f"Form filled by {submitter_username if submitter_username else 'unknown'}."
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=corrected_form,
            parse_mode="HTML"
        )

        deal_id = generate_deal_id()

        while deal_id in deals:
            deal_id = generate_deal_id()

        # Get room number from chat_id
        room_num = get_room_by_channel_id(str(chat_id).replace("-100", ""))
        if room_num is None:
            room_num = "N/A"

        import time as time_module
        
        # Get escrow sender username and mentioned_user from group_data
        full_channel_id = str(chat_id)
        escrow_sender = None
        escrow_mentioned_user = None
        if full_channel_id in group_data:
            escrow_sender = group_data[full_channel_id].get('sender_user')
            escrow_mentioned_user = group_data[full_channel_id].get('mentioned_user')
        
        # Determine fixed address index based on room number
        # Odd rooms (1,3,5,7,9,11,13,15,17,19) use Address 1 (index 0)
        # Even rooms (2,4,6,8,10,12,14,16,18,20) use Address 2 (index 1)
        fixed_address_index = None
        if room_num != "N/A":
            try:
                room_num_int = int(room_num)
                if room_num_int % 2 == 1:  # Odd room
                    fixed_address_index = 0  # Address 1
                else:  # Even room
                    fixed_address_index = 1  # Address 2
            except (ValueError, TypeError):
                pass
        
        # Get channel_id for deal log updates
        channel_id = str(chat_id).replace("-100", "") if str(chat_id).startswith("-100") else str(chat_id)
        
        deals[deal_id] = {
            'chat_id': chat_id,
            'channel_id': channel_id,
            'seller': form_data['seller'],
            'buyer': form_data['buyer'],
            'buyer_username': form_data['buyer'],
            'seller_username': form_data['seller'],
            'amount_crypto': amount_crypto,
            'amount_usdt': form_data.get('amount_usdt'),
            'amount_usdc': form_data.get('amount_usdc'),
            'amount_inr': form_data.get('amount_inr', ''),
            'payment_method': form_data.get('payment_method', ''),
            'time': form_data.get('time', ''),
            'currency': currency,
            'network': None,
            'buyer_address': None,
            'seller_address': None,
            'status': 'pending_network',
            'buyer_address_msg_id': None,
            'seller_address_msg_id': None,
            'room_number': room_num,
            'mentioned_user': escrow_mentioned_user,
            'sender_user': escrow_sender,
            'form_submitted_at': time_module.time(),
            'fixed_address_index': fixed_address_index
        }
        save_deals()

        # Store form submission time in group_data for duration calculation
        if full_channel_id in group_data:
            group_data[full_channel_id]["deal_start_time"] = time_module.time()
            save_group_data()

        seller = form_data['seller']
        buyer = form_data['buyer']

        # Transfer log_message_id from group_data to deal and update the log
        if full_channel_id in group_data and group_data[full_channel_id].get('log_message_id'):
            deals[deal_id]['log_message_id'] = group_data[full_channel_id]['log_message_id']
            save_deals()
            # Update the existing log message with deal info
            await update_deal_log(context.bot, deal_id, "Deal Started")

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
            reply_markup=get_network_buttons(deal_id, currency)
        )


async def send_2fa_welcome_message(context, chat_id, username, user_id):
    """Send 2FA verification welcome message to a user."""
    log_info(f"Sending 2FA welcome message to @{username} (ID: {user_id}) in chat {chat_id}")
    msg = (
        f"Hii @{username}, Welcome to the @CryptoIndiaUnited Escrow Group!\n\n"
        f"Please <b>check & verify your 2FA</b> code by clicking the button below "
        f"before proceeding with the deal.\n\n"
        f"You will be able to send messages once your 2FA is verified."
    )
    keyboard = [
        [InlineKeyboardButton("Check 2FA", callback_data=f"check2fa_{chat_id}_{user_id}")],
        [InlineKeyboardButton("I've checked & verified my 2FA", callback_data=f"verify2fa_{chat_id}_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=msg,
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        log_info(f"2FA welcome message sent successfully to @{username}")
    except Exception as e:
        log_error(f"Failed to send 2FA welcome message to @{username}: {e}")


async def send_form_messages(context, chat_id, mentioned_user, sender_user):
    """Send the deal form messages after both users have verified 2FA."""
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
    user_id = user.id
    username = user.username.lower() if user.username else None

    if chat_id in allowed_users:
        allowed = allowed_users[chat_id]
        if username and username in allowed:
            await join_request.approve()
            log_info(f"Join approved: @{username}")

            # Restrict user's message permission after they join
            await asyncio.sleep(1)
            try:
                channel_id = int(chat_id)
                if channel_id < 0:
                    channel_id = int(str(channel_id).replace("-100", ""))
                
                restrict_rights = ChatBannedRights(
                    until_date=None,
                    view_messages=False,
                    send_messages=True,
                    send_media=True,
                    send_stickers=True,
                    send_gifs=True,
                    send_games=True,
                    send_inline=True,
                    embed_links=True
                )
                await userbot_client(EditBannedRequest(
                    channel=channel_id,
                    participant=user_id,
                    banned_rights=restrict_rights
                ))
                log_info(f"User {user_id} (@{username}) restricted from sending messages until 2FA verification")
            except Exception as e:
                log_error(f"Failed to restrict user {user_id}: {e}")

            if chat_id in group_data:
                if username not in group_data[chat_id]["joined_users"]:
                    group_data[chat_id]["joined_users"].append(username)
                    
                    # Store user ID based on whether they are the mentioned user or sender
                    mentioned = group_data[chat_id]["mentioned_user"]
                    sender = group_data[chat_id]["sender_user"]
                    mentioned_clean = mentioned.lstrip("@").lower()
                    sender_clean = sender.lstrip("@").lower()
                    
                    if username == mentioned_clean:
                        group_data[chat_id]["mentioned_user_id"] = user_id
                    elif username == sender_clean:
                        group_data[chat_id]["sender_user_id"] = user_id
                    
                    save_group_data()

                    joined_count = len(group_data[chat_id]["joined_users"])

                    # Send 2FA welcome message for each user who joins
                    await asyncio.sleep(2)
                    await send_2fa_welcome_message(context, chat_id, username, user_id)

                    # Update deal log with join status
                    room_num = group_data[chat_id].get("room_number", "N/A")
                    channel_id = chat_id.replace("-100", "") if chat_id.startswith("-100") else chat_id
                    joined_users = group_data[chat_id]["joined_users"]
                    initiator_joined = sender_clean in [u.lower() for u in joined_users]
                    counterparty_joined = mentioned_clean in [u.lower() for u in joined_users]
                    await update_initial_deal_log(context.bot, channel_id, sender, mentioned, room_num, initiator_joined, counterparty_joined)

                    # Send form messages when second user joins
                    if joined_count == 2:
                        await asyncio.sleep(1)
                        await send_form_messages(context, chat_id, mentioned, sender)
        else:
            await join_request.decline()
    else:
        await join_request.decline()


async def handle_chat_member_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle users who are directly added to the group (not via join request)."""
    global group_data
    
    chat_member = update.chat_member
    if not chat_member:
        return
    
    chat_id = str(chat_member.chat.id)
    new_member = chat_member.new_chat_member
    old_member = chat_member.old_chat_member
    
    if not new_member or not new_member.user:
        return
    
    user = new_member.user
    user_id = user.id
    username = user.username.lower() if user.username else None
    
    if not username:
        return
    
    old_status = old_member.status if old_member else None
    new_status = new_member.status
    
    is_new_member = (
        old_status in [None, "left", "kicked"] and 
        new_status in ["member", "administrator", "restricted"]
    )
    
    if not is_new_member:
        return
    
    if chat_id not in allowed_users:
        return
    
    allowed = allowed_users[chat_id]
    if username not in allowed:
        return
    
    if chat_id not in group_data:
        return
    
    if username in group_data[chat_id].get("joined_users", []):
        return
    
    log_info(f"User @{username} directly added to group {chat_id}")
    
    await asyncio.sleep(1)
    try:
        channel_id = int(chat_id)
        if channel_id < 0:
            channel_id = int(str(channel_id).replace("-100", ""))
        
        restrict_rights = ChatBannedRights(
            until_date=None,
            view_messages=False,
            send_messages=True,
            send_media=True,
            send_stickers=True,
            send_gifs=True,
            send_games=True,
            send_inline=True,
            embed_links=True
        )
        await userbot_client(EditBannedRequest(
            channel=channel_id,
            participant=user_id,
            banned_rights=restrict_rights
        ))
        log_info(f"User {user_id} (@{username}) restricted from sending messages until 2FA verification")
    except Exception as e:
        log_error(f"Failed to restrict user {user_id}: {e}")
    
    if "joined_users" not in group_data[chat_id]:
        group_data[chat_id]["joined_users"] = []
    
    group_data[chat_id]["joined_users"].append(username)
    
    mentioned = group_data[chat_id].get("mentioned_user", "")
    sender = group_data[chat_id].get("sender_user", "")
    mentioned_clean = mentioned.lstrip("@").lower() if mentioned else ""
    sender_clean = sender.lstrip("@").lower() if sender else ""
    
    if username == mentioned_clean:
        group_data[chat_id]["mentioned_user_id"] = user_id
    elif username == sender_clean:
        group_data[chat_id]["sender_user_id"] = user_id
    
    save_group_data()
    
    joined_count = len(group_data[chat_id]["joined_users"])
    
    await asyncio.sleep(2)
    await send_2fa_welcome_message(context, chat_id, username, user_id)
    
    room_num = group_data[chat_id].get("room_number", "N/A")
    channel_id_str = chat_id.replace("-100", "") if chat_id.startswith("-100") else chat_id
    joined_users = group_data[chat_id]["joined_users"]
    initiator_joined = sender_clean in [u.lower() for u in joined_users]
    counterparty_joined = mentioned_clean in [u.lower() for u in joined_users]
    await update_initial_deal_log(context.bot, channel_id_str, sender, mentioned, room_num, initiator_joined, counterparty_joined)
    
    if joined_count == 2:
        await asyncio.sleep(1)
        await send_form_messages(context, chat_id, mentioned, sender)


async def escrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global userbot_client
    # Only work in groups, not DMs
    if update.effective_chat.type == "private":
        return

    sender = update.effective_user.username
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if sender has a username
    if not sender:
        await context.bot.send_message(
            chat_id=chat_id,
            text="You need a username to deal!",
            reply_to_message_id=update.message.message_id
        )
        return

    # Check if user is banned
    if is_user_banned(user_id, sender):
        await context.bot.send_message(
            chat_id=chat_id,
            text="You are banned from using this bot."
        )
        return

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

    # Check if sender has an active escrow deal
    active_user, active_link = get_user_active_deal(sender_username)
    if active_user:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f'{active_user} already has an <a href="{active_link}">active escrow deal</a>! Please ask them to complete it before starting a new one.',
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_to_message_id=update.message.message_id
        )
        return

    # Check if mentioned user has an active escrow deal
    active_user, active_link = get_user_active_deal(mentioned_user)
    if active_user:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f'{active_user} already has an <a href="{active_link}">active escrow deal</a>! Please ask them to complete it before starting a new one.',
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_to_message_id=update.message.message_id
        )
        return

    # Get mentioned user's ID using userbot
    if userbot_client is None:
        await init_userbot()
    
    mentioned_user_id = None
    mentioned_has_username = True
    try:
        mentioned_clean = mentioned_user.lstrip("@")
        mentioned_entity = await userbot_client.get_entity(mentioned_clean)
        mentioned_user_id = mentioned_entity.id
        # Check if mentioned user has a username
        if not getattr(mentioned_entity, 'username', None):
            mentioned_has_username = False
    except Exception as e:
        log_warning(f"Could not get mentioned user ID: {e}")
        # If we can't get the entity, assume they don't have a valid username
        mentioned_has_username = False

    # Check if mentioned user has a username
    if not mentioned_has_username:
        await context.bot.send_message(
            chat_id=chat_id,
            text="You need a username to deal!",
            reply_to_message_id=update.message.message_id
        )
        return

    # Find a free room where both users are not banned
    room_num, room_data = await get_free_room_for_users(user_id, mentioned_user_id)

    if room_num is None:
        # Check if there are any free rooms at all
        has_free_room = False
        for r_num, r_data in rooms.items():
            if r_data.get('status') == 'free':
                has_free_room = True
                break
        
        if has_free_room:
            # Free rooms exist but users are banned in all of them
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ No available escrow rooms for these users. Please try again later."
            )
            return
        
        # No free rooms - check if we can create a new one
        missing_room = None
        for i in range(1, 21):
            if str(i) not in rooms:
                missing_room = i
                break

        if missing_room is None:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ All escrow rooms are currently busy. Please try again later."
            )
            return

        bot_info = await context.bot.get_me()
        bot_username = bot_info.username

        invite_link, room_num, channel_id = await create_escrow_group(
            missing_room,
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

        rooms[str(missing_room)] = {
            "room_number": missing_room,
            "channel_id": channel_id,
            "invite_link": invite_link,
            "status": "busy",
            "current_deal_id": None,
            "sender_user": sender_username,
            "mentioned_user": mentioned_user
        }
        save_rooms()
        room_num = str(missing_room)
    else:
        invite_link = room_data.get('invite_link')
        channel_id = room_data.get('channel_id')

    sender_clean = sender_username.lstrip("@").lower()
    mentioned_clean = mentioned_user.lstrip("@").lower()

    full_channel_id = f"-100{channel_id}"
    allowed_users[full_channel_id] = [sender_clean, mentioned_clean]
    save_allowed_users()

    group_data[full_channel_id] = {
        "allowed_users": [sender_clean, mentioned_clean],
        "joined_users": [],
        "mentioned_user": mentioned_user,
        "sender_user": sender_username,
        "room_number": room_num,
        "sender_user_id": user_id,
        "mentioned_user_id": mentioned_user_id
    }
    save_group_data()

    mark_room_busy(room_num, None, sender_username, mentioned_user)

    message = (
        f"{mentioned_user} & {sender_username} are requested to join "
        f"<b>Crypto India Escrow Room {room_num}</b>. "
        f"Please use the following link to join the room...\n\n"
        f"{invite_link}\n\n"
        f"🚫 <b>Beware of Scammers</b> 🚫\n\n"
        f"Read <a href=\"https://t.me/c/3446573761/3299/3424\">Important Safety Tips</a>."
    )

    sent_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_to_message_id=update.message.message_id
    )

    # Store the escrow message info for editing on /clean
    group_data[full_channel_id]["escrow_message_id"] = sent_msg.message_id
    group_data[full_channel_id]["escrow_chat_id"] = chat_id
    save_group_data()

    # Send initial deal log to log channel
    await send_initial_deal_log(context.bot, room_num, sender_username, mentioned_user, channel_id, False, False)


async def setup_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to create all 20 escrow rooms. Also checks for deleted groups and recreates them."""
    global userbot_client
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id not in ADMIN_USER_IDS:
        return

    if userbot_client is None:
        await init_userbot()

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "<b>🔧 SETUP ROOMS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔄 Checking existing rooms and creating missing ones...\n\n"
            "<i>This may take a few minutes.</i>"
        ),
        parse_mode="HTML"
    )

    bot_info = await context.bot.get_me()
    bot_username = bot_info.username

    created_count = 0
    recreated_count = 0
    for room_number in range(1, 21):
        room_key = str(room_number)
        
        # Check if room exists in our records
        if room_key in rooms:
            # Verify the group still exists by trying to access it
            room_data = rooms[room_key]
            channel_id = room_data.get('channel_id')
            if channel_id:
                try:
                    full_channel_id = int(f"-100{channel_id}")
                    await userbot_client.get_entity(full_channel_id)
                    # Group exists, skip
                    continue
                except Exception as e:
                    # Group doesn't exist or can't be accessed, need to recreate
                    log_warning(f"Room {room_number} group not accessible, recreating: {e}")
                    del rooms[room_key]
                    save_rooms()
                    recreated_count += 1

        try:
            invite_link, room_num, channel_id = await create_escrow_group(
                room_number,
                "@setup",
                "@setup",
                bot_username
            )

            if invite_link and channel_id:
                rooms[str(room_number)] = {
                    "room_number": room_number,
                    "channel_id": channel_id,
                    "invite_link": invite_link,
                    "status": "free",
                    "current_deal_id": None,
                    "sender_user": None,
                    "mentioned_user": None
                }
                save_rooms()
                created_count += 1
                log_info(f"Room {room_number} created")

            await asyncio.sleep(2)

        except Exception as e:
            log_error(f"Room {room_number}: Setup failed - {e}")
            continue

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"<b>🔧 SETUP ROOMS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>✅ Setup Complete</b>\n\n"
            f"<b>📊 Results:</b>\n"
            f"├ 🆕 New Rooms Created: <b>{created_count}</b>\n"
            f"├ 🔄 Rooms Recreated: <b>{recreated_count}</b>\n"
            f"└ 📋 Total Rooms: <b>{len(rooms)}</b>"
        ),
        parse_mode="HTML"
    )


async def exampleform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send example form for escrow deal."""
    example_text = (
        "USDT Seller: @DemoSeller\n"
        "USDT Buyer: @DemoBuyer\n"
        "Amount[USDT]: 100\n"
        "Amount[INR]: 9100\n"
        "Payment Method: CDM\n"
        "Time[Minute]: 30"
    )
    await update.message.reply_text(example_text)


async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove all members from the group and mark deal as completed."""
    global userbot_client, deals, rooms, group_data

    chat_id = update.effective_chat.id
    full_channel_id = str(chat_id)

    if userbot_client is None:
        await init_userbot()

    room_num = get_room_by_channel_id(chat_id)

    # Check if deal was completed (payment released or manually completed via .complete)
    deal_completed = False
    manually_completed = False
    if full_channel_id in group_data:
        deal_completed = group_data[full_channel_id].get("deal_completed", False)
        manually_completed = group_data[full_channel_id].get("manually_completed", False)

    # Check if deposit was detected (deal exists with deposit status)
    deposit_detected = False
    channel_id_str = str(chat_id).replace("-100", "") if str(chat_id).startswith("-100") else str(chat_id)
    for deal_id, deal in deals.items():
        if deal.get('channel_id') == channel_id_str or deal.get('chat_id') == chat_id:
            if deal.get('status') in ['deposit_pending', 'deposit_confirmed', 'completed']:
                deposit_detected = True
                break

    # Edit original escrow message based on deal status
    if full_channel_id in group_data:
        gdata = group_data[full_channel_id]
        escrow_msg_id = gdata.get("escrow_message_id")
        escrow_chat_id = gdata.get("escrow_chat_id")
        mentioned_user = gdata.get("mentioned_user", "")
        sender_user = gdata.get("sender_user", "")
        sender_user_id = gdata.get("sender_user_id", "")
        mentioned_user_id = gdata.get("mentioned_user_id", "")
        room_number = gdata.get("room_number", room_num or "")

        # Format user info - only show ID if available (in monospace)
        mentioned_info = f"{mentioned_user} (<code>{mentioned_user_id}</code>)" if mentioned_user_id else mentioned_user
        sender_info = f"{sender_user} (<code>{sender_user_id}</code>)" if sender_user_id else sender_user
        
        if escrow_msg_id and escrow_chat_id:
            # Skip editing if manually completed via .complete (message already edited)
            if manually_completed:
                pass  # Don't edit, .complete already set the message
            elif deal_completed:
                # Calculate duration from form submission to release
                import time as time_module
                start_time = gdata.get("deal_start_time", 0)
                release_time = gdata.get("deal_release_time", time_module.time())
                duration_seconds = int(release_time - start_time)
                
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                seconds = duration_seconds % 60
                
                if hours > 0:
                    duration_str = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    duration_str = f"{minutes}m {seconds}s"
                else:
                    duration_str = f"{seconds}s"
                
                complete_msg = (
                    f"🟢 <b>Status</b>: Deal <b>Completed</b> between\n"
                    f"{mentioned_info} &\n"
                    f"{sender_info}\n"
                    f"<b>@CryptoIndiaUnited Escrow Room {room_number}</b>\n"
                    f"🕗 Completed in {duration_str}"
                )
                try:
                    await context.bot.edit_message_text(
                        chat_id=escrow_chat_id,
                        message_id=escrow_msg_id,
                        text=complete_msg,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    log_warning(f"Could not edit escrow message: {e}")
            elif not deposit_detected:
                # Deal cancelled - no deposit detected
                cancel_msg = (
                    f"🔴 <b>Status</b>: Deal <b>Cancelled</b> between\n"
                    f"{mentioned_info} &\n"
                    f"{sender_info}\n"
                    f"<b>@CryptoIndiaUnited Escrow Room {room_number}</b>"
                )
                try:
                    await context.bot.edit_message_text(
                        chat_id=escrow_chat_id,
                        message_id=escrow_msg_id,
                        text=cancel_msg,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    log_warning(f"Could not edit escrow message: {e}")
                
                # Also edit the deal log message to show cancelled
                log_message_id = None
                # First try to get log_message_id from group_data (always has current deal's log)
                if full_channel_id in group_data:
                    log_message_id = group_data[full_channel_id].get('log_message_id')
                # If not found in group_data, try the most recent deal
                if not log_message_id:
                    for deal_id, deal in deals.items():
                        if deal.get('channel_id') == channel_id_str or deal.get('chat_id') == chat_id:
                            if deal.get('log_message_id'):
                                log_message_id = deal.get('log_message_id')
                
                if log_message_id:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=DEAL_LOG_CHANNEL_ID,
                            message_id=log_message_id,
                            text="<b>Deal Cancelled !!</b>",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        log_warning(f"Could not edit deal log message: {e}")

    for deal_id, deal in list(deals.items()):
        if deal.get('channel_id') == channel_id_str or deal.get('chat_id') == chat_id:
            del deals[deal_id]
            log_info(f"Deal #{deal_id} marked as completed (cleaned)")
    save_deals()

    if room_num:
        mark_room_free(room_num)
        log_info(f"Room {room_num} marked as free")

    # Clear group_data entry so users can start new deals
    if full_channel_id in group_data:
        del group_data[full_channel_id]
        save_group_data()
        log_info(f"Group data cleared for channel {full_channel_id}")

    kicked_count = 0
    try:
        bot_info = await context.bot.get_me()
        bot_id = bot_info.id

        userbot_me = await userbot_client.get_me()
        userbot_id = userbot_me.id

        protected_ids = set([bot_id, userbot_id, 6662820986])

        try:
            from telethon.tl.functions.channels import GetParticipantsRequest
            from telethon.tl.types import ChannelParticipantsRecent
            participants = await userbot_client(GetParticipantsRequest(
                channel=chat_id,
                filter=ChannelParticipantsRecent(),
                offset=0,
                limit=100,
                hash=0
            ))

            from datetime import timedelta
            for user in participants.users:
                if user.id not in protected_ids:
                    try:
                        # Kick user with a temporary ban that expires in 35 seconds
                        # This kicks them but doesn't permanently ban them
                        kick_rights = ChatBannedRights(
                            until_date=datetime.now() + timedelta(seconds=35),
                            view_messages=True
                        )
                        await userbot_client(EditBannedRequest(
                            channel=chat_id,
                            participant=user.id,
                            banned_rights=kick_rights
                        ))
                        kicked_count += 1
                    except Exception as kick_error:
                        log_warning(f"Could not kick user {user.id}: {kick_error}")
        except Exception as get_error:
            log_warning(f"Could not get participants: {get_error}")

    except Exception as e:
        log_error(f"Error in clean command: {e}")

    await update.message.reply_text("Cleaned!")


async def complete_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to manually mark a deal as completed. Triggered by .complete command."""
    global group_data
    
    user_id = update.effective_user.id
    
    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return
    
    chat_id = update.effective_chat.id
    full_channel_id = str(chat_id)
    
    room_num = get_room_by_channel_id(chat_id)
    
    if full_channel_id not in group_data:
        await update.message.reply_text("No active deal found in this group.")
        return
    
    gdata = group_data[full_channel_id]
    escrow_msg_id = gdata.get("escrow_message_id")
    escrow_chat_id = gdata.get("escrow_chat_id")
    mentioned_user = gdata.get("mentioned_user", "")
    sender_user = gdata.get("sender_user", "")
    sender_user_id = gdata.get("sender_user_id", "")
    mentioned_user_id = gdata.get("mentioned_user_id", "")
    room_number = gdata.get("room_number", room_num or "")
    
    if not escrow_msg_id or not escrow_chat_id:
        await update.message.reply_text("Could not find the original escrow message.")
        return
    
    # Calculate duration from deal start (form submission) to now
    import time as time_module
    start_time = gdata.get("deal_start_time", 0)
    current_time = time_module.time()
    
    if start_time == 0:
        duration_str = "N/A"
    else:
        duration_seconds = int(current_time - start_time)
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        
        if hours > 0:
            duration_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = f"{seconds}s"
    
    # Format user info - only show ID if available (in monospace)
    mentioned_info = f"{mentioned_user} (<code>{mentioned_user_id}</code>)" if mentioned_user_id else mentioned_user
    sender_info = f"{sender_user} (<code>{sender_user_id}</code>)" if sender_user_id else sender_user
    
    complete_msg = (
        f"🟢 <b>Status</b>: Deal <b>Completed</b> between\n"
        f"{mentioned_info} &\n"
        f"{sender_info}\n"
        f"<b>@CryptoIndiaUnited Escrow Room {room_number}</b>\n"
        f"🕗 Completed in {duration_str}"
    )
    
    # Mark as manually completed so /clean doesn't overwrite with cancelled
    group_data[full_channel_id]["manually_completed"] = True
    save_group_data()
    
    try:
        await context.bot.edit_message_text(
            chat_id=escrow_chat_id,
            message_id=escrow_msg_id,
            text=complete_msg,
            parse_mode="HTML"
        )
        await update.message.reply_text("Deal marked as completed!")
    except Exception as e:
        log_warning(f"Could not edit escrow message: {e}")
        await update.message.reply_text(f"Error: Could not edit escrow message.")


async def rooms_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display professional status of all rooms."""
    user_id = update.effective_user.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    if not rooms:
        await update.message.reply_text(
            "<b>🏠 ROOM STATUS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "❌ No rooms configured yet.\n\n"
            "Use /setup_rooms to create rooms.",
            parse_mode="HTML"
        )
        return

    total_rooms = len(rooms)
    free_rooms = sum(1 for r in rooms.values() if r.get('status') == 'free')
    busy_rooms = total_rooms - free_rooms

    header = (
        "<b>🏠 ESCROW ROOMS STATUS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>📊 Overview:</b>\n"
        f"├ Total Rooms: <b>{total_rooms}</b>\n"
        f"├ 🟢 Available: <b>{free_rooms}</b>\n"
        f"└ 🔴 In Use: <b>{busy_rooms}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>📋 ROOM DETAILS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    room_details = ""
    for room_num in sorted(rooms.keys(), key=lambda x: int(x)):
        room_data = rooms[room_num]
        status = room_data.get('status', 'unknown')
        status_icon = "🟢" if status == 'free' else "🔴"
        status_text = "Available" if status == 'free' else "In Use"

        room_details += f"{status_icon} <b>Room {room_num}</b> - {status_text}\n"

        if status == 'busy':
            sender = room_data.get('sender_user', 'N/A')
            mentioned = room_data.get('mentioned_user', 'N/A')
            deal_id = room_data.get('current_deal_id', 'N/A')
            room_details += f"    ├ 👤 Seller: {sender}\n"
            room_details += f"    ├ 👤 Buyer: {mentioned}\n"
            if deal_id:
                room_details += f"    └ 📝 Deal: #{deal_id}\n"
            else:
                room_details += f"    └ 📝 Deal: Pending\n"
        room_details += "\n"

    footer = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    )

    await update.message.reply_text(
        header + room_details + footer,
        parse_mode="HTML"
    )


async def empty_all_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Free all rooms and kick all members from them."""
    global userbot_client, deals, rooms, group_data

    user_id = update.effective_user.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    if userbot_client is None:
        await init_userbot()

    progress_msg = await update.message.reply_text("emptying all rooms.....")

    total_kicked = 0
    rooms_cleaned = 0

    bot_info = await context.bot.get_me()
    bot_id = bot_info.id
    userbot_me = await userbot_client.get_me()
    userbot_id = userbot_me.id
    protected_ids = set([bot_id, userbot_id, 6662820986])

    for room_num, room_data in rooms.items():
        channel_id = room_data.get('channel_id')
        if not channel_id:
            continue

        full_channel_id = f"-100{channel_id}"

        # Clear deals for this room
        for deal_id, deal in list(deals.items()):
            if str(deal.get('chat_id')) == full_channel_id:
                del deals[deal_id]
                log_info(f"Deal #{deal_id} removed (empty command)")

        # Clear group_data entry so users can start new deals
        if full_channel_id in group_data:
            del group_data[full_channel_id]
            log_info(f"Group data cleared for room {room_num} (empty command)")

        # Kick all members
        try:
            from telethon.tl.functions.channels import GetParticipantsRequest
            from telethon.tl.types import ChannelParticipantsRecent
            participants = await userbot_client(GetParticipantsRequest(
                channel=int(full_channel_id),
                filter=ChannelParticipantsRecent(),
                offset=0,
                limit=100,
                hash=0
            ))

            for user in participants.users:
                if user.id not in protected_ids:
                    try:
                        ban_rights = ChatBannedRights(
                            until_date=None,
                            view_messages=True
                        )
                        await userbot_client(EditBannedRequest(
                            channel=int(full_channel_id),
                            participant=user.id,
                            banned_rights=ban_rights
                        ))
                        unban_rights = ChatBannedRights(
                            until_date=None,
                            view_messages=False,
                            send_messages=False,
                            send_media=False,
                            send_stickers=False,
                            send_gifs=False,
                            send_games=False,
                            send_inline=False,
                            embed_links=False
                        )
                        await userbot_client(EditBannedRequest(
                            channel=int(full_channel_id),
                            participant=user.id,
                            banned_rights=unban_rights
                        ))
                        total_kicked += 1
                    except Exception:
                        pass
        except Exception as e:
            log_warning(f"Could not process room {room_num}: {e}")

        # Mark room as free
        mark_room_free(room_num)
        rooms_cleaned += 1

    save_deals()
    save_group_data()

    await progress_msg.edit_text("All rooms have been emptied and are ready to use!")


async def delete_all_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete all rooms from the database so they won't be used for escrow."""
    global rooms

    user_id = update.effective_user.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    room_count = len(rooms)
    rooms = {}
    save_rooms()

    await update.message.reply_text(
        f"<b>🗑️ DELETE ALL ROOMS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>✅ Operation Complete</b>\n\n"
        f"<b>📊 Results:</b>\n"
        f"└ 🏠 Rooms Deleted: <b>{room_count}</b>\n\n"
        f"<i>Old rooms will no longer be used for escrow.</i>\n\n"
        f"💡 Use /newrooms to create 20 new escrow rooms.",
        parse_mode="HTML"
    )
    log_info(f"All {room_count} rooms deleted by admin {user_id}")


async def create_new_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create 20 new escrow rooms. Clears existing rooms and creates fresh ones."""
    global userbot_client, rooms

    user_id = update.effective_user.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    if userbot_client is None:
        await init_userbot()

    await update.message.reply_text(
        "<b>🏗️ CREATE NEW ROOMS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔄 Clearing existing rooms and creating 20 new escrow rooms...\n\n"
        "<i>This may take a few minutes.</i>",
        parse_mode="HTML"
    )

    # Clear existing rooms data to stop using old groups
    rooms.clear()
    save_rooms()
    log_info("Cleared all existing room data")

    bot_info = await context.bot.get_me()
    bot_username = bot_info.username

    created_count = 0
    failed_count = 0

    for room_number in range(1, 21):
        try:
            invite_link, room_num, channel_id = await create_escrow_group(
                room_number,
                "@system",
                "@system",
                bot_username
            )

            if invite_link:
                rooms[str(room_number)] = {
                    "room_number": room_number,
                    "channel_id": channel_id,
                    "invite_link": invite_link,
                    "status": "free",
                    "current_deal_id": None,
                    "sender_user": None,
                    "mentioned_user": None
                }
                save_rooms()
                created_count += 1
                log_info(f"Room {room_number} created")
            else:
                failed_count += 1
                log_error(f"Room {room_number}: Failed to create")
        except Exception as e:
            failed_count += 1
            log_error(f"Room {room_number}: Setup failed - {e}")

    await update.message.reply_text(
        f"<b>🏗️ CREATE NEW ROOMS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>✅ Operation Complete</b>\n\n"
        f"<b>📊 Results:</b>\n"
        f"├ 🟢 Created: <b>{created_count}</b> room(s)\n"
        f"├ 🔴 Failed: <b>{failed_count}</b> room(s)\n"
        f"└ 📋 Total Rooms: <b>{len(rooms)}</b>",
        parse_mode="HTML"
    )


async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user from the group and blacklist from bot commands. Triggered by .ban command."""
    global banned_users

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    # Check if replying to a message
    reply_to = update.message.reply_to_message
    target_user_id = None
    if reply_to and reply_to.from_user:
        # Ban the user whose message is being replied to
        target_user = reply_to.from_user
        ban_username = target_user.username.lower() if target_user.username else None
        ban_id = str(target_user.id)
        target_user_id = target_user.id
        display_name = f"@{target_user.username}" if target_user.username else f"User ID: {ban_id}"
    else:
        # Parse arguments from message text (for .ban command)
        message_text = update.message.text.strip()
        parts = message_text.split(maxsplit=1)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "<b>🚫 BAN USER</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "<b>📖 Usage:</b>\n"
                "├ <code>.ban @username</code> - Ban by username\n"
                "├ <code>.ban 123456789</code> - Ban by user ID\n"
                "└ Reply to a message with <code>.ban</code>",
                parse_mode="HTML"
            )
            return

        target = parts[1].split()[0]

        # Check if it's a user ID (numeric) or username
        if target.isdigit():
            ban_id = target
            target_user_id = int(target)
            ban_username = None
            display_name = f"@{ban_id}"
        else:
            ban_username = target.lstrip('@').lower()
            ban_id = f"username_{ban_username}"
            display_name = f"@{ban_username}"

    # First, try to ban the user from the current Telegram group
    if target_user_id:
        try:
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_user_id)
            log_info(f"User {display_name} banned from group {chat_id}")
        except Exception as e:
            log_error(f"Failed to ban user from group: {e}")

    # Then blacklist from bot commands
    if ban_id not in banned_users:
        banned_users[ban_id] = {
            "username": ban_username,
            "banned_by": user_id,
            "banned_at": datetime.now().isoformat()
        }
        save_banned_users()

    await update.message.reply_text(
        f"{display_name} is banned from the group!",
        parse_mode="HTML"
    )
    log_info(f"User {display_name} banned by admin {user_id}")


async def kickall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kick all non-admin members from the group. Triggered by /kickall command."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id not in ADMIN_USER_IDS:
        return
    
    if update.effective_chat.type == "private":
        return
    
    status_msg = await update.message.reply_text("Kicking all members...")
    
    kicked_count = 0
    failed_count = 0
    
    try:
        channel_id = chat_id
        if channel_id < 0:
            channel_id = int(str(channel_id).replace("-100", ""))
        
        log_info(f"Kickall: chat_id={chat_id}, channel_id={channel_id}")
        
        participants = await userbot_client.get_participants(channel_id)
        log_info(f"Kickall: Total participants found: {len(participants)}")
        
        admins = await userbot_client.get_participants(channel_id, filter=ChannelParticipantsAdmins)
        admin_ids = [admin.id for admin in admins]
        log_info(f"Kickall: Group admins: {admin_ids}")
        admin_ids.extend(ADMIN_USER_IDS)
        log_info(f"Kickall: All admin IDs (including bot admins): {admin_ids}")
        
        members_to_kick = []
        for participant in participants:
            log_info(f"Kickall: Checking participant {participant.id}, bot={getattr(participant, 'bot', False)}")
            if participant.id in admin_ids:
                log_info(f"Kickall: Skipping {participant.id} - is admin")
                continue
            if hasattr(participant, 'bot') and participant.bot:
                log_info(f"Kickall: Skipping {participant.id} - is bot")
                continue
            members_to_kick.append(participant.id)
        
        log_info(f"Found {len(members_to_kick)} members to kick")
        
        for member_id in members_to_kick:
            userbot_success = False
            bot_success = False
            
            try:
                kick_rights = ChatBannedRights(until_date=None, view_messages=True)
                await userbot_client(EditBannedRequest(channel=channel_id, participant=member_id, banned_rights=kick_rights))
                await asyncio.sleep(0.3)
                unban_rights = ChatBannedRights(until_date=None, view_messages=False)
                await userbot_client(EditBannedRequest(channel=channel_id, participant=member_id, banned_rights=unban_rights))
                userbot_success = True
                log_info(f"Userbot kicked member {member_id}")
            except Exception as e:
                log_error(f"Userbot failed to kick {member_id}: {e}")
            
            try:
                await context.bot.ban_chat_member(chat_id=chat_id, user_id=member_id)
                await asyncio.sleep(0.3)
                await context.bot.unban_chat_member(chat_id=chat_id, user_id=member_id)
                bot_success = True
                log_info(f"Bot kicked member {member_id}")
            except Exception as e:
                log_error(f"Bot failed to kick {member_id}: {e}")
            
            if userbot_success or bot_success:
                kicked_count += 1
            else:
                failed_count += 1
        
        await status_msg.edit_text(
            f"<b>KICKALL COMPLETE</b>\n\n"
            f"Kicked: {kicked_count} members\n"
            f"Failed: {failed_count}",
            parse_mode="HTML"
        )
        log_info(f"Kickall completed by admin {user_id}: {kicked_count} kicked, {failed_count} failed")
    except Exception as e:
        log_error(f"Kickall failed: {e}")
        await status_msg.edit_text(f"Failed to kick members: {e}")


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user from using bot commands. Triggered by .unban command."""
    global banned_users

    user_id = update.effective_user.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    # Parse arguments from message text (for .unban command)
    message_text = update.message.text.strip()
    parts = message_text.split(maxsplit=1)
    
    if len(parts) < 2:
        await update.message.reply_text(
            "<b>✅ UNBAN USER</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>📖 Usage:</b>\n"
            "├ <code>.unban @username</code> - Unban by username\n"
            "└ <code>.unban 123456789</code> - Unban by user ID",
            parse_mode="HTML"
        )
        return

    target = parts[1].split()[0]

    # Check if it's a user ID (numeric) or username
    if target.isdigit():
        ban_id = target
        display_name = f"User ID: {ban_id}"
    else:
        ban_username = target.lstrip('@').lower()
        ban_id = f"username_{ban_username}"
        display_name = f"@{ban_username}"

    if ban_id not in banned_users:
        await update.message.reply_text(
            f"<b>✅ UNBAN USER</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚠️ {display_name} is not banned.",
            parse_mode="HTML"
        )
        return

    del banned_users[ban_id]
    save_banned_users()

    await update.message.reply_text(
        f"<b>✅ UNBAN USER</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>✅ User Unbanned Successfully</b>\n\n"
        f"<b>👤 User:</b> {display_name}\n"
        f"<b>📋 Status:</b> Can now use bot commands",
        parse_mode="HTML"
    )
    log_info(f"User {display_name} unbanned by admin {user_id}")


async def group_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user from all groups where the userbot is admin. Triggered by .gunban command."""
    global userbot_client

    user_id = update.effective_user.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    # Parse arguments from message text (for .gunban command)
    message_text = update.message.text.strip()
    parts = message_text.split(maxsplit=1)
    
    if len(parts) < 2:
        await update.message.reply_text(
            "<b>🌐 GROUP UNBAN</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>📖 Usage:</b>\n"
            "├ <code>.gunban @username</code> - Unban by username\n"
            "└ <code>.gunban 123456789</code> - Unban by user ID\n\n"
            "<i>Unbans user from all groups where bot is admin.</i>",
            parse_mode="HTML"
        )
        return

    target = parts[1].split()[0]

    if userbot_client is None:
        await init_userbot()

    # Get the target user ID
    target_user_id = None
    display_name = target

    if target.isdigit():
        target_user_id = int(target)
        display_name = f"User ID: {target}"
    else:
        # Try to resolve username to user ID
        username = target.lstrip('@')
        display_name = f"@{username}"
        try:
            entity = await userbot_client.get_entity(username)
            target_user_id = entity.id
        except Exception as e:
            await update.message.reply_text(
                f"<b>🌐 GROUP UNBAN</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"❌ <b>User Not Found</b>\n\n"
                f"<b>👤 User:</b> {display_name}\n"
                f"<i>Error: {str(e)}</i>",
                parse_mode="HTML"
            )
            return

    if not target_user_id:
        await update.message.reply_text(
            f"<b>🌐 GROUP UNBAN</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"❌ <b>Invalid User</b>\n\n"
            f"Could not resolve {display_name} to a user ID.",
            parse_mode="HTML"
        )
        return

    await update.message.reply_text(
        f"<b>🌐 GROUP UNBAN</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔄 Unbanning {display_name} from all groups...",
        parse_mode="HTML"
    )

    unbanned_count = 0
    failed_count = 0
    groups_checked = 0

    from telethon.tl.functions.channels import EditBannedRequest
    from telethon.tl.types import ChatBannedRights, Channel

    # Get all dialogs (groups/channels) the userbot is in
    try:
        dialogs = await userbot_client.get_dialogs()
        
        for dialog in dialogs:
            entity = dialog.entity
            
            # Only process groups/supergroups (channels with megagroup=True or regular groups)
            if not isinstance(entity, Channel):
                continue
            
            # Skip broadcast channels (only process groups)
            if entity.broadcast:
                continue
            
            groups_checked += 1
            
            try:
                # Unban the user (remove all restrictions)
                unban_rights = ChatBannedRights(
                    until_date=None,
                    view_messages=False,
                    send_messages=False,
                    send_media=False,
                    send_stickers=False,
                    send_gifs=False,
                    send_games=False,
                    send_inline=False,
                    embed_links=False
                )
                await userbot_client(EditBannedRequest(
                    channel=entity,
                    participant=target_user_id,
                    banned_rights=unban_rights
                ))
                unbanned_count += 1
            except Exception as e:
                failed_count += 1
                log_warning(f"Could not unban user {target_user_id} from {entity.title}: {e}")
    except Exception as e:
        await update.message.reply_text(
            f"<b>🌐 GROUP UNBAN</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"❌ <b>Error</b>\n\n"
            f"Could not get group list: {str(e)}",
            parse_mode="HTML"
        )
        return

    await update.message.reply_text(
        f"<b>🌐 GROUP UNBAN</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>✅ Operation Complete</b>\n\n"
        f"<b>👤 User:</b> {display_name}\n\n"
        f"<b>📊 Results:</b>\n"
        f"├ 🔍 Groups Checked: <b>{groups_checked}</b>\n"
        f"├ 🟢 Unbanned: <b>{unbanned_count}</b>\n"
        f"└ 🔴 Failed/Not Banned: <b>{failed_count}</b>\n\n"
        f"<i>User can now rejoin these groups.</i>",
        parse_mode="HTML"
    )
    log_info(f"User {display_name} unbanned from {unbanned_count} groups by admin {user_id}")


async def list_banned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all banned users. Triggered by .banned command."""
    user_id = update.effective_user.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    if not banned_users:
        await update.message.reply_text(
            "<b>BANNED USERS LIST</b>\n\n"
            "No users are currently banned.",
            parse_mode="HTML"
        )
        return

    keyboard = [[InlineKeyboardButton("List", callback_data="show_banned_list")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "<b>BANNED USERS LIST</b>",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def set_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set a specific address (Address 1 or Address 2) for a deal. Triggered by .setaddy command."""
    user_id = update.effective_user.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    # Parse arguments from message text (for .setaddy command)
    message_text = update.message.text.strip()
    parts = message_text.split(maxsplit=1)
    
    if len(parts) < 2:
        await update.message.reply_text(
            "<b>⚙️ ADDRESS CONFIGURATION</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>Usage:</b> <code>.setaddy [deal_id]</code>\n\n"
            "<b>Example:</b> <code>.setaddy D1234</code>",
            parse_mode="HTML"
        )
        return

    deal_id = parts[1].split()[0].upper()
    if not deal_id.startswith("D"):
        deal_id = f"D{deal_id}"

    if deal_id not in deals:
        await update.message.reply_text(
            f"<b>⚙️ ADDRESS CONFIGURATION</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>❌ Deal Not Found</b>\n\n"
            f"Deal ID <code>{deal_id}</code> does not exist.",
            parse_mode="HTML"
        )
        return

    deal = deals[deal_id]
    status = deal.get('status', 'unknown')

    # Check if deal is active (not completed or cancelled)
    inactive_statuses = ['completed', 'cancelled', 'released']
    if status in inactive_statuses:
        await update.message.reply_text(
            f"<b>⚙️ ADDRESS CONFIGURATION</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>⚠️ Deal Inactive</b>\n\n"
            f"Deal <code>{deal_id}</code> is already <b>{status.capitalize()}</b>.\n"
            f"Cannot modify address for inactive deals.",
            parse_mode="HTML"
        )
        return

    # Get current deal info
    network = deal.get('network')
    current_address = deal.get('deposit_address', 'Not set')
    currency = deal.get('currency', 'USDT')
    fixed_index = deal.get('fixed_address_index')

    # Show current fixed address if set
    fixed_status = f"Address {fixed_index + 1}" if fixed_index is not None else "Not fixed (rotating)"

    # Build address selection buttons with professional styling
    keyboard = [
        [
            InlineKeyboardButton("📍 Address 1", callback_data=f"setaddy_{deal_id}_1"),
            InlineKeyboardButton("📍 Address 2", callback_data=f"setaddy_{deal_id}_2")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"setaddy_{deal_id}_cancel", style="danger")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    network_display = network.upper() if network else "Pending Selection"
    status_emoji = "🟢" if status == "active" else "🟡" if status == "pending" else "⚪"
    
    await update.message.reply_text(
        f"<b>⚙️ ADDRESS CONFIGURATION</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>📋 Deal ID:</b> <code>{deal_id}</code>\n"
        f"<b>{status_emoji} Status:</b> {status.capitalize()}\n"
        f"<b>💰 Currency:</b> {currency}\n"
        f"<b>🌐 Network:</b> {network_display}\n\n"
        f"<b>📌 Current Configuration:</b>\n"
        f"├ Fixed Address: <b>{fixed_status}</b>\n"
        f"└ Deposit Address:\n<code>{current_address}</code>\n\n"
        f"<b>Select deposit address:</b>",
        parse_mode="HTML",
        reply_markup=reply_markup
    )


async def set_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set 2FA code for a user. Only works in private chats."""
    # Ignore if not in private chat
    if update.effective_chat.type != "private":
        return

    user = update.effective_user
    user_id = user.id
    username = user.username or ""

    if not context.args:
        await update.message.reply_text(
            "Please use correct format:\n"
            "/set2fa <code>&lt;2FA_code&gt;</code>\n\n"
            "Example: /set2fa MySecret123",
            parse_mode="HTML"
        )
        return

    code = context.args[0]

    if len(code) < 6:
        await update.message.reply_text(
            "The provided 2FA code is too short. Please choose a code with at least 6 characters."
        )
        return

    user_2fa[str(user_id)] = {
        "user_id": user_id,
        "username": username,
        "code": code,
        "set_at": datetime.now().isoformat()
    }
    save_user_2fa()

    await update.message.reply_text(
        "✅ 2FA code has been set successfully.\n\n"
        "🔐 Important Security Information:\n"
        "• Always verify your 2FA code after joining the escrow room.\n"
        "• 2FA setup happens ONLY once per user.\n"
        "• The bot will NEVER ask you to set your 2FA again.\n"
        "• Admins will NEVER ask for your 2FA code.\n\n"
        "🚨 If any group or person asks you to re-set or share your 2FA code, it is a SCAM.\n"
        "Keep your 2FA code private at all times."
    )
    log_info(f"User {user_id} (@{username}) set their 2FA code")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all available commands (admin only)."""
    user_id = update.effective_user.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    msg = (
        "<b>📋 COMMAND LIST</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>👥 General Commands:</b>\n"
        "├ /escrow @username - Start escrow deal\n"
        "├ /exampleform - Show deal form format\n"
        "├ /clean - Clean room after deal\n"
        "└ /set2fa [code] - Set your 2FA code\n\n"
        "<b>🔧 Admin Commands:</b>\n"
        "├ .cmd - Show this command list\n"
        "├ .rooms - View all room statuses\n"
        "├ .empty - Empty all rooms\n"
        "├ .deleteall - Delete all rooms\n"
        "├ .newrooms - Create 20 new rooms\n"
        "├ .setup_rooms - Initialize room pool\n"
        "├ .setaddy [deal_id] - Set deal address\n"
        "├ .ban @user - Ban user from bot\n"
        "├ .unban @user - Unban from bot\n"
        "├ .gunban @user - Unban from all groups\n"
        "├ .banned - List banned users\n"
        "├ .complete - Mark deal as completed\n"
        "└ .review - Scan rooms for issues"
    )

    await update.message.reply_text(msg, parse_mode="HTML")


async def review_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to scan all rooms for assignment issues."""
    global userbot_client
    
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        return
    
    if userbot_client is None:
        await init_userbot()
    
    await update.message.reply_text(
        "<b>🔍 SCANNING ROOMS...</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please wait while I check all rooms for issues...",
        parse_mode="HTML"
    )
    
    issues = []
    
    for room_num, room_data in rooms.items():
        room_status = room_data.get('status', 'unknown')
        channel_id = room_data.get('channel_id')
        full_channel_id = f"-100{channel_id}" if channel_id else None
        
        group_exists = False
        if channel_id and userbot_client:
            try:
                entity = await userbot_client.get_entity(int(f"-100{channel_id}"))
                group_exists = True
            except Exception:
                group_exists = False
        
        has_group_data = full_channel_id in group_data if full_channel_id else False
        has_active_deal = False
        active_deal_id = None
        
        for deal_id, deal in deals.items():
            deal_channel = deal.get('channel_id')
            if deal_channel and str(deal_channel) == str(channel_id):
                deal_status = deal.get('status', '')
                if deal_status not in ['completed', 'cancelled']:
                    has_active_deal = True
                    active_deal_id = deal_id
                    break
        
        if not group_exists and channel_id:
            issues.append({
                'room': room_num,
                'type': 'deleted_group',
                'description': f"Room {room_num}: Telegram group deleted but room still exists in config",
                'fix_action': f"fix_deleted_{room_num}"
            })
        
        if room_status == 'busy' and not has_active_deal and not has_group_data:
            issues.append({
                'room': room_num,
                'type': 'busy_no_deal',
                'description': f"Room {room_num}: Marked as busy but no active deal or group data",
                'fix_action': f"fix_busy_{room_num}"
            })
        
        if room_status == 'free' and has_active_deal:
            issues.append({
                'room': room_num,
                'type': 'free_with_deal',
                'description': f"Room {room_num}: Marked as free but has active deal #{active_deal_id}",
                'fix_action': f"fix_free_{room_num}_{active_deal_id}"
            })
        
        if has_group_data and room_status == 'free':
            gd = group_data.get(full_channel_id, {})
            if gd.get('joined_users') or gd.get('sender_user'):
                issues.append({
                    'room': room_num,
                    'type': 'stale_group_data',
                    'description': f"Room {room_num}: Has stale group_data but room is free",
                    'fix_action': f"fix_stale_{room_num}"
                })
    
    if not issues:
        await update.message.reply_text(
            "<b>✅ ROOM REVIEW COMPLETE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "No issues found! All rooms are properly configured.",
            parse_mode="HTML"
        )
        return
    
    msg = (
        f"<b>⚠️ ROOM REVIEW COMPLETE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Found {len(issues)} issue(s):</b>\n\n"
    )
    
    keyboard = []
    for i, issue in enumerate(issues):
        msg += f"{i+1}. {issue['description']}\n\n"
        keyboard.append([InlineKeyboardButton(
            f"🔧 Fix Room {issue['room']}",
            callback_data=f"review_{issue['fix_action']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔧 Fix All Issues", callback_data="review_fix_all")])
    
    await update.message.reply_text(
        msg,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_review_fix(query, callback_data):
    """Handle fix buttons from .review command."""
    global rooms, group_data, deals
    
    action = callback_data.replace("review_", "")
    
    if action == "fix_all":
        fixed_count = 0
        for room_num, room_data in list(rooms.items()):
            room_status = room_data.get('status', 'unknown')
            channel_id = room_data.get('channel_id')
            full_channel_id = f"-100{channel_id}" if channel_id else None
            
            has_group_data = full_channel_id in group_data if full_channel_id else False
            has_active_deal = False
            
            for deal_id, deal in deals.items():
                deal_channel = deal.get('channel_id')
                if deal_channel and str(deal_channel) == str(channel_id):
                    deal_status = deal.get('status', '')
                    if deal_status not in ['completed', 'cancelled']:
                        has_active_deal = True
                        break
            
            if room_status == 'busy' and not has_active_deal and not has_group_data:
                rooms[room_num]['status'] = 'free'
                rooms[room_num]['sender_user'] = None
                rooms[room_num]['mentioned_user'] = None
                rooms[room_num]['current_deal_id'] = None
                fixed_count += 1
            
            if room_status == 'free' and has_group_data:
                if full_channel_id in group_data:
                    del group_data[full_channel_id]
                    fixed_count += 1
        
        save_rooms()
        save_group_data()
        
        await query.edit_message_text(
            f"<b>✅ FIXES APPLIED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Fixed {fixed_count} issue(s).\n\n"
            f"Run <code>.review</code> again to verify.",
            parse_mode="HTML"
        )
        return
    
    if action.startswith("fix_busy_"):
        room_num = action.replace("fix_busy_", "")
        if room_num in rooms:
            rooms[room_num]['status'] = 'free'
            rooms[room_num]['sender_user'] = None
            rooms[room_num]['mentioned_user'] = None
            rooms[room_num]['current_deal_id'] = None
            save_rooms()
            
            channel_id = rooms[room_num].get('channel_id')
            full_channel_id = f"-100{channel_id}" if channel_id else None
            if full_channel_id and full_channel_id in group_data:
                del group_data[full_channel_id]
                save_group_data()
            
            await query.edit_message_text(
                f"<b>✅ FIXED</b>\n\n"
                f"Room {room_num} has been marked as free.",
                parse_mode="HTML"
            )
        return
    
    if action.startswith("fix_stale_"):
        room_num = action.replace("fix_stale_", "")
        if room_num in rooms:
            channel_id = rooms[room_num].get('channel_id')
            full_channel_id = f"-100{channel_id}" if channel_id else None
            if full_channel_id and full_channel_id in group_data:
                del group_data[full_channel_id]
                save_group_data()
            
            await query.edit_message_text(
                f"<b>✅ FIXED</b>\n\n"
                f"Stale group_data for Room {room_num} has been cleared.",
                parse_mode="HTML"
            )
        return
    
    if action.startswith("fix_free_"):
        parts = action.replace("fix_free_", "").split("_")
        room_num = parts[0]
        deal_id = parts[1] if len(parts) > 1 else None
        
        if room_num in rooms:
            rooms[room_num]['status'] = 'busy'
            if deal_id:
                rooms[room_num]['current_deal_id'] = deal_id
            save_rooms()
            
            await query.edit_message_text(
                f"<b>✅ FIXED</b>\n\n"
                f"Room {room_num} has been marked as busy.",
                parse_mode="HTML"
            )
        return
    
    if action.startswith("fix_deleted_"):
        room_num = action.replace("fix_deleted_", "")
        if room_num in rooms:
            rooms[room_num]['status'] = 'free'
            rooms[room_num]['channel_id'] = None
            rooms[room_num]['invite_link'] = None
            rooms[room_num]['sender_user'] = None
            rooms[room_num]['mentioned_user'] = None
            rooms[room_num]['current_deal_id'] = None
            save_rooms()
            
            await query.edit_message_text(
                f"<b>✅ FIXED</b>\n\n"
                f"Room {room_num} config cleared. Run <code>.setup_rooms</code> to recreate.",
                parse_mode="HTML"
            )
        return
    
    await query.answer("Unknown fix action")


async def main():
    load_allowed_users()
    load_group_data()
    load_deals()
    load_rooms()
    load_banned_users()
    load_user_2fa()
    log_info("Database initialized")

    # Log room status
    total_rooms = len(rooms)
    free_rooms = sum(1 for r in rooms.values() if r.get('status') == 'free')
    busy_rooms = total_rooms - free_rooms
    log_info(f"Rooms loaded: {total_rooms} total, {free_rooms} free, {busy_rooms} busy")

    # Log active deals
    active_deals = len(deals)
    if active_deals > 0:
        log_info(f"Active deals: {active_deals}")

    # Log banned users
    if banned_users:
        log_info(f"Banned users: {len(banned_users)}")

    await init_userbot()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # General commands (slash prefix)
    app.add_handler(CommandHandler("escrow", escrow))
    app.add_handler(CommandHandler("exampleform", exampleform))
    app.add_handler(CommandHandler("clean", clean))
    app.add_handler(CommandHandler("set2fa", set_2fa))
    app.add_handler(CommandHandler("kickall", kickall))
    # Admin commands (dot prefix)
    app.add_handler(MessageHandler(filters.Regex(r'^\.setup_rooms\b'), setup_rooms))
    app.add_handler(MessageHandler(filters.Regex(r'^\.rooms\b'), rooms_status))
    app.add_handler(MessageHandler(filters.Regex(r'^\.empty\b'), empty_all_rooms))
    app.add_handler(MessageHandler(filters.Regex(r'^\.deleteall\b'), delete_all_rooms))
    app.add_handler(MessageHandler(filters.Regex(r'^\.newrooms\b'), create_new_rooms))
    app.add_handler(MessageHandler(filters.Regex(r'^\.ban\b'), ban_user))
    app.add_handler(MessageHandler(filters.Regex(r'^\.unban\b'), unban_user))
    app.add_handler(MessageHandler(filters.Regex(r'^\.gunban\b'), group_unban_user))
    app.add_handler(MessageHandler(filters.Regex(r'^\.banned\b'), list_banned))
    app.add_handler(MessageHandler(filters.Regex(r'^\.cmd\b'), cmd_list))
    app.add_handler(MessageHandler(filters.Regex(r'^\.setaddy\b'), set_address))
    app.add_handler(MessageHandler(filters.Regex(r'^\.complete\b'), complete_deal))
    app.add_handler(MessageHandler(filters.Regex(r'^\.review\b'), review_rooms))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(ChatMemberHandler(handle_chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message
    ))
    app.add_handler(MessageHandler(
        filters.PHOTO, handle_photo
    ))

    log_info("Bot started successfully")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
