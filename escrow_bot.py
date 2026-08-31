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
    Update, ChatJoinRequest, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQueryResultArticle, InputTextMessageContent
)
from telegram.ext import (  # noqa: E402
    ApplicationBuilder, CommandHandler, ContextTypes,
    ChatJoinRequestHandler, CallbackQueryHandler, MessageHandler, filters,
    ChatMemberHandler, InlineQueryHandler, ApplicationHandlerStop, TypeHandler
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
from telethon.tl.functions.contacts import ResolveUsernameRequest, ImportContactsRequest  # noqa: E402
from telethon.tl.types import InputPhoneContact  # noqa: E402
from telethon.tl.types import (
    ChatAdminRights, Channel, ChatBannedRights, ChannelParticipantsAdmins, User
)  # noqa: E402


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
OLD_ROOMS_FILE = "old_rooms.json"
USER_2FA_FILE = "user_2fa.json"
DEAL_FORM_CACHE_FILE = "deal_form_cache.json"
ESCROW_ADDRESSES_FILE = "escrow_addresses.json"
FORCE_ESCROW_FILE = "force_escrow.json"
WORK_CHATS_FILE = "work_chats.json"
DEAL_HISTORY_FILE = "deal_history.json"
HIDDEN_VOLUME_FILE = "hidden_volume.json"

# Default addresses and QR images (used if escrow_addresses.json doesn't exist)
_DEFAULT_ADDRESSES = {
    "USDT_BSC": {
        "addresses": ["0x526F1629c3624643199c15d6eC2EBdF3Fde49265", "0xf282e789e835ed379aea84ece204d2d643e6774f"],
        "qr_images": ["bsc_address1_qr.jpg", "bsc_qr_2.jpg"]
    },
    "USDT_POLYGON": {
        "addresses": ["0x526F1629c3624643199c15d6eC2EBdF3Fde49265", "0xf282e789e835ed379aea84ece204d2d643e6774f"],
        "qr_images": ["polygon_address1_qr.jpg", "polygon_qr_2.jpg"]
    },
    "USDT_SOL": {
        "addresses": ["NeT11YPWEr9aGacptszdXYFnJYETMGzS4vweVfQAnW3", "5KDFAQ6p1ofPWZBGaxWTSu2EziyX9GyQ36H547zxBou3"],
        "qr_images": ["sol_address1_qr.jpg", "sol_qr_2.jpg"]
    },
    "USDC_BSC": {
        "addresses": ["0x526F1629c3624643199c15d6eC2EBdF3Fde49265", "0xf282e789e835ed379aea84ece204d2d643e6774f"],
        "qr_images": ["usdc_bsc_address1_qr.jpg", "usdc_bsc_qr_2.jpg"]
    },
    "USDC_POLYGON": {
        "addresses": ["0x526F1629c3624643199c15d6eC2EBdF3Fde49265"],
        "qr_images": ["usdc_polygon_address1_qr.jpg"]
    },
    "USDC_SOL": {
        "addresses": ["NeT11YPWEr9aGacptszdXYFnJYETMGzS4vweVfQAnW3", "9AHM8xU6rW6sC4hZJcpciaT64tqstcw5o7cWW31eKZB5"],
        "qr_images": ["usdc_sol_qr_1.jpg", "usdc_sol_address1_qr.jpg"]
    }
}


def load_escrow_addresses():
    """Load escrow addresses from JSON file, or use defaults."""
    try:
        with open(ESCROW_ADDRESSES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # First run - save defaults to file
        save_escrow_addresses(_DEFAULT_ADDRESSES)
        return dict(_DEFAULT_ADDRESSES)


def save_escrow_addresses(data=None):
    """Save current escrow addresses to JSON file."""
    if data is None:
        data = _build_current_addresses()
    with open(ESCROW_ADDRESSES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _build_current_addresses():
    """Build current addresses dict from in-memory arrays."""
    return {
        "USDT_BSC": {"addresses": list(BSC_DEPOSIT_ADDRESSES), "qr_images": list(BSC_QR_IMAGES)},
        "USDT_POLYGON": {"addresses": list(POLYGON_DEPOSIT_ADDRESSES), "qr_images": list(POLYGON_QR_IMAGES)},
        "USDT_SOL": {"addresses": list(SOL_DEPOSIT_ADDRESSES), "qr_images": list(SOL_QR_IMAGES)},
        "USDC_BSC": {"addresses": list(USDC_BSC_DEPOSIT_ADDRESSES), "qr_images": list(USDC_BSC_QR_IMAGES)},
        "USDC_POLYGON": {"addresses": [USDC_POLYGON_DEPOSIT_ADDRESS], "qr_images": [USDC_POLYGON_QR_IMAGE]},
        "USDC_SOL": {"addresses": list(USDC_SOL_DEPOSIT_ADDRESSES), "qr_images": list(USDC_SOL_QR_IMAGES)},
    }


def _apply_addresses_from_data(data):
    """Apply loaded address data to in-memory arrays."""
    global USDC_POLYGON_DEPOSIT_ADDRESS, USDC_POLYGON_QR_IMAGE

    d = data.get("USDT_BSC", {})
    if d.get("addresses"):
        BSC_DEPOSIT_ADDRESSES[:] = d["addresses"]
        BSC_QR_IMAGES[:] = d["qr_images"]

    d = data.get("USDT_POLYGON", {})
    if d.get("addresses"):
        POLYGON_DEPOSIT_ADDRESSES[:] = d["addresses"]
        POLYGON_QR_IMAGES[:] = d["qr_images"]

    d = data.get("USDT_SOL", {})
    if d.get("addresses"):
        SOL_DEPOSIT_ADDRESSES[:] = d["addresses"]
        SOL_QR_IMAGES[:] = d["qr_images"]

    d = data.get("USDC_BSC", {})
    if d.get("addresses"):
        USDC_BSC_DEPOSIT_ADDRESSES[:] = d["addresses"]
        USDC_BSC_QR_IMAGES[:] = d["qr_images"]

    d = data.get("USDC_POLYGON", {})
    if d.get("addresses"):
        USDC_POLYGON_DEPOSIT_ADDRESS = d["addresses"][0]
        USDC_POLYGON_QR_IMAGE = d["qr_images"][0]

    d = data.get("USDC_SOL", {})
    if d.get("addresses"):
        USDC_SOL_DEPOSIT_ADDRESSES[:] = d["addresses"]
        USDC_SOL_QR_IMAGES[:] = d["qr_images"]

    # Refresh DEPOSIT_ADDRESSES dict
    DEPOSIT_ADDRESSES["BSC"] = BSC_DEPOSIT_ADDRESSES[0]
    DEPOSIT_ADDRESSES["POLYGON"] = POLYGON_DEPOSIT_ADDRESSES[0]
    DEPOSIT_ADDRESSES["SOL"] = SOL_DEPOSIT_ADDRESSES[0]
    DEPOSIT_ADDRESSES["USDC_BSC"] = USDC_BSC_DEPOSIT_ADDRESSES[0]
    DEPOSIT_ADDRESSES["USDC_POLYGON"] = USDC_POLYGON_DEPOSIT_ADDRESS
    DEPOSIT_ADDRESSES["USDC_SOL"] = USDC_SOL_DEPOSIT_ADDRESSES[0]


# QR Images for USDT addresses
BSC_QR_IMAGES = [
    "bsc_address1_qr.jpg",    # QR for Address 1
    "bsc_qr_2.jpg"     # QR for Address 2
]
POLYGON_QR_IMAGES = [
    "polygon_address1_qr.jpg",  # QR for Address 1
    "polygon_qr_2.jpg"   # QR for Address 2
]
SOL_QR_IMAGES = [
    "sol_address1_qr.jpg",    # QR for Address 1
    "sol_qr_2.jpg"     # QR for Address 2
]

# USDT Deposit Addresses
BSC_DEPOSIT_ADDRESSES = [
    "0x526F1629c3624643199c15d6eC2EBdF3Fde49265",  # Address 1
    "0xf282e789e835ed379aea84ece204d2d643e6774f"   # Address 2
]

POLYGON_DEPOSIT_ADDRESSES = [
    "0x526F1629c3624643199c15d6eC2EBdF3Fde49265",  # Address 1
    "0xf282e789e835ed379aea84ece204d2d643e6774f"   # Address 2
]

SOL_DEPOSIT_ADDRESSES = [
    "NeT11YPWEr9aGacptszdXYFnJYETMGzS4vweVfQAnW3",  # Address 1
    "5KDFAQ6p1ofPWZBGaxWTSu2EziyX9GyQ36H547zxBou3"   # Address 2
]

# USDC Deposit Addresses
USDC_BSC_QR_IMAGES = [
    "usdc_bsc_address1_qr.jpg",  # QR for Address 1
    "usdc_bsc_qr_2.jpg"   # QR for Address 2
]
USDC_BSC_DEPOSIT_ADDRESSES = [
    "0x526F1629c3624643199c15d6eC2EBdF3Fde49265",  # Address 1
    "0xf282e789e835ed379aea84ece204d2d643e6774f"   # Address 2
]

# USDC Polygon
USDC_POLYGON_DEPOSIT_ADDRESS = "0x526F1629c3624643199c15d6eC2EBdF3Fde49265"
USDC_POLYGON_QR_IMAGE = "usdc_polygon_address1_qr.jpg"

# USDC Solana
USDC_SOL_QR_IMAGES = [
    "usdc_sol_qr_1.jpg",          # QR for Address 1
    "usdc_sol_address1_qr.jpg"    # QR for Address 2
]
USDC_SOL_DEPOSIT_ADDRESSES = [
    "NeT11YPWEr9aGacptszdXYFnJYETMGzS4vweVfQAnW3",  # Address 1
    "9AHM8xU6rW6sC4hZJcpciaT64tqstcw5o7cWW31eKZB5"   # Address 2
]

DEPOSIT_ADDRESSES = {
    "BSC": BSC_DEPOSIT_ADDRESSES[0],
    "POLYGON": POLYGON_DEPOSIT_ADDRESSES[0],
    "SOL": SOL_DEPOSIT_ADDRESSES[0],
    "USDC_BSC": USDC_BSC_DEPOSIT_ADDRESSES[0],
    "USDC_POLYGON": USDC_POLYGON_DEPOSIT_ADDRESS,
    "USDC_SOL": USDC_SOL_DEPOSIT_ADDRESSES[0]
}

bsc_address_index = 0
polygon_address_index = 0
sol_address_index = 0
usdc_bsc_address_index = 0
usdc_sol_address_index = 0

# State tracking for /changeaddy admin sessions
# Key: user_id, Value: dict with slot, currency, network, step
changeaddy_sessions = {}
profile_cooldowns = {}

ADMIN_USER_IDS = [7338429782, 8346781181, 6662820986, 7090417167, 6643621069, 6302273200]
WORKLIST_ADMIN_ID = 6643621069

# Extra admin added to every newly created escrow group (resolved by ID, then
# username, then phone). ID is the source of truth; username may change.
EXTRA_ADMIN_USER_ID = 6302273200
EXTRA_ADMIN_USERNAME = "iUsrXD"
EXTRA_ADMIN_PHONE = "+918288914135"

# Only these admins are treated as admins for deal cancellation (the ones that
# stay in the group after /clean and .empty). Every other admin is treated as a
# normal user for cancel purposes (can only cancel a deal they're a party to).
CANCEL_ADMIN_IDS = [6662820986, EXTRA_ADMIN_USER_ID]

DEAL_LOG_CHANNEL_ID = -1004433511813

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

CONFIRMATION_TARGET = 30

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
deal_form_cache = {}
force_escrow_users = {}
work_chats = []
deal_history = {}
hidden_volume_users = {}


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


old_rooms = []

def load_old_rooms():
    global old_rooms
    try:
        with open(OLD_ROOMS_FILE, "r") as f:
            old_rooms = json.load(f)
    except FileNotFoundError:
        old_rooms = []

def save_old_rooms():
    with open(OLD_ROOMS_FILE, "w") as f:
        json.dump(old_rooms, f)

def add_old_room(channel_id, title=""):
    """Store an old room's channel ID for later deletion."""
    entry = {"channel_id": int(channel_id), "title": title}
    if not any(r["channel_id"] == int(channel_id) for r in old_rooms):
        old_rooms.append(entry)
        save_old_rooms()


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


def load_deal_form_cache():
    global deal_form_cache
    try:
        with open(DEAL_FORM_CACHE_FILE, "r") as f:
            deal_form_cache = json.load(f)
    except FileNotFoundError:
        deal_form_cache = {}


def save_deal_form_cache():
    with open(DEAL_FORM_CACHE_FILE, "w") as f:
        json.dump(deal_form_cache, f)



def load_force_escrow():
    global force_escrow_users
    try:
        with open(FORCE_ESCROW_FILE, "r") as f:
            force_escrow_users = json.load(f)
    except FileNotFoundError:
        force_escrow_users = {}


def save_force_escrow():
    with open(FORCE_ESCROW_FILE, "w") as f:
        json.dump(force_escrow_users, f)


def load_work_chats():
    global work_chats
    try:
        with open(WORK_CHATS_FILE, "r") as f:
            loaded_chats = json.load(f)
        work_chats = [int(chat_id) for chat_id in loaded_chats]
    except (FileNotFoundError, TypeError, ValueError):
        work_chats = []


def save_work_chats():
    with open(WORK_CHATS_FILE, "w") as f:
        json.dump(work_chats, f)


def load_deal_history():
    global deal_history
    try:
        with open(DEAL_HISTORY_FILE, "r") as f:
            deal_history = json.load(f)
    except FileNotFoundError:
        deal_history = {}


def save_deal_history():
    with open(DEAL_HISTORY_FILE, "w") as f:
        json.dump(deal_history, f)


def load_hidden_volume():
    global hidden_volume_users
    try:
        with open(HIDDEN_VOLUME_FILE, "r") as f:
            loaded_users = json.load(f)
        if isinstance(loaded_users, dict):
            hidden_volume_users = {
                str(user_id): True for user_id in loaded_users
            }
        else:
            hidden_volume_users = {}
    except (FileNotFoundError, TypeError, ValueError):
        hidden_volume_users = {}


def save_hidden_volume():
    with open(HIDDEN_VOLUME_FILE, "w") as f:
        json.dump(hidden_volume_users, f)


async def record_deal_result(deal, deal_id, status, chat_id):
    """Persist a completed or cancelled deal for profile statistics."""
    try:
        if status not in ("completed", "cancelled"):
            return

        history_key = str(deal_id)
        existing = deal_history.get(history_key)
        if existing:
            if (
                existing.get("status") == "completed"
                and status == "cancelled"
            ) or existing.get("status") == status:
                return

        buyer = deal["buyer"]
        seller = deal["seller"]
        currency = deal["currency"]
        amount = 0.0
        try:
            amount = float(deal.get("amount_crypto"))
        except (TypeError, ValueError):
            pass

        group_info = group_data.get(str(chat_id), {})
        identities = (
            (
                group_info.get("sender_user"),
                group_info.get("sender_user_id")
            ),
            (
                group_info.get("mentioned_user"),
                group_info.get("mentioned_user_id")
            )
        )

        async def resolve_user_id(username):
            username_clean = str(username or "").lstrip("@").lower()
            for known_username, known_user_id in identities:
                if (
                    username_clean
                    == str(known_username or "").lstrip("@").lower()
                ):
                    try:
                        return int(known_user_id)
                    except (TypeError, ValueError):
                        break

            if not username_clean:
                return None
            try:
                global userbot_client
                if userbot_client is None:
                    await init_userbot()
                if userbot_client is not None:
                    entity = await userbot_client.get_entity(username_clean)
                    if isinstance(entity, User):
                        return int(entity.id)
            except Exception as resolve_error:
                log_warning(
                    f"Could not resolve deal user {username_clean}: "
                    f"{resolve_error}"
                )
            return None

        deal_history[history_key] = {
            "status": status,
            "ts": time.time(),
            "currency": currency,
            "amount": amount,
            "buyer": str(buyer).lstrip("@").lower(),
            "seller": str(seller).lstrip("@").lower(),
            "buyer_id": await resolve_user_id(buyer),
            "seller_id": await resolve_user_id(seller)
        }
        save_deal_history()
    except Exception as history_error:
        log_warning(
            f"Could not record deal result for {deal_id}: {history_error}"
        )


def is_force_escrow_user(username):
    """Check if a username is whitelisted to bypass the active-deal restriction."""
    if not username:
        return False
    return username.lstrip('@').lower() in force_escrow_users


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


import re
import base58


def is_valid_evm_address(address):
    """Check if address is a valid EVM (BSC/Polygon) hex address."""
    return bool(re.fullmatch(r'0x[0-9a-fA-F]{40}', address))


def is_valid_solana_address(address):
    """Check if address is a valid Solana base58 address."""
    try:
        decoded = base58.b58decode(address)
        return len(decoded) == 32
    except Exception:
        return False


def is_valid_crypto_address(address, network):
    """Validate a crypto address for the given network."""
    if network in ("BSC", "POLYGON", "USDC_BSC", "USDC_POLYGON"):
        return is_valid_evm_address(address)
    elif network in ("SOL", "USDC_SOL"):
        return is_valid_solana_address(address)
    return False


def truncate_address(address):
    """Truncate address to first 3 and last 4 characters."""
    if not address or len(address) < 8:
        return address or "N/A"
    return f"{address[:3]}...{address[-4:]}"


def build_deal_log_message(deal_id, buyer, seller, room_num, status, deposit_address=None, amount=None, token=None, escrow_sender=None, initiator_joined=False, counterparty_joined=False, mentioned_user=None, show_parties=False):
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
    
    # Build buyer/seller lines (only shown after form is submitted)
    parties_lines = ""
    if show_parties and buyer and seller and buyer != 'N/A' and seller != 'N/A':
        parties_lines = (
            f"• <b>Deal ID</b> - #{deal_id}\n"
            f"• <b>Seller</b> - {seller}\n"
            f"• <b>Buyer</b> - {buyer}\n"
        )
    
    msg = (
        f"<b>ESCROW ROOM {room_num}</b>\n\n"
        f"• <b>Initiator ({initiator}) Status</b> - {initiator_status}\n"
        f"• <b>CounterParty ({counterparty}) Status</b> - {counterparty_status}\n"
        f"{parties_lines}"
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
        
        # Show buyer/seller parties once the deal has form data
        show_parties = buyer != 'N/A' and seller != 'N/A'
        
        msg = build_deal_log_message(deal_id, buyer, seller, room_num, status, deposit_address, amount, token, escrow_sender, initiator_joined, counterparty_joined, mentioned_user, show_parties)
        
        # Add "DEAL INFO" button if deal has form data
        reply_markup = None
        if show_parties and deal.get('corrected_form_text'):
            keyboard = [[InlineKeyboardButton("DEAL INFO", callback_data=f"checkescrow_{deal_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        await bot.edit_message_text(
            chat_id=DEAL_LOG_CHANNEL_ID,
            message_id=log_message_id,
            text=msg,
            parse_mode="HTML",
            reply_markup=reply_markup
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
        full_channel_id = get_marked_peer_id(channel_id)
        if full_channel_id is None:
            return False
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


def entity_has_username(entity):
    """Return True if a Telethon user entity has any active username.

    Accounts for the newer multiple/collectible usernames feature where the
    primary `username` field may be None while active usernames live in the
    `usernames` list.
    """
    if getattr(entity, 'username', None):
        return True
    for u in getattr(entity, 'usernames', None) or []:
        if getattr(u, 'active', False) and getattr(u, 'username', None):
            return True
    return False


def get_marked_peer_id(channel_id):
    """Normalize a stored room channel id to a Telethon marked peer id."""
    if channel_id is None:
        return None

    channel_str = str(channel_id).strip()
    if not channel_str:
        return None
    if channel_str.startswith("-100"):
        try:
            return int(channel_str)
        except ValueError:
            return None
    try:
        return int(f"-100{channel_str.lstrip('-')}")
    except ValueError:
        return None


def parse_work_chat_id(value):
    """Parse a raw or marked numeric Telegram chat id."""
    chat_id = str(value).strip()
    if chat_id.startswith("@"):
        return None
    try:
        return int(chat_id)
    except ValueError:
        return None


def is_work_chat(chat_id):
    """Return True when a chat matches an entry in the working list."""
    try:
        parsed_chat_id = int(chat_id)
    except (TypeError, ValueError):
        return False
    if parsed_chat_id in work_chats:
        return True

    marked_chat_id = get_marked_peer_id(parsed_chat_id)
    if marked_chat_id is None:
        return False
    return any(
        get_marked_peer_id(stored_chat_id) == marked_chat_id
        for stored_chat_id in work_chats
    )


def is_worklist_management_update(update):
    """Return True for an authorized worklist-management command."""
    user = update.effective_user
    message = update.effective_message
    if not user or user.id != WORKLIST_ADMIN_ID or not message:
        return False

    text = message.text or ""
    if not text.startswith("/"):
        return False
    command = text.split()[0].split("@", 1)[0].lower()
    return command in {"/addchat", "/removechat", "/worklist"}


async def whitelist_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Drop updates from chats outside the configured working list."""
    chat = update.effective_chat
    if is_worklist_management_update(update):
        return
    if not chat:
        return
    if chat.type == "private" or is_work_chat(chat.id):
        return
    if chat.id == DEAL_LOG_CHANNEL_ID:
        return

    marked_chat_id = get_marked_peer_id(chat.id)
    if marked_chat_id is not None:
        for room_data in rooms.values():
            if get_marked_peer_id(room_data.get("channel_id")) == marked_chat_id:
                return

        finished_statuses = {
            "completed", "cancelled", "released", "payment_released"
        }
        for deal in deals.values():
            if (
                get_marked_peer_id(deal.get("channel_id")) == marked_chat_id
                and deal.get("status") not in finished_statuses
            ):
                return

    raise ApplicationHandlerStop


def room_has_active_deal(channel_id):
    """Return True if a room's channel has a deal that isn't finished."""
    channel_id_str = str(channel_id).replace("-100", "") if str(channel_id).startswith("-100") else str(channel_id)
    finished = ('completed', 'cancelled', 'released', 'payment_released')
    for deal in deals.values():
        if str(deal.get('channel_id')) == channel_id_str:
            if deal.get('status', '') not in finished:
                return True
    return False


def protected_from_removal_ids(bot_id, userbot_id):
    """IDs that must never be kicked/banned from escrow rooms."""
    return {bot_id, userbot_id, 6662820986, EXTRA_ADMIN_USER_ID}


async def resolve_extra_admin(client):
    """Resolve the extra-admin user via ID, username, or phone (with contact import).

    Returns the Telethon user entity, or None if it cannot be resolved.
    """
    for label, identifier in (
        ("id", EXTRA_ADMIN_USER_ID),
        ("username", EXTRA_ADMIN_USERNAME),
        ("phone", EXTRA_ADMIN_PHONE),
    ):
        try:
            entity = await client.get_entity(identifier)
            if entity is not None:
                return entity
        except Exception as e:
            log_warning(f"Extra admin resolve by {label} failed: {e}")
    try:
        imported = await client(ImportContactsRequest(
            contacts=[InputPhoneContact(
                client_id=0,
                phone=EXTRA_ADMIN_PHONE,
                first_name="Escrow",
                last_name="Admin"
            )]
        ))
        if imported.users:
            return imported.users[0]
        log_warning("Extra admin phone import returned no users")
    except Exception as e:
        log_warning(f"Extra admin phone import failed: {e}")
    return None


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
                    full_channel_id = get_marked_peer_id(channel_id)
                    if full_channel_id is None:
                        raise ValueError("Invalid channel_id")
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
    return f"D{random.randint(36432, 99999)}"


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
                    style="primary", icon_custom_emoji_id="6253755610299372930"
                ),
                InlineKeyboardButton(
                    "USDC[SOL]", callback_data=f"network_{deal_id}_USDC_SOL",
                    style="primary", icon_custom_emoji_id="6255864821493796954"
                )
            ],
            [
                InlineKeyboardButton(
                    "USDC[POLYGON]", callback_data=f"network_{deal_id}_USDC_POLYGON",
                    style="primary", icon_custom_emoji_id="6253279916901535974"
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
                    style="primary", icon_custom_emoji_id="6253755610299372930"
                ),
                InlineKeyboardButton(
                    "USDT[SOL]", callback_data=f"network_{deal_id}_SOL",
                    style="primary", icon_custom_emoji_id="6255864821493796954"
                )
            ],
            [
                InlineKeyboardButton(
                    "USDT[POLYGON]", callback_data=f"network_{deal_id}_POLYGON",
                    style="primary", icon_custom_emoji_id="6253279916901535974"
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


def get_usdc_sol_deposit_info():
    """Get rotating USDC SOL deposit address and QR image."""
    global usdc_sol_address_index
    address = USDC_SOL_DEPOSIT_ADDRESSES[usdc_sol_address_index]
    qr_image = USDC_SOL_QR_IMAGES[usdc_sol_address_index]
    usdc_sol_address_index = (usdc_sol_address_index + 1) % len(USDC_SOL_DEPOSIT_ADDRESSES)
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
                    for i, addr in enumerate(USDC_SOL_DEPOSIT_ADDRESSES):
                        if addr.lower() == deposit_address.lower():
                            qr_image = USDC_SOL_QR_IMAGES[i]
                            break
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
            if fixed_index is not None and fixed_index < len(USDC_SOL_DEPOSIT_ADDRESSES):
                deposit_address = USDC_SOL_DEPOSIT_ADDRESSES[fixed_index]
                qr_image = USDC_SOL_QR_IMAGES[fixed_index]
            else:
                deposit_address, qr_image = get_usdc_sol_deposit_info()
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


async def get_evm_block_number(base_network):
    """Get the latest EVM block number using configured RPC fallbacks."""
    if base_network == "BSC":
        rpc_endpoints = BSC_RPC_ENDPOINTS
    elif base_network == "POLYGON":
        rpc_endpoints = POLYGON_RPC_ENDPOINTS
    else:
        return None

    timeout = aiohttp.ClientTimeout(total=15)
    block_payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1
    }

    for rpc_endpoint in rpc_endpoints:
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    rpc_endpoint,
                    json=block_payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        log_warning(
                            f"{base_network} RPC {rpc_endpoint} error getting block number: "
                            f"{response.status}"
                        )
                        continue
                    data = await response.json()
                    if "error" in data:
                        log_warning(f"{base_network} RPC {rpc_endpoint} error: {data['error']}")
                        continue
                    return int(data["result"], 16)
        except asyncio.TimeoutError:
            log_warning(f"{base_network} RPC {rpc_endpoint} timeout")
        except Exception as e:
            log_warning(f"{base_network} RPC {rpc_endpoint} error: {e}")

    log_warning(f"All {base_network} RPC endpoints failed getting block number")
    return None


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


def build_payment_detected_message(
    deal_id, amount, total, deal_amount, curr, confirmations
):
    """Build payment detected message."""
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


def build_deposit_confirmation_message(deal_id, amount, curr, confirmations):
    """Build the live deposit confirmation message."""
    msg = (
        f"<b><i>Deal</i></b> #{deal_id}\n\n"
        f"<b>DEPOSIT IS BEING CONFIRMED</b>\n\n"
        f"Amount: <b>{amount:.2f} {curr}</b>\n"
        f"Current Confirmations: {confirmations}\n"
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


async def finalize_payment_received(bot, deal, deal_id, chat_id, received_amount):
    """Send the post-confirmation payment messages."""
    try:
        await update_deal_log(bot, deal_id, "Payment Received")
    except Exception as log_error:
        log_warning(f"Could not update payment received log for deal {deal_id}: {log_error}")

    try:
        received_msg = build_usdt_received_message(
            deal, deal_id, received_amount
        )
        await bot.send_message(
            chat_id=chat_id,
            text=received_msg,
            parse_mode="HTML",
            reply_markup=get_deal_buttons(deal_id)
        )
    except Exception as received_error:
        log_warning(f"Could not send payment received message for deal {deal_id}: {received_error}")

    payment_type = deal.get('payment_details_type', 'text')
    sent_details = None
    if payment_type == 'photo':
        photo_id = deal.get('payment_details')
        try:
            details_msg = build_payment_details_message(deal, deal_id)
            sent_details = await bot.send_photo(
                chat_id=chat_id,
                photo=photo_id,
                caption=details_msg,
                parse_mode="HTML"
            )
        except Exception as photo_error:
            log_warning(f"Could not send payment details photo for deal {deal_id}: {photo_error}")
            try:
                sent_details = await bot.send_message(
                    chat_id=chat_id,
                    text=build_payment_details_message(deal, deal_id),
                    parse_mode="HTML"
                )
            except Exception as details_error:
                log_warning(f"Could not send payment details for deal {deal_id}: {details_error}")
    else:
        try:
            details_msg = build_payment_details_message(deal, deal_id)
            sent_details = await bot.send_message(
                chat_id=chat_id,
                text=details_msg,
                parse_mode="HTML"
            )
        except Exception as details_error:
            log_warning(f"Could not send payment details for deal {deal_id}: {details_error}")

    if sent_details:
        await update_current_stage_button(bot, deal, chat_id, sent_details.message_id)


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
    confirmation_check_interval = 5
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
        detected_transactions = []

        for tx in transactions:
            if tx.get("to", "").lower() == deposit_address.lower():
                detected_transactions.append(tx)
                amount = parse_transaction_amount(tx, network)
                total_received += amount
                if amount > latest_amount:
                    latest_amount = amount

        if total_received > 0:
            if deal_id not in active_monitors or deal_id not in deals:
                return

            deal['received_amount'] = total_received
            save_deals()

            # Update deal log - Deposit Detected with amount
            await update_deal_log(bot, deal_id, f"Deposit Detected [ {total_received} {currency} ]")

            base_network = network.replace("USDC_", "") if network.startswith("USDC_") else network
            detected_tx_block = None
            initial_confirmations = CONFIRMATION_TARGET
            if base_network in ("BSC", "POLYGON"):
                block_numbers = []
                for tx in detected_transactions:
                    try:
                        block_numbers.append(int(tx.get("blockNumber", "0")))
                    except (TypeError, ValueError):
                        continue
                if block_numbers:
                    detected_tx_block = max(block_numbers)

                latest_block = await get_evm_block_number(base_network)
                if latest_block is None or detected_tx_block is None:
                    initial_confirmations = 1
                else:
                    initial_confirmations = max(
                        1, latest_block - detected_tx_block + 1
                    )

            confirming_msg = build_deposit_confirmation_message(
                deal_id,
                latest_amount,
                currency,
                f"{initial_confirmations}/{CONFIRMATION_TARGET}"
            )
            sent_confirming = None
            try:
                sent_confirming = await bot.send_message(
                    chat_id=chat_id,
                    text=confirming_msg,
                    parse_mode="HTML"
                )
            except Exception as confirming_error:
                log_warning(
                    f"Could not send deposit confirmation message for deal "
                    f"{deal_id}: {confirming_error}"
                )

            confirmations = initial_confirmations
            confirmed = base_network == "SOL" or confirmations >= CONFIRMATION_TARGET
            while not confirmed:
                if deal_id not in active_monitors or deal_id not in deals:
                    return

                await asyncio.sleep(confirmation_check_interval)

                if deal_id not in active_monitors or deal_id not in deals:
                    return

                latest_block = await get_evm_block_number(base_network)
                if latest_block is None or detected_tx_block is None:
                    continue

                new_confirmations = max(
                    1, latest_block - detected_tx_block + 1
                )
                if new_confirmations != confirmations and sent_confirming:
                    confirmations = new_confirmations
                    updated_confirming_msg = build_deposit_confirmation_message(
                        deal_id,
                        latest_amount,
                        currency,
                        f"{confirmations}/{CONFIRMATION_TARGET}"
                    )
                    try:
                        await bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=sent_confirming.message_id,
                            text=updated_confirming_msg,
                            parse_mode="HTML"
                        )
                    except Exception as edit_error:
                        if "message is not modified" not in str(edit_error).lower():
                            log_warning(
                                f"Could not update deposit confirmations for deal "
                                f"{deal_id}: {edit_error}"
                            )
                elif new_confirmations != confirmations:
                    confirmations = new_confirmations

                if confirmations >= CONFIRMATION_TARGET:
                    confirmed = True

            if deal_id not in active_monitors or deal_id not in deals:
                return

            try:
                detected_msg = build_payment_detected_message(
                    deal_id,
                    latest_amount,
                    total_received,
                    deal_amount,
                    currency,
                    f"{confirmations}/{CONFIRMATION_TARGET}"
                )
                await bot.send_message(
                    chat_id=chat_id,
                    text=detected_msg,
                    parse_mode="HTML"
                )
            except Exception as detected_error:
                log_warning(
                    f"Could not send payment detected message for deal "
                    f"{deal_id}: {detected_error}"
                )

            if sent_confirming:
                try:
                    await bot.delete_message(
                        chat_id=chat_id,
                        message_id=sent_confirming.message_id
                    )
                except Exception as delete_error:
                    log_warning(
                        f"Could not delete deposit confirmation message for deal "
                        f"{deal_id}: {delete_error}"
                    )

            if deal_id not in active_monitors or deal_id not in deals:
                return

            deal = deals[deal_id]
            try:
                deal['status'] = 'payment_received'
                save_deals()
            except Exception as status_error:
                log_warning(f"Could not save payment status for deal {deal_id}: {status_error}")

            await finalize_payment_received(
                bot, deal, deal_id, chat_id, total_received
            )

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
                log_error(f"Room {room_number}: Could not resolve migrated channel_id")
                return None, room_number, None
        except Exception as migrate_error:
            log_warning(f"Room {room_number}: Migration error - {migrate_error}")
            return None, room_number, None

        try:
            await userbot_client(EditChatAboutRequest(
                peer=channel_id,
                about="Join @CryptoIndiaUnited"
            ))
        except Exception as about_error:
            log_warning(f"Room {room_number}: Could not set description - {about_error}")

        try:
            from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest
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
                anonymous=True,
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
            extra_admin_rights = ChatAdminRights(
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
            extra_admin_entity = await resolve_extra_admin(userbot_client)
            if extra_admin_entity is not None:
                try:
                    await userbot_client(InviteToChannelRequest(
                        channel=channel_id,
                        users=[extra_admin_entity]
                    ))
                except Exception as invite_err:
                    log_warning(f"Room {room_number}: Could not invite extra admin - {invite_err}")
                try:
                    await userbot_client(EditAdminRequest(
                        channel=channel_id,
                        user_id=extra_admin_entity.id,
                        admin_rights=extra_admin_rights,
                        rank="Admin"
                    ))
                    log_info(f"Room {room_number}: Extra admin {extra_admin_entity.id} promoted")
                except Exception as promote_err:
                    log_warning(f"Room {room_number}: Could not promote extra admin - {promote_err}")
            else:
                log_warning(f"Room {room_number}: Could not resolve extra admin")
        except Exception as extra_admin_error:
            log_warning(f"Room {room_number}: Could not add extra admin - {extra_admin_error}")

        # Join requests are handled via invite link with request_needed=True
        # ToggleJoinRequestRequest only works on public channels, so we skip it for private chats

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


USDT_FORM_QUERY = (
    "\n\nUSDT Seller:\n"
    "USDT Buyer:\n"
    "Amount[USDT]:\n"
    "Amount[INR]:\n"
    "Payment Method:\n"
    "Time[Minute]:"
)

USDC_FORM_QUERY = (
    "\n\nUSDC Seller:\n"
    "USDC Buyer:\n"
    "Amount[USDC]:\n"
    "Amount[INR]:\n"
    "Payment Method:\n"
    "Time[Minute]:"
)


def get_form_keyboard():
    usdt_button = InlineKeyboardButton(
        "GET FORM FOR USDT DEAL",
        switch_inline_query_current_chat=USDT_FORM_QUERY,
        icon_custom_emoji_id="5413589900450625318"
    )
    usdc_button = InlineKeyboardButton(
        "GET FORM FOR USDC DEAL",
        switch_inline_query_current_chat=USDC_FORM_QUERY,
        icon_custom_emoji_id="5388945416760866233"
    )
    return InlineKeyboardMarkup([[usdt_button], [usdc_button]])


async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    query_text = query.query.strip()

    results = []
    if "USDT" in query_text.upper() or not query_text:
        usdt_form = (
            "USDT Seller:\n"
            "USDT Buyer:\n"
            "Amount[USDT]:\n"
            "Amount[INR]:\n"
            "Payment Method:\n"
            "Time[Minute]:"
        )
        results.append(
            InlineQueryResultArticle(
                id="usdt_form",
                title="USDT Deal Form",
                description="Tap to send USDT escrow form",
                input_message_content=InputTextMessageContent(usdt_form)
            )
        )
    if "USDC" in query_text.upper() or not query_text:
        usdc_form = (
            "USDC Seller:\n"
            "USDC Buyer:\n"
            "Amount[USDC]:\n"
            "Amount[INR]:\n"
            "Payment Method:\n"
            "Time[Minute]:"
        )
        results.append(
            InlineQueryResultArticle(
                id="usdc_form",
                title="USDC Deal Form",
                description="Tap to send USDC escrow form",
                input_message_content=InputTextMessageContent(usdc_form)
            )
        )

    await query.answer(results, cache_time=0)


async def handle_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    global deals, group_data

    query = update.callback_query
    data = query.data
    user = query.from_user
    user_id = user.id
    username = user.username.lower() if user.username else None

    # Handle "DEAL INFO" callback - show corrected form as popup
    if data.startswith("checkescrow_"):
        deal_id = data.replace("checkescrow_", "")
        # Check active deals first, then fall back to persistent cache
        form_text = None
        if deal_id in deals:
            form_text = deals[deal_id].get('corrected_form_text', '')
        if not form_text:
            form_text = deal_form_cache.get(deal_id, '')
        if form_text:
            await query.answer(form_text, show_alert=True)
        else:
            await query.answer("No form details available.", show_alert=True)
        return

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

    if data.startswith("network_"):
        parts = data.split("_")
        deal_id = parts[1]
        network = "_".join(parts[2:])

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
        buyer_clean = deal['buyer'].lstrip('@').lower()

        if username != seller_clean and username != buyer_clean and user_id not in CANCEL_ADMIN_IDS:
            await query.answer("Only the buyer or seller can cancel the deal!")
            return

        canceller_first_name = query.from_user.first_name or "Unknown"
        canceller_id = query.from_user.id
        canceller_link = f'<a href="tg://user?id={canceller_id}">{canceller_first_name}</a>'
        if username == seller_clean:
            canceller_role_link = f'<a href="tg://user?id={canceller_id}">Seller</a>'
            other_username = deal['buyer'].lstrip('@')
            other_role_link = f'<a href="https://t.me/{other_username}">Buyer</a>'
            other_link = f'<a href="https://t.me/{other_username}">{other_username}</a>'
        elif username == buyer_clean:
            canceller_role_link = f'<a href="tg://user?id={canceller_id}">Buyer</a>'
            other_username = deal['seller'].lstrip('@')
            other_role_link = f'<a href="https://t.me/{other_username}">Seller</a>'
            other_link = f'<a href="https://t.me/{other_username}">{other_username}</a>'
        else:
            canceller_role_link = f'<a href="tg://user?id={canceller_id}">Admin</a>'
            other_username = None
            other_role_link = None
            other_link = None

        if deal_id in active_monitors:
            del active_monitors[deal_id]

        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

        await record_deal_result(deal, deal_id, "cancelled", query.message.chat_id)
        del deals[deal_id]
        save_deals()

        if other_link:
            cancel_text = (
                f"<b><u>Deal</u></b> #{deal_id}\n\n"
                f"{other_link} [{other_role_link}] the deal has been "
                f"cancelled by {canceller_link} [{canceller_role_link}]."
            )
        else:
            cancel_text = (
                f"<b><u>Deal</u></b> #{deal_id}\n\n"
                f"The deal has been cancelled by {canceller_link} [{canceller_role_link}]."
            )

        # Remove buttons from original message
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        # Send cancel message as a new message
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=cancel_text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
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
        chat_id = query.message.chat_id

        deal['received_amount'] = deal_amount
        deal['admin_confirmed'] = True
        save_deals()

        try:
            await query.message.delete()
        except Exception:
            pass

        confirmations = 1
        confirming_msg = build_deposit_confirmation_message(
            deal_id,
            deal_amount,
            currency,
            f"{confirmations}/{CONFIRMATION_TARGET}"
        )
        sent_confirming = None
        try:
            sent_confirming = await context.bot.send_message(
                chat_id=chat_id,
                text=confirming_msg,
                parse_mode="HTML"
            )
        except Exception as confirming_error:
            log_warning(
                f"Could not send admin deposit confirmation message for deal "
                f"{deal_id}: {confirming_error}"
            )

        confirmation_step = max(1, CONFIRMATION_TARGET // 5)
        while confirmations < CONFIRMATION_TARGET:
            if deal_id not in deals:
                return

            await asyncio.sleep(1)

            if deal_id not in deals:
                return

            confirmations = min(
                CONFIRMATION_TARGET, confirmations + confirmation_step
            )
            updated_confirming_msg = build_deposit_confirmation_message(
                deal_id,
                deal_amount,
                currency,
                f"{confirmations}/{CONFIRMATION_TARGET}"
            )
            if sent_confirming:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=sent_confirming.message_id,
                        text=updated_confirming_msg,
                        parse_mode="HTML"
                    )
                except Exception as edit_error:
                    if "message is not modified" not in str(edit_error).lower():
                        log_warning(
                            f"Could not update admin deposit confirmations for deal "
                            f"{deal_id}: {edit_error}"
                        )

        if deal_id not in deals:
            return

        try:
            detected_msg = build_payment_detected_message(
                deal_id,
                deal_amount,
                deal_amount,
                str(deal_amount),
                currency,
                f"{confirmations}/{CONFIRMATION_TARGET}"
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=detected_msg,
                parse_mode="HTML"
            )
        except Exception as detected_error:
            log_warning(
                f"Could not send admin payment detected message for deal "
                f"{deal_id}: {detected_error}"
            )

        if sent_confirming:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=sent_confirming.message_id
                )
            except Exception as delete_error:
                log_warning(
                    f"Could not delete admin deposit confirmation message for deal "
                    f"{deal_id}: {delete_error}"
                )

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        try:
            deal['status'] = 'payment_received'
            save_deals()
        except Exception as status_error:
            log_warning(f"Could not save payment status for deal {deal_id}: {status_error}")

        await finalize_payment_received(
            context.bot, deal, deal_id, chat_id, deal_amount
        )
        return

    if data.startswith("admincancel_"):
        parts = data.split("_")
        deal_id = parts[1]

        user_id = query.from_user.id
        if user_id not in CANCEL_ADMIN_IDS:
            await query.answer("Only admins can cancel!")
            return

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

        await record_deal_result(deal, deal_id, "cancelled", query.message.chat_id)
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

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()
        buyer_clean = deal['buyer'].lstrip('@').lower()

        if username != seller_clean and username != buyer_clean and user_id not in CANCEL_ADMIN_IDS:
            await query.answer("Only the buyer or seller can cancel the deal!")
            return

        canceller_first_name = query.from_user.first_name or "Unknown"
        canceller_id = query.from_user.id
        canceller_link = f'<a href="tg://user?id={canceller_id}">{canceller_first_name}</a>'
        if username == seller_clean:
            canceller_role_link = f'<a href="tg://user?id={canceller_id}">Seller</a>'
            other_username = deal['buyer'].lstrip('@')
            other_role_link = f'<a href="https://t.me/{other_username}">Buyer</a>'
            other_link = f'<a href="https://t.me/{other_username}">{other_username}</a>'
        elif username == buyer_clean:
            canceller_role_link = f'<a href="tg://user?id={canceller_id}">Buyer</a>'
            other_username = deal['seller'].lstrip('@')
            other_role_link = f'<a href="https://t.me/{other_username}">Seller</a>'
            other_link = f'<a href="https://t.me/{other_username}">{other_username}</a>'
        else:
            canceller_role_link = f'<a href="tg://user?id={canceller_id}">Admin</a>'
            other_username = None
            other_role_link = None
            other_link = None

        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

        await record_deal_result(deal, deal_id, "cancelled", query.message.chat_id)
        del deals[deal_id]
        save_deals()

        if other_link:
            cancel_text = (
                f"<b><u>Deal</u></b> #{deal_id}\n\n"
                f"{other_link} [{other_role_link}] the deal has been "
                f"cancelled by {canceller_link} [{canceller_role_link}]."
            )
        else:
            cancel_text = (
                f"<b><u>Deal</u></b> #{deal_id}\n\n"
                f"The deal has been cancelled by {canceller_link} [{canceller_role_link}]."
            )

        # Remove buttons from original message
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        # Send cancel message as a new message
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=cancel_text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
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
        await record_deal_result(deal, deal_id, "completed", query.message.chat_id)

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
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Deal has been cancelled.",
                parse_mode="HTML"
            )
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()
        buyer_clean = deal['buyer'].lstrip('@').lower()

        if username != seller_clean and username != buyer_clean and user_id not in CANCEL_ADMIN_IDS:
            await query.answer("Only the buyer or seller can cancel the deal!")
            return

        canceller_first_name = query.from_user.first_name or "Unknown"
        canceller_id = query.from_user.id
        canceller_link = f'<a href="tg://user?id={canceller_id}">{canceller_first_name}</a>'
        if username == seller_clean:
            canceller_role_link = f'<a href="tg://user?id={canceller_id}">Seller</a>'
            other_username = deal['buyer'].lstrip('@')
            other_role_link = f'<a href="https://t.me/{other_username}">Buyer</a>'
            other_link = f'<a href="https://t.me/{other_username}">{other_username}</a>'
        elif username == buyer_clean:
            canceller_role_link = f'<a href="tg://user?id={canceller_id}">Buyer</a>'
            other_username = deal['seller'].lstrip('@')
            other_role_link = f'<a href="https://t.me/{other_username}">Seller</a>'
            other_link = f'<a href="https://t.me/{other_username}">{other_username}</a>'
        else:
            canceller_role_link = f'<a href="tg://user?id={canceller_id}">Admin</a>'
            other_username = None
            other_role_link = None
            other_link = None

        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

        await record_deal_result(deal, deal_id, "cancelled", query.message.chat_id)
        del deals[deal_id]
        save_deals()

        if other_link:
            cancel_text = (
                f"<b><u>Deal</u></b> #{deal_id}\n\n"
                f"{other_link} [{other_role_link}] the deal has been "
                f"cancelled by {canceller_link} [{canceller_role_link}]."
            )
        else:
            cancel_text = (
                f"<b><u>Deal</u></b> #{deal_id}\n\n"
                f"The deal has been cancelled by {canceller_link} [{canceller_role_link}]."
            )

        # Remove buttons from original message
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        # Send cancel message as a new message
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=cancel_text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        return

    # Handle changeaddy callbacks (admin changing escrow addresses)
    if data.startswith("chaddy_"):
        parts = data.split("_")

        # chaddy_clearall - reset all addresses to defaults
        if data == "chaddy_clearall":
            if user_id not in ADMIN_USER_IDS:
                await query.answer("Admin only!")
                return
            _apply_addresses_from_data(_DEFAULT_ADDRESSES)
            save_escrow_addresses()
            await query.edit_message_text(
                "<b>✅ All addresses reset to defaults.</b>\n\n"
                "<i>The bot is now using the default addresses.</i>",
                parse_mode="HTML"
            )
            return

        # chaddy_cancel_{user_id}
        if parts[1] == "cancel":
            target_user_id = int(parts[2])
            if user_id != target_user_id:
                await query.answer("This is not your session!")
                return
            changeaddy_sessions.pop(user_id, None)
            await query.edit_message_text("Address change cancelled.", parse_mode="HTML")
            return

        # chaddy_slot_{1|2}_{user_id}
        if parts[1] == "slot":
            slot = int(parts[2])  # 1 or 2
            target_user_id = int(parts[3])
            if user_id != target_user_id:
                await query.answer("This is not your session!")
                return
            if user_id not in changeaddy_sessions:
                await query.answer("Session expired. Use /changeaddy again.")
                return
            changeaddy_sessions[user_id]["slot"] = slot
            changeaddy_sessions[user_id]["step"] = "currency"
            keyboard = [
                [
                    InlineKeyboardButton("USDT", callback_data=f"chaddy_cur_USDT_{user_id}"),
                    InlineKeyboardButton("USDC", callback_data=f"chaddy_cur_USDC_{user_id}")
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data=f"chaddy_cancel_{user_id}")]
            ]
            await query.edit_message_text(
                f"<b>🔄 CHANGE ESCROW ADDRESS</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>Selected:</b> Address {slot}\n\n"
                f"Select currency:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # chaddy_cur_{USDT|USDC}_{user_id}
        if parts[1] == "cur":
            currency = parts[2]
            target_user_id = int(parts[3])
            if user_id != target_user_id:
                await query.answer("This is not your session!")
                return
            if user_id not in changeaddy_sessions:
                await query.answer("Session expired. Use /changeaddy again.")
                return
            session = changeaddy_sessions[user_id]
            session["currency"] = currency
            session["step"] = "network"
            slot = session["slot"]
            index = slot - 1

            # Build network buttons with current address info
            networks = ["BSC", "SOL", "POLYGON"]
            rows = []
            for net in networks:
                cur_addr, cur_qr = get_address_and_qr(currency, net, index)
                if cur_addr is None and currency == "USDC" and net == "POLYGON" and slot == 2:
                    # USDC Polygon has only 1 address
                    continue
                label = f"{currency}[{net}]"
                rows.append([InlineKeyboardButton(label, callback_data=f"chaddy_net_{net}_{user_id}")])

            rows.append([InlineKeyboardButton("❌ Cancel", callback_data=f"chaddy_cancel_{user_id}")])
            await query.edit_message_text(
                f"<b>🔄 CHANGE ESCROW ADDRESS</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>Selected:</b> Address {slot} | {currency}\n\n"
                f"Select network:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(rows)
            )
            return

        # chaddy_net_{NETWORK}_{user_id}
        if parts[1] == "net":
            network = parts[2]
            target_user_id = int(parts[3])
            if user_id != target_user_id:
                await query.answer("This is not your session!")
                return
            if user_id not in changeaddy_sessions:
                await query.answer("Session expired. Use /changeaddy again.")
                return
            session = changeaddy_sessions[user_id]
            session["network"] = network
            session["step"] = "awaiting_qr"
            slot = session["slot"]
            currency = session["currency"]
            index = slot - 1

            cur_addr, cur_qr = get_address_and_qr(currency, network, index)

            # Send current QR image with info
            import os
            qr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), cur_qr) if cur_qr else None

            msg_text = (
                f"<b>🔄 CHANGE ESCROW ADDRESS</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"<b>Changing:</b> Address {slot} | {currency} | {network}\n\n"
                f"<b>Current Address:</b>\n<code>{cur_addr}</code>\n\n"
                f"<b>Current QR:</b> <code>{cur_qr}</code>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📸 <b>Now send the new QR code image or cancel.</b>"
            )
            cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data=f"chaddy_cancel_{user_id}")]])

            try:
                if qr_path and os.path.exists(qr_path):
                    await query.message.delete()
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=open(qr_path, 'rb'),
                        caption=msg_text,
                        parse_mode="HTML",
                        reply_markup=cancel_kb
                    )
                else:
                    await query.edit_message_text(msg_text, parse_mode="HTML", reply_markup=cancel_kb)
            except Exception:
                await query.edit_message_text(msg_text, parse_mode="HTML", reply_markup=cancel_kb)
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
                elif network == 'SOL' and address_index < len(USDC_SOL_DEPOSIT_ADDRESSES):
                    new_address = USDC_SOL_DEPOSIT_ADDRESSES[address_index]
                    new_qr_image = USDC_SOL_QR_IMAGES[address_index]

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
    """Handle photo messages - for payment details QR codes and changeaddy QR uploads."""
    global deals

    message = update.message
    if not message or not message.photo:
        return

    chat_id = message.chat_id
    user = message.from_user
    user_id = user.id
    username = user.username.lower() if user.username else None

    # Handle changeaddy QR image upload
    if user_id in changeaddy_sessions and changeaddy_sessions[user_id].get("step") == "awaiting_qr":
        session = changeaddy_sessions[user_id]
        slot = session["slot"]
        currency = session["currency"]
        network = session["network"]
        index = slot - 1

        # Download the photo
        photo_file = await message.photo[-1].get_file()
        # Build filename based on currency/network/slot
        if currency == "USDT":
            if slot == 1:
                qr_filename = f"{network.lower()}_address1_qr.jpg"
            else:
                qr_filename = f"{network.lower()}_qr_2.jpg"
        else:
            if network == "POLYGON":
                qr_filename = "usdc_polygon_address1_qr.jpg"
            elif network == "SOL":
                if slot == 1:
                    qr_filename = "usdc_sol_qr_1.jpg"
                else:
                    qr_filename = "usdc_sol_address1_qr.jpg"
            else:
                if slot == 1:
                    qr_filename = f"usdc_{network.lower()}_address1_qr.jpg"
                else:
                    qr_filename = f"usdc_{network.lower()}_qr_2.jpg"

        import os
        qr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), qr_filename)
        await photo_file.download_to_drive(qr_path)

        session["new_qr_filename"] = qr_filename
        session["step"] = "awaiting_address"

        cancel_kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data=f"chaddy_cancel_{user_id}")]])
        await message.reply_text(
            f"<b>🔄 CHANGE ESCROW ADDRESS</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Changing:</b> Address {slot} | {currency} | {network}\n\n"
            f"✅ QR code saved as <code>{qr_filename}</code>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 <b>Now send the new deposit address as text, or cancel.</b>",
            parse_mode="HTML",
            reply_markup=cancel_kb
        )
        return

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
    user_id_msg = user.id
    username = user.username.lower() if user.username else None
    text = message.text.strip()

    # Handle changeaddy address text input
    if user_id_msg in changeaddy_sessions and changeaddy_sessions[user_id_msg].get("step") == "awaiting_address":
        session = changeaddy_sessions[user_id_msg]
        slot = session["slot"]
        currency = session["currency"]
        network = session["network"]
        new_qr_filename = session["new_qr_filename"]
        index = slot - 1
        new_address = text.strip()

        # Validate the address
        if not is_valid_crypto_address(new_address, network if currency == "USDT" else f"USDC_{network}"):
            await message.reply_text(
                f"❌ Invalid {currency} address for {network}! Please send a valid address.",
                parse_mode="HTML"
            )
            return

        # Get old address for confirmation
        old_addr, old_qr = get_address_and_qr(currency, network, index)

        # Update the address and QR (also saves to JSON permanently)
        set_address_and_qr(currency, network, index, new_address, new_qr_filename)

        # Clean up session
        changeaddy_sessions.pop(user_id_msg, None)

        await message.reply_text(
            f"<b>✅ ADDRESS UPDATED SUCCESSFULLY</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Slot:</b> Address {slot}\n"
            f"<b>Currency:</b> {currency}\n"
            f"<b>Network:</b> {network}\n\n"
            f"<b>Old Address:</b>\n<code>{old_addr}</code>\n\n"
            f"<b>New Address:</b>\n<code>{new_address}</code>\n\n"
            f"<b>QR Image:</b> <code>{new_qr_filename}</code>",
            parse_mode="HTML"
        )
        log_info(f"Admin {user_id_msg} changed {currency} {network} Address {slot} from {old_addr} to {new_address}")
        return

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

                network = deal.get('network', 'BSC')
                currency = deal.get('currency', 'USDT')
                if not is_valid_crypto_address(text.strip(), network):
                    await message.reply_text(
                        f"Please provide valid {currency} Address!"
                    )
                    return

                deal['buyer_address'] = text.strip()
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

                network = deal.get('network', 'BSC')
                currency = deal.get('currency', 'USDT')
                if not is_valid_crypto_address(text.strip(), network):
                    await message.reply_text(
                        f"Please provide valid {currency} Address!"
                    )
                    return

                deal['seller_address'] = text.strip()
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
        # Only process deal forms in bot-managed groups (rooms)
        if get_room_by_channel_id(chat_id) is None:
            return

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
            'fixed_address_index': fixed_address_index,
            'corrected_form_text': (
                f"{currency} Seller: {form_data['seller']}\n"
                f"{currency} Buyer: {form_data['buyer']}\n"
                f"Amount[{currency}]: {amount_crypto}\n"
                f"Amount[INR]: {form_data.get('amount_inr', '')}\n"
                f"Payment Method: {form_data.get('payment_method', '')}\n"
                f"Time[Minute]: {form_data.get('time', '')}\n"
                f"\n"
                f"Form filled by {submitter_username if submitter_username else 'unknown'}."
            )
        }
        save_deals()

        # Also store form text in persistent cache so it survives deal deletion
        deal_form_cache[deal_id] = deals[deal_id]['corrected_form_text']
        save_deal_form_cache()

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

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode="HTML",
                reply_markup=get_network_buttons(deal_id, currency)
            )
        except Exception as e:
            log_error(f"Failed to send network selection message for deal #{deal_id}: {e}")
            # Fallback: send without custom emoji buttons
            try:
                fallback_keyboard = []
                if currency == "USDC":
                    fallback_keyboard = [
                        [
                            InlineKeyboardButton("USDC[BSC]", callback_data=f"network_{deal_id}_USDC_BSC"),
                            InlineKeyboardButton("USDC[SOL]", callback_data=f"network_{deal_id}_USDC_SOL")
                        ],
                        [InlineKeyboardButton("USDC[POLYGON]", callback_data=f"network_{deal_id}_USDC_POLYGON")],
                        [InlineKeyboardButton("Cancel", callback_data=f"cancel_{deal_id}")]
                    ]
                else:
                    fallback_keyboard = [
                        [
                            InlineKeyboardButton("USDT[BSC]", callback_data=f"network_{deal_id}_BSC"),
                            InlineKeyboardButton("USDT[SOL]", callback_data=f"network_{deal_id}_SOL")
                        ],
                        [InlineKeyboardButton("USDT[POLYGON]", callback_data=f"network_{deal_id}_POLYGON")],
                        [InlineKeyboardButton("Cancel", callback_data=f"cancel_{deal_id}")]
                    ]
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(fallback_keyboard)
                )
            except Exception as e2:
                log_error(f"Fallback network message also failed for deal #{deal_id}: {e2}")


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
    keyboard = get_form_keyboard()
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
    keyboard = get_form_keyboard()
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

                    # If first user joined, send "Waiting for..." message
                    if joined_count == 1:
                        # Determine who hasn't joined yet
                        if username == mentioned_clean:
                            waiting_for = sender
                        else:
                            waiting_for = mentioned
                        try:
                            await context.bot.send_message(
                                chat_id=int(chat_id),
                                text=f"Waiting for {waiting_for} to join the group!"
                            )
                        except Exception as e:
                            log_error(f"Failed to send waiting message: {e}")

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
    
    # If first user joined, send "Waiting for..." message
    if joined_count == 1:
        if username == mentioned_clean:
            waiting_for = sender
        else:
            waiting_for = mentioned
        try:
            await context.bot.send_message(
                chat_id=int(chat_id),
                text=f"Waiting for {waiting_for} to join the group!"
            )
        except Exception as e:
            log_error(f"Failed to send waiting message: {e}")
    
    room_num = group_data[chat_id].get("room_number", "N/A")
    channel_id_str = chat_id.replace("-100", "") if chat_id.startswith("-100") else chat_id
    joined_users = group_data[chat_id]["joined_users"]
    initiator_joined = sender_clean in [u.lower() for u in joined_users]
    counterparty_joined = mentioned_clean in [u.lower() for u in joined_users]
    await update_initial_deal_log(context.bot, channel_id_str, sender, mentioned, room_num, initiator_joined, counterparty_joined)
    
    if joined_count == 2:
        await asyncio.sleep(1)
        await send_form_messages(context, chat_id, mentioned, sender)


async def forceescrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/forceescrow @username - Whitelist a user to bypass the active-deal restriction in /escrow."""
    global force_escrow_users

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Admin only
    if user_id not in ADMIN_USER_IDS:
        return

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Usage: /forceescrow @username",
            reply_to_message_id=update.message.message_id
        )
        return

    target = context.args[0].lstrip('@').lower()
    if not target:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Usage: /forceescrow @username",
            reply_to_message_id=update.message.message_id
        )
        return

    force_escrow_users[target] = {
        "added_by": user_id,
        "added_at": datetime.now().isoformat()
    }
    save_force_escrow()

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ @{target} can now create unlimited escrows without the active deal restriction.",
        reply_to_message_id=update.message.message_id
    )
    log_info(f"@{target} added to force escrow list by admin {user_id}")


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
        log_warning(f"/escrow blocked: sender {user_id} has no username")
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

    # Check if sender has an active escrow deal (force-escrow users bypass this)
    if not is_force_escrow_user(sender_username):
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

    # Check if mentioned user has an active escrow deal (force-escrow users bypass this)
    if not is_force_escrow_user(mentioned_user):
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
        # Check if mentioned user has a username (account for multiple/collectible usernames)
        if not entity_has_username(mentioned_entity):
            mentioned_has_username = False
    except Exception as e:
        log_warning(f"Could not get mentioned user ID: {e}")
        # If we can't get the entity, assume they don't have a valid username
        mentioned_has_username = False

    # Check if mentioned user has a username
    if not mentioned_has_username:
        log_warning(
            f"/escrow blocked: mentioned user {mentioned_user} "
            f"(id={mentioned_user_id}) has no detectable username"
        )
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

    status_msg = await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "<b>🔧 Setup Rooms</b>\n\n"
            "🔄 Verifying rooms <b>0</b>/20..."
        ),
        parse_mode="HTML"
    )

    bot_info = await context.bot.get_me()
    bot_username = bot_info.username
    bot_id = bot_info.id
    userbot_me = await userbot_client.get_me()
    userbot_id = userbot_me.id

    # Phase 1: Verify all rooms
    verified_count = 0
    rooms_to_recreate = []
    rooms_to_create = []
    for room_number in range(1, 21):
        room_key = str(room_number)
        expected_title = f"Crypto India Escrow Room {room_number}"

        if room_number % 5 == 1:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text=(
                        f"<b>🔧 Setup Rooms</b>\n\n"
                        f"🔍 Verifying room <b>{room_number}</b>/20..."
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass

        if room_key not in rooms:
            rooms_to_create.append(room_number)
            continue

        room_data = rooms[room_key]
        channel_id = room_data.get('channel_id')
        if not channel_id:
            rooms_to_create.append(room_number)
            continue

        needs_recreate = False
        try:
            full_channel_id = get_marked_peer_id(channel_id)
            if full_channel_id is None:
                raise ValueError("Invalid channel_id")
            entity = await userbot_client.get_entity(full_channel_id)

            group_title = getattr(entity, 'title', '') or ''
            if group_title != expected_title:
                needs_recreate = True

            if not needs_recreate:
                try:
                    from telethon.tl.functions.channels import GetParticipantsRequest
                    from telethon.tl.types import ChannelParticipantsAdmins
                    admins_result = await userbot_client(GetParticipantsRequest(
                        channel=full_channel_id,
                        filter=ChannelParticipantsAdmins(),
                        offset=0,
                        limit=100,
                        hash=0
                    ))
                    admin_ids_in_group = {u.id for u in admins_result.users}
                    # Bot, userbot and the extra admin must all be admins
                    required_admins = [bot_id, userbot_id, EXTRA_ADMIN_USER_ID]
                    missing = [rid for rid in required_admins if rid not in admin_ids_in_group]
                    if missing:
                        needs_recreate = True
                except Exception:
                    pass

            if needs_recreate:
                rooms_to_recreate.append(room_number)
            else:
                verified_count += 1
                # Make the verified room usable by /escrow: clear stale busy
                # status when no unfinished deal is tied to it.
                if room_data.get('status') != 'free' and not room_has_active_deal(channel_id):
                    room_data['status'] = 'free'
                    room_data['current_deal_id'] = None
                    room_data['sender_user'] = None
                    room_data['mentioned_user'] = None
                    save_rooms()

        except Exception:
            rooms_to_recreate.append(room_number)

    # Phase 2: Recreate/create rooms that failed verification
    created_count = 0
    recreated_count = 0
    all_to_fix = [(n, "recreate") for n in rooms_to_recreate] + [(n, "create") for n in rooms_to_create]

    if all_to_fix:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=(
                    f"<b>🔧 Setup Rooms</b>\n\n"
                    f"🔍 Verified: <b>{verified_count}</b>\n"
                    f"🔄 Fixing <b>{len(all_to_fix)}</b> room(s)..."
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass

        for room_number, action in all_to_fix:
            room_key = str(room_number)
            if action == "recreate" and room_key in rooms:
                old_cid = rooms[room_key].get('channel_id')
                if old_cid:
                    add_old_room(old_cid, f"Crypto India Escrow Room {room_number}")
                del rooms[room_key]
                save_rooms()

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
                    if action == "recreate":
                        recreated_count += 1
                    else:
                        created_count += 1
                    log_info(f"Room {room_number} {action}d")

                await asyncio.sleep(2)

            except Exception as e:
                log_error(f"Room {room_number}: {action} failed - {e}")
                continue

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text=(
                f"<b>🔧 Setup Rooms</b>\n\n"
                f"✅ <b>Complete</b>\n\n"
                f"  ↳ Verified: <b>{verified_count}</b>\n"
                f"  ↳ New: <b>{created_count}</b>\n"
                f"  ↳ Recreated: <b>{recreated_count}</b>\n"
                f"  ↳ Total: <b>{len(rooms)}</b>"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass


async def mark_active(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark an existing group as an active bot room by chat ID."""
    global userbot_client

    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        return

    # Reject if all 20 rooms are active with no gaps
    all_active = all(str(n) in rooms for n in range(1, 21))
    if all_active:
        await update.message.reply_text(
            "<b>📌 Mark Active</b>\n\n"
            "❌ All 20 rooms (1-20) are already active. No slots available.",
            parse_mode="HTML"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "<b>📌 Mark Active</b>\n\n"
            "<b>Usage:</b> <code>/markactive [chat_id]</code>\n\n"
            "<b>Example:</b> <code>/markactive -1001234567890</code>",
            parse_mode="HTML"
        )
        return

    if userbot_client is None:
        await init_userbot()

    raw_chat_id = context.args[0].strip()
    try:
        target_id = int(raw_chat_id)
    except ValueError:
        await update.message.reply_text(
            "<b>📌 Mark Active</b>\n\n"
            "❌ Invalid chat ID. Must be a number.",
            parse_mode="HTML"
        )
        return

    status_msg = await update.message.reply_text(
        "<b>📌 Mark Active</b>\n\n"
        "🔍 Fetching group info...",
        parse_mode="HTML"
    )

    try:
        entity = await userbot_client.get_entity(target_id)
    except Exception as e:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id,
                text=(
                    "<b>📌 Mark Active</b>\n\n"
                    f"❌ Could not access group: <code>{e}</code>"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    group_title = getattr(entity, 'title', '') or ''
    channel_id = entity.id

    # Extract room number from title
    room_number = None
    if 'Crypto India Escrow Room' in group_title:
        try:
            room_number = int(group_title.replace('Crypto India Escrow Room', '').strip())
        except ValueError:
            pass

    if room_number is None:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id,
                text=(
                    "<b>📌 Mark Active</b>\n\n"
                    f"❌ Group name '<b>{group_title}</b>' doesn't match "
                    f"'Crypto India Escrow Room [N]' format."
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    # Reject if room number already active
    room_key = str(room_number)
    if room_key in rooms:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id,
                text=(
                    "<b>📌 Mark Active</b>\n\n"
                    f"❌ Room {room_number} is already active. Cannot add duplicate."
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    # Check admins in the group
    admin_info = []
    bot_is_admin = False
    userbot_is_admin = False
    try:
        from telethon.tl.functions.channels import GetParticipantsRequest
        from telethon.tl.types import ChannelParticipantsAdmins
        admins_result = await userbot_client(GetParticipantsRequest(
            channel=target_id,
            filter=ChannelParticipantsAdmins(),
            offset=0,
            limit=100,
            hash=0
        ))
        admin_ids_in_group = {u.id for u in admins_result.users}
        bot_info = await context.bot.get_me()
        me = await userbot_client.get_me()
        bot_is_admin = bot_info.id in admin_ids_in_group
        userbot_is_admin = me.id in admin_ids_in_group
        for u in admins_result.users:
            name = f"{u.first_name or ''} {u.last_name or ''}".strip()
            admin_info.append(f"  ↳ {name} (<code>{u.id}</code>)")
    except Exception:
        pass

    # Generate invite link
    invite_link = None
    try:
        invite = await userbot_client(ExportChatInviteRequest(
            peer=target_id,
            expire_date=None,
            usage_limit=0,
            request_needed=True
        ))
        invite_link = invite.link
    except Exception:
        pass

    # Register the room
    rooms[room_key] = {
        "room_number": room_number,
        "channel_id": channel_id,
        "invite_link": invite_link or "",
        "status": "free",
        "current_deal_id": None,
        "sender_user": None,
        "mentioned_user": None
    }
    save_rooms()

    admins_text = "\n".join(admin_info) if admin_info else "  ↳ Could not fetch"
    bot_status = "✅" if bot_is_admin else "❌"
    userbot_status = "✅" if userbot_is_admin else "❌"

    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text=(
                f"<b>📌 Mark Active</b>\n\n"
                f"✅ <b>Room {room_number} registered</b>\n\n"
                f"  ↳ Name: <b>{group_title}</b>\n"
                f"  ↳ Channel ID: <code>{channel_id}</code>\n"
                f"  ↳ Bot admin: {bot_status}\n"
                f"  ↳ Userbot admin: {userbot_status}\n\n"
                f"<b>Admins:</b>\n{admins_text}"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass


async def mark_inactive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a room from the active pool by chat ID."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        return

    if not context.args:
        await update.message.reply_text(
            "<b>📌 Mark Inactive</b>\n\n"
            "<b>Usage:</b> <code>/markinactive [chat_id]</code>\n\n"
            "<b>Example:</b> <code>/markinactive -1001234567890</code>",
            parse_mode="HTML"
        )
        return

    raw_chat_id = context.args[0].strip()
    try:
        target_id = int(raw_chat_id)
    except ValueError:
        await update.message.reply_text(
            "<b>📌 Mark Inactive</b>\n\n"
            "❌ Invalid chat ID. Must be a number.",
            parse_mode="HTML"
        )
        return

    # Convert to channel ID format (strip -100 prefix if present)
    target_str = str(target_id)
    if target_str.startswith("-100"):
        channel_id_str = target_str[4:]
    else:
        channel_id_str = target_str

    # Find the room with this channel ID
    found_key = None
    found_room = None
    for room_key, room_data in rooms.items():
        if str(room_data.get('channel_id')) == channel_id_str:
            found_key = room_key
            found_room = room_data
            break

    if not found_key:
        await update.message.reply_text(
            "<b>📌 Mark Inactive</b>\n\n"
            f"❌ No active room found with chat ID <code>{raw_chat_id}</code>.",
            parse_mode="HTML"
        )
        return

    room_number = found_room.get('room_number', found_key)

    # Check for active deal
    has_active_deal = False
    for deal_id, deal in deals.items():
        if str(deal.get('channel_id')) == channel_id_str:
            if deal.get('status') not in ['completed', 'cancelled', 'released']:
                has_active_deal = True
                break

    if has_active_deal:
        await update.message.reply_text(
            "<b>📌 Mark Inactive</b>\n\n"
            f"❌ Room {room_number} has an active deal. Cancel it first.",
            parse_mode="HTML"
        )
        return

    # Remove from active rooms
    del rooms[found_key]
    save_rooms()

    await update.message.reply_text(
        f"<b>📌 Mark Inactive</b>\n\n"
        f"✅ Room {room_number} removed from active pool.\n\n"
        f"  ↳ Channel ID: <code>{channel_id_str}</code>\n"
        f"  ↳ Active rooms: <b>{len(rooms)}</b>",
        parse_mode="HTML"
    )
    log_info(f"Room {room_number} marked inactive by admin {user_id}")


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

    # Block cleaning if there's an active (non-completed) deal
    channel_id_str = str(chat_id).replace("-100", "") if str(chat_id).startswith("-100") else str(chat_id)
    for deal_id, deal in deals.items():
        if deal.get('channel_id') == channel_id_str or deal.get('chat_id') == chat_id:
            deal_status = deal.get('status', '')
            if deal_status not in ('completed', 'released', 'payment_released'):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"Please cancel the active deal first using /cancel or the cancel button."
                    ),
                    parse_mode="HTML",
                    reply_to_message_id=update.message.message_id
                )
                return

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

        protected_ids = protected_from_removal_ids(bot_id, userbot_id)

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

            for user in participants.users:
                if user.id not in protected_ids:
                    try:
                        # Kick the user: ban then immediately unban so they are
                        # removed from the group but not left in the banned list
                        # (they can rejoin).
                        kick_rights = ChatBannedRights(
                            until_date=None,
                            view_messages=True
                        )
                        await userbot_client(EditBannedRequest(
                            channel=chat_id,
                            participant=user.id,
                            banned_rights=kick_rights
                        ))
                        await asyncio.sleep(0.3)
                        unban_rights = ChatBannedRights(
                            until_date=None,
                            view_messages=False
                        )
                        await userbot_client(EditBannedRequest(
                            channel=chat_id,
                            participant=user.id,
                            banned_rights=unban_rights
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
    channel_id_str = (
        str(chat_id).replace("-100", "")
        if str(chat_id).startswith("-100") else str(chat_id)
    )
    deal_id = None
    deal = None
    for candidate_id, candidate_deal in deals.items():
        if (
            candidate_deal.get("chat_id") == chat_id
            or str(candidate_deal.get("channel_id")) == channel_id_str
        ):
            deal_id = candidate_id
            deal = candidate_deal
            break
    
    if full_channel_id not in group_data:
        await update.message.reply_text("No active deal found in this group.")
        return
    
    gdata = group_data[full_channel_id]
    if deal is not None:
        await record_deal_result(deal, deal_id, "completed", chat_id)
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


async def manual_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to manually mark the counterparty as joined in an escrow room.
    Usage: /manualadd <room_number>"""
    global group_data

    user_id = update.effective_user.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    text = update.message.text.strip()
    parts = text.split()
    if len(parts) < 2:
        await update.message.reply_text("Usage: /manualadd <room_number>")
        return

    room_num = parts[1]

    # Find the room and its channel_id
    if room_num not in rooms:
        await update.message.reply_text(f"Room {room_num} not found.")
        return

    room_data = rooms[room_num]
    channel_id = str(room_data.get('channel_id', ''))
    if not channel_id:
        await update.message.reply_text(f"Room {room_num} has no channel ID.")
        return

    # Build the full channel ID (with -100 prefix)
    full_channel_id = f"-100{channel_id}"

    if full_channel_id not in group_data:
        await update.message.reply_text(f"No active deal data found for Room {room_num}.")
        return

    gdata = group_data[full_channel_id]
    mentioned_user = gdata.get("mentioned_user", "")
    sender_user = gdata.get("sender_user", "")
    mentioned_clean = mentioned_user.lstrip("@").lower() if mentioned_user else ""
    sender_clean = sender_user.lstrip("@").lower() if sender_user else ""

    if "joined_users" not in gdata:
        gdata["joined_users"] = []

    joined_users = gdata["joined_users"]

    # Determine who the counterparty is (the one NOT yet joined)
    # The initiator (sender) usually joins first; counterparty is the mentioned user
    counterparty_username = None
    if mentioned_clean and mentioned_clean not in [u.lower() for u in joined_users]:
        counterparty_username = mentioned_clean
    elif sender_clean and sender_clean not in [u.lower() for u in joined_users]:
        counterparty_username = sender_clean

    if not counterparty_username:
        await update.message.reply_text(f"Both users have already joined Room {room_num}.")
        return

    # Add the counterparty to joined_users
    joined_users.append(counterparty_username)
    save_group_data()

    joined_count = len(joined_users)

    # Update the deal log with the new join status
    initiator_joined = sender_clean in [u.lower() for u in joined_users]
    counterparty_joined = mentioned_clean in [u.lower() for u in joined_users]
    await update_initial_deal_log(
        context.bot, channel_id, sender_user, mentioned_user,
        room_num, initiator_joined, counterparty_joined
    )

    await update.message.reply_text(
        f"Counterparty @{counterparty_username} manually marked as joined in Room {room_num}."
    )

    log_info(f"Admin manually added counterparty @{counterparty_username} to Room {room_num}")

    # If both users are now joined, send form messages to continue the deal
    if joined_count >= 2:
        await asyncio.sleep(1)
        await send_form_messages(context, full_channel_id, mentioned_user, sender_user)


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
    protected_ids = protected_from_removal_ids(bot_id, userbot_id)

    # Clear ALL deals and group_data so users don't get "active escrow" errors
    cleared_deals = len(deals)
    cleared_groups = len(group_data)
    deals.clear()
    group_data.clear()
    if cleared_deals > 0:
        log_info(f"All {cleared_deals} deal(s) cleared (empty command)")
    if cleared_groups > 0:
        log_info(f"All {cleared_groups} group data entries cleared (empty command)")

    for room_num, room_data in rooms.items():
        channel_id = room_data.get('channel_id')
        if not channel_id:
            continue

        full_channel_id = f"-100{channel_id}"

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
    for room_data in rooms.values():
        old_cid = room_data.get('channel_id')
        if old_cid:
            add_old_room(old_cid, f"Crypto India Escrow Room {room_data.get('room_number', '?')}")
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


async def delete_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete old escrow room groups using stored channel IDs, keeping current active rooms."""
    global userbot_client

    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        return

    if userbot_client is None:
        await init_userbot()

    if not old_rooms:
        await update.message.reply_text(
            "<b>🗑️ Delete Old Rooms</b>\n\n"
            "✅ No old rooms to delete.",
            parse_mode="HTML"
        )
        return

    total = len(old_rooms)
    status_msg = await update.message.reply_text(
        f"<b>🗑️ Delete Old Rooms</b>\n\n"
        f"🔄 Deleting <b>0</b>/{total}...",
        parse_mode="HTML"
    )

    deleted_count = 0
    failed_count = 0
    from telethon.tl.functions.channels import DeleteChannelRequest
    for i, entry in enumerate(list(old_rooms), 1):
        cid = entry["channel_id"]
        title = entry.get("title", f"ID:{cid}")

        if i % 5 == 1 and i > 1:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_msg.message_id,
                    text=(
                        f"<b>🗑️ Delete Old Rooms</b>\n\n"
                        f"🔄 Deleting <b>{i}</b>/{total}..."
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass

        try:
            await userbot_client(DeleteChannelRequest(channel=int(f"-100{cid}")))
            deleted_count += 1
            log_info(f"Deleted old group: {title} (ID: {cid})")
        except Exception as e:
            log_warning(f"Could not delete '{title}' (ID: {cid}) - {e}")
            failed_count += 1

        await asyncio.sleep(1)

    old_rooms.clear()
    save_old_rooms()

    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text=(
                f"<b>🗑️ Delete Old Rooms</b>\n\n"
                f"✅ <b>Complete</b>\n\n"
                f"  ↳ Deleted: <b>{deleted_count}</b>\n"
                f"  ↳ Failed: <b>{failed_count}</b>\n"
                f"  ↳ Active (kept): <b>{len(rooms)}</b>"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass


async def create_new_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create 20 new escrow rooms. Clears existing rooms and creates fresh ones."""
    global userbot_client, rooms

    user_id = update.effective_user.id

    # Silently ignore non-admin users
    if user_id not in ADMIN_USER_IDS:
        return

    if userbot_client is None:
        await init_userbot()

    status_msg = await update.message.reply_text(
        "<b>🏗️ New Rooms</b>\n\n"
        "🔄 Creating room <b>0</b>/20...",
        parse_mode="HTML"
    )

    # Store current room channel IDs as old rooms before clearing
    for room_data in rooms.values():
        old_cid = room_data.get('channel_id')
        if old_cid:
            add_old_room(old_cid, f"Crypto India Escrow Room {room_data.get('room_number', '?')}")
    rooms.clear()
    save_rooms()
    log_info("Cleared all existing room data")

    bot_info = await context.bot.get_me()
    bot_username = bot_info.username

    created_count = 0
    failed_count = 0

    for room_number in range(1, 21):
        # Update progress every 5 rooms
        if room_number % 5 == 1:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_msg.message_id,
                    text=(
                        f"<b>🏗️ New Rooms</b>\n\n"
                        f"🔄 Creating room <b>{room_number}</b>/20..."
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass

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

    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text=(
                f"<b>🏗️ New Rooms</b>\n\n"
                f"✅ <b>Complete</b>\n\n"
                f"  ↳ Created: <b>{created_count}</b>\n"
                f"  ↳ Failed: <b>{failed_count}</b>\n"
                f"  ↳ Total: <b>{len(rooms)}</b>"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass


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


def get_address_and_qr(currency, network, index):
    """Get current address and QR filename for a given currency/network/index."""
    if currency == "USDT":
        if network == "BSC":
            return BSC_DEPOSIT_ADDRESSES[index], BSC_QR_IMAGES[index]
        elif network == "POLYGON":
            return POLYGON_DEPOSIT_ADDRESSES[index], POLYGON_QR_IMAGES[index]
        elif network == "SOL":
            return SOL_DEPOSIT_ADDRESSES[index], SOL_QR_IMAGES[index]
    elif currency == "USDC":
        if network == "BSC":
            return USDC_BSC_DEPOSIT_ADDRESSES[index], USDC_BSC_QR_IMAGES[index]
        elif network == "POLYGON":
            return USDC_POLYGON_DEPOSIT_ADDRESS, USDC_POLYGON_QR_IMAGE
        elif network == "SOL":
            return USDC_SOL_DEPOSIT_ADDRESSES[index], USDC_SOL_QR_IMAGES[index]
    return None, None


def set_address_and_qr(currency, network, index, new_address, new_qr_filename):
    """Update address and QR filename in the global arrays."""
    global USDC_POLYGON_DEPOSIT_ADDRESS, USDC_POLYGON_QR_IMAGE
    if currency == "USDT":
        if network == "BSC":
            BSC_DEPOSIT_ADDRESSES[index] = new_address
            BSC_QR_IMAGES[index] = new_qr_filename
        elif network == "POLYGON":
            POLYGON_DEPOSIT_ADDRESSES[index] = new_address
            POLYGON_QR_IMAGES[index] = new_qr_filename
        elif network == "SOL":
            SOL_DEPOSIT_ADDRESSES[index] = new_address
            SOL_QR_IMAGES[index] = new_qr_filename
    elif currency == "USDC":
        if network == "BSC":
            USDC_BSC_DEPOSIT_ADDRESSES[index] = new_address
            USDC_BSC_QR_IMAGES[index] = new_qr_filename
        elif network == "POLYGON":
            USDC_POLYGON_DEPOSIT_ADDRESS = new_address
            USDC_POLYGON_QR_IMAGE = new_qr_filename
        elif network == "SOL":
            USDC_SOL_DEPOSIT_ADDRESSES[index] = new_address
            USDC_SOL_QR_IMAGES[index] = new_qr_filename
    # Update the DEPOSIT_ADDRESSES dict for index 0
    if index == 0:
        if currency == "USDT":
            key = network
        else:
            key = f"USDC_{network}"
        if key == "USDC_POLYGON":
            DEPOSIT_ADDRESSES[key] = USDC_POLYGON_DEPOSIT_ADDRESS
        else:
            DEPOSIT_ADDRESSES[key] = new_address
    # Save to JSON permanently
    save_escrow_addresses()


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/cancel - Cancel the active deal in the current group."""
    if update.effective_chat.type == "private":
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    user_id = user.id
    username = user.username.lower() if user.username else None
    first_name = user.first_name or "Unknown"

    # Find active deal in this chat
    active_deal_id = None
    for deal_id, deal in deals.items():
        if deal.get('chat_id') == chat_id:
            active_deal_id = deal_id
            break

    if not active_deal_id:
        await context.bot.send_message(
            chat_id=chat_id,
            text="No active deal in this group.",
            reply_to_message_id=update.message.message_id
        )
        return

    deal = deals[active_deal_id]
    seller_clean = deal['seller'].lstrip('@').lower()
    buyer_clean = deal['buyer'].lstrip('@').lower()

    if username != seller_clean and username != buyer_clean and user_id not in CANCEL_ADMIN_IDS:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Only the buyer or seller can cancel the deal!",
            reply_to_message_id=update.message.message_id
        )
        return

    canceller_link = f'<a href="tg://user?id={user_id}">{first_name}</a>'
    if username == seller_clean:
        canceller_role_link = f'<a href="tg://user?id={user_id}">Seller</a>'
        other_username = deal['buyer'].lstrip('@')
        other_role_link = f'<a href="https://t.me/{other_username}">Buyer</a>'
        other_link = f'<a href="https://t.me/{other_username}">{other_username}</a>'
    elif username == buyer_clean:
        canceller_role_link = f'<a href="tg://user?id={user_id}">Buyer</a>'
        other_username = deal['seller'].lstrip('@')
        other_role_link = f'<a href="https://t.me/{other_username}">Seller</a>'
        other_link = f'<a href="https://t.me/{other_username}">{other_username}</a>'
    else:
        canceller_role_link = f'<a href="tg://user?id={user_id}">Admin</a>'
        other_username = None
        other_role_link = None
        other_link = None

    if active_deal_id in active_monitors:
        del active_monitors[active_deal_id]

    room_num = get_room_by_channel_id(chat_id)
    if room_num:
        mark_room_free(room_num)

    await record_deal_result(deal, active_deal_id, "cancelled", chat_id)
    del deals[active_deal_id]
    save_deals()

    if other_link:
        cancel_text = (
            f"<b><u>Deal</u></b> #{active_deal_id}\n\n"
            f"{other_link} [{other_role_link}] the deal has been "
            f"cancelled by {canceller_link} [{canceller_role_link}]."
        )
    else:
        cancel_text = (
            f"<b><u>Deal</u></b> #{active_deal_id}\n\n"
            f"The deal has been cancelled by {canceller_link} [{canceller_role_link}]."
        )

    await context.bot.send_message(
        chat_id=chat_id,
        text=cancel_text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )


async def changeaddy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/changeaddy - Admin command to change escrow deposit addresses."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        return

    chat_id = update.effective_chat.id
    changeaddy_sessions[user_id] = {"chat_id": chat_id, "step": "slot"}

    keyboard = [
        [
            InlineKeyboardButton("📍 Address 1", callback_data=f"chaddy_slot_1_{user_id}"),
            InlineKeyboardButton("📍 Address 2", callback_data=f"chaddy_slot_2_{user_id}")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"chaddy_cancel_{user_id}")]
    ]
    await update.message.reply_text(
        "<b>🔄 CHANGE ESCROW ADDRESS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Which address slot do you want to change?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
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
            "<b>Example:</b> <code>.setaddy #D36432</code>",
            parse_mode="HTML"
        )
        return

    deal_id = parts[1].split()[0].strip("#").upper()
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


async def wallets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all current escrow wallet addresses (admin only)."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_USER_IDS:
        return

    msg = (
        "<b>💰 ESCROW WALLETS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>🔸 USDT [BSC]</b>\n"
        f"  ↳ A1: <code>{BSC_DEPOSIT_ADDRESSES[0]}</code>\n"
        f"  ↳ A2: <code>{BSC_DEPOSIT_ADDRESSES[1]}</code>\n\n"
        "<b>🔸 USDT [Polygon]</b>\n"
        f"  ↳ A1: <code>{POLYGON_DEPOSIT_ADDRESSES[0]}</code>\n"
        f"  ↳ A2: <code>{POLYGON_DEPOSIT_ADDRESSES[1]}</code>\n\n"
        "<b>🔸 USDT [Solana]</b>\n"
        f"  ↳ A1: <code>{SOL_DEPOSIT_ADDRESSES[0]}</code>\n"
        f"  ↳ A2: <code>{SOL_DEPOSIT_ADDRESSES[1]}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>🔹 USDC [BSC]</b>\n"
        f"  ↳ A1: <code>{USDC_BSC_DEPOSIT_ADDRESSES[0]}</code>\n"
        f"  ↳ A2: <code>{USDC_BSC_DEPOSIT_ADDRESSES[1]}</code>\n\n"
        "<b>🔹 USDC [Polygon]</b>\n"
        f"  ↳ A1: <code>{USDC_POLYGON_DEPOSIT_ADDRESS}</code>\n\n"
        "<b>🔹 USDC [Solana]</b>\n"
        f"  ↳ A1: <code>{USDC_SOL_DEPOSIT_ADDRESSES[0]}</code>\n"
        f"  ↳ A2: <code>{USDC_SOL_DEPOSIT_ADDRESSES[1]}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Use /changeaddy to update</i>"
    )

    await update.message.reply_text(msg, parse_mode="HTML")


async def add_work_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a chat to the working list."""
    if update.effective_user.id != WORKLIST_ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: /addchat <chat_id>\n"
            "Only numeric chat IDs are supported."
        )
        return

    raw_chat_id = context.args[0].strip()
    if raw_chat_id.startswith("@"):
        await update.message.reply_text(
            "Usernames are not supported. Please provide a numeric chat ID."
        )
        return
    chat_id = parse_work_chat_id(raw_chat_id)
    if chat_id is None:
        await update.message.reply_text(
            "Invalid chat ID. Please provide a numeric ID, such as "
            "<code>-1001234567890</code>.",
            parse_mode="HTML"
        )
        return
    if is_work_chat(chat_id):
        await update.message.reply_text(
            f"Chat <code>{chat_id}</code> is already in the worklist.",
            parse_mode="HTML"
        )
        return

    work_chats.append(chat_id)
    save_work_chats()
    await update.message.reply_text(
        f"✅ Added chat <code>{chat_id}</code> to the worklist.",
        parse_mode="HTML"
    )


async def remove_work_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a chat from the working list."""
    if update.effective_user.id != WORKLIST_ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: /removechat <chat_id>\n"
            "Only numeric chat IDs are supported."
        )
        return

    raw_chat_id = context.args[0].strip()
    if raw_chat_id.startswith("@"):
        await update.message.reply_text(
            "Usernames are not supported. Please provide a numeric chat ID."
        )
        return
    chat_id = parse_work_chat_id(raw_chat_id)
    if chat_id is None:
        await update.message.reply_text(
            "Invalid chat ID. Please provide a numeric ID, such as "
            "<code>-1001234567890</code>.",
            parse_mode="HTML"
        )
        return
    if not is_work_chat(chat_id):
        await update.message.reply_text(
            f"Chat <code>{chat_id}</code> is not in the worklist.",
            parse_mode="HTML"
        )
        return

    marked_chat_id = get_marked_peer_id(chat_id)
    for stored_chat_id in work_chats:
        if stored_chat_id == chat_id or (
            marked_chat_id is not None
            and get_marked_peer_id(stored_chat_id) == marked_chat_id
        ):
            work_chats.remove(stored_chat_id)
            break
    save_work_chats()
    await update.message.reply_text(
        f"✅ Removed chat <code>{chat_id}</code> from the worklist.",
        parse_mode="HTML"
    )


async def worklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the current working chat list."""
    if update.effective_user.id != WORKLIST_ADMIN_ID:
        return
    if not work_chats:
        await update.message.reply_text(
            "<b>WORKLIST</b>\n\nNo chats added.",
            parse_mode="HTML"
        )
        return

    chat_lines = "\n".join(
        f"• <code>{chat_id}</code>" for chat_id in work_chats
    )
    await update.message.reply_text(
        f"<b>WORKLIST</b>\n\n{chat_lines}",
        parse_mode="HTML"
    )


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show a user's deal statistics for the last 30 days."""
    requester = update.effective_user
    current_time = time.time()
    last_profile_time = profile_cooldowns.get(requester.id)
    if (
        last_profile_time is not None
        and current_time - last_profile_time < 60
    ):
        await update.message.reply_text(
            "Please wait for 1 minute before accessing another profile."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "Please use /profile <username>."
        )
        return

    display_username = context.args[0].lstrip("@")
    target_username = display_username.lower()
    if not re.fullmatch(r"[A-Za-z0-9_]{5,32}", display_username):
        await update.message.reply_text(
            "Invalid username. Please provide a valid username."
        )
        return

    global userbot_client
    if userbot_client is None:
        try:
            await init_userbot()
        except Exception as init_error:
            log_warning(f"Could not initialize userbot for profile: {init_error}")
    if userbot_client is None:
        await update.message.reply_text(
            "Invalid username. Please provide a valid username."
        )
        return

    try:
        target_entity = await userbot_client.get_entity(display_username)
        if not isinstance(target_entity, User):
            raise ValueError("resolved entity is not a user")
        profile_user_id = int(target_entity.id)
        if profile_user_id <= 0:
            raise ValueError("resolved user ID is invalid")
    except Exception as resolve_error:
        log_warning(
            f"Could not resolve profile user {display_username}: "
            f"{resolve_error}"
        )
        await update.message.reply_text(
            "Invalid username. Please provide a valid username."
        )
        return

    cutoff = current_time - (30 * 24 * 3600)
    profile_records = []
    successful_deals = 0
    cancelled_deals = 0
    volumes = {
        "USDT Bought": 0.0,
        "USDT Sold": 0.0,
        "USDC Bought": 0.0,
        "USDC Sold": 0.0
    }

    for record in deal_history.values():
        if not isinstance(record, dict):
            continue
        try:
            record_ts = float(record.get("ts", 0))
        except (TypeError, ValueError):
            continue
        if record_ts < cutoff:
            continue

        buyer = str(record.get("buyer", "")).lstrip("@").lower()
        seller = str(record.get("seller", "")).lstrip("@").lower()
        try:
            buyer_id = int(record.get("buyer_id"))
        except (TypeError, ValueError):
            buyer_id = None
        try:
            seller_id = int(record.get("seller_id"))
        except (TypeError, ValueError):
            seller_id = None

        buyer_matches = buyer_id == profile_user_id or (
            buyer_id is None and target_username == buyer
        )
        seller_matches = seller_id == profile_user_id or (
            seller_id is None and target_username == seller
        )
        if not buyer_matches and not seller_matches:
            continue

        profile_records.append((record_ts, record))
        status = record.get("status")
        if status == "completed":
            successful_deals += 1
            try:
                amount = float(record.get("amount", 0))
            except (TypeError, ValueError):
                amount = 0.0
            currency = str(record.get("currency", "")).upper()
            if currency in ("USDT", "USDC"):
                if buyer_matches:
                    volumes[f"{currency} Bought"] += amount
                if seller_matches:
                    volumes[f"{currency} Sold"] += amount
        elif status == "cancelled":
            cancelled_deals += 1

    total_deals = successful_deals + cancelled_deals
    if total_deals:
        success_rate = f"{successful_deals / total_deals * 100:.2f}%"
    else:
        success_rate = "0"

    def format_amount(amount):
        return "0" if amount == 0 else f"{amount:.2f}"

    if str(profile_user_id) in hidden_volume_users:
        successful_display = "[Hidden]"
        cancelled_display = "[Hidden]"
    else:
        successful_display = str(successful_deals)
        cancelled_display = str(cancelled_deals)

    profile_text = (
        f"@{display_username} ({profile_user_id if profile_user_id is not None else 'N/A'})\n\n"
        "<b>Last 30 Days Data</b>\n"
        f"Deal Success Rate: {success_rate}\n"
        f"Successful Deals: {successful_display}\n"
        f"Cancelled Deals: {cancelled_display}\n"
        f"USDT Bought: {format_amount(volumes['USDT Bought'])}\n"
        f"USDT Sold: {format_amount(volumes['USDT Sold'])}\n"
        f"USDC Bought: {format_amount(volumes['USDC Bought'])}\n"
        f"USDC Sold: {format_amount(volumes['USDC Sold'])}"
    )
    try:
        await update.message.reply_text(profile_text, parse_mode="HTML")
    except Exception as profile_error:
        log_warning(f"Could not send profile for {display_username}: {profile_error}")
        return
    profile_cooldowns[requester.id] = time.time()


async def hide_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hide the requesting user's deal counts in profile responses."""
    user_id = str(update.effective_user.id)
    if user_id in hidden_volume_users:
        await update.message.reply_text(
            "You are already opted out  to hide trading volume."
        )
        return

    hidden_volume_users[user_id] = True
    save_hidden_volume()
    await update.message.reply_text(
        "You have opted out successfully to hide trading volume."
    )


async def show_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the requesting user's deal counts in profile responses."""
    user_id = str(update.effective_user.id)
    if user_id not in hidden_volume_users:
        await update.message.reply_text(
            "You are already opted in to show trading volume."
        )
        return

    del hidden_volume_users[user_id]
    save_hidden_volume()
    await update.message.reply_text(
        "You have opted in successfully to show trading volume."
    )


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
        "├ /profile [@username] - View 30-day deal stats\n"
        "├ /hide_volume - Hide your deal counts\n"
        "├ /show_volume - Show your deal counts\n"
        "├ /exampleform - Show deal form format\n"
        "├ /clean - Clean room after deal\n"
        "└ /set2fa [code] - Set your 2FA code\n\n"
        "<b>🔧 Admin Commands:</b>\n"
        "├ .cmd - Show this command list\n"
        "├ .rooms - View all room statuses\n"
        "├ .empty - Empty all rooms\n"
        "├ .deleteall - Clear room data\n"
        "├ .delete_rooms - Delete all Telegram groups\n"
        "├ /markactive [chat_id] - Register group as room\n"
        "├ /markinactive [chat_id] - Remove room from pool\n"
        "├ .newrooms - Create 20 new rooms\n"
        "├ .setup_rooms - Initialize room pool\n"
        "├ /changeaddy - Change escrow address\n"
        "├ .setaddy [deal_id] - Set deal address\n"
        "├ .ban @user - Ban user from bot\n"
        "├ .unban @user - Unban from bot\n"
        "├ .gunban @user - Unban from all groups\n"
        "├ .banned - List banned users\n"
        "├ .complete - Mark deal as completed\n"
        "├ .wallets - View all escrow addresses\n"
        "├ /addchat [chat_id] - Add chat to worklist\n"
        "├ /removechat [chat_id] - Remove chat from worklist\n"
        "├ /worklist - View working chat list\n"
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
                full_channel_id = get_marked_peer_id(channel_id)
                if full_channel_id is None:
                    raise ValueError("Invalid channel_id")
                await userbot_client.get_entity(full_channel_id)
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
    load_old_rooms()
    load_banned_users()
    load_user_2fa()
    load_deal_form_cache()
    load_force_escrow()
    load_work_chats()
    load_deal_history()
    load_hidden_volume()

    # Load escrow addresses from JSON (permanent storage)
    addr_data = load_escrow_addresses()
    _apply_addresses_from_data(addr_data)
    log_info(f"Escrow addresses loaded from {ESCROW_ADDRESSES_FILE}")

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

    # Add 0.25s delay to all bot API requests
    _original_do_post = app.bot._do_post
    async def _delayed_do_post(*args, **kwargs):
        await asyncio.sleep(0.25)
        return await _original_do_post(*args, **kwargs)
    app.bot._do_post = _delayed_do_post
    app.add_handler(TypeHandler(Update, whitelist_gate), group=-1)
    # General commands (slash prefix)
    app.add_handler(CommandHandler("escrow", escrow))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("hide_volume", hide_volume))
    app.add_handler(CommandHandler("show_volume", show_volume))
    app.add_handler(CommandHandler("forceescrow", forceescrow))
    app.add_handler(CommandHandler("exampleform", exampleform))
    app.add_handler(CommandHandler("clean", clean))
    app.add_handler(CommandHandler("set2fa", set_2fa))
    app.add_handler(CommandHandler("kickall", kickall))
    app.add_handler(CommandHandler("addchat", add_work_chat))
    app.add_handler(CommandHandler("removechat", remove_work_chat))
    app.add_handler(CommandHandler("worklist", worklist))
    # Admin commands (dot prefix)
    app.add_handler(MessageHandler(filters.Regex(r'^\.setup_rooms\b'), setup_rooms))
    app.add_handler(MessageHandler(filters.Regex(r'^\.rooms\b'), rooms_status))
    app.add_handler(MessageHandler(filters.Regex(r'^\.empty\b'), empty_all_rooms))
    app.add_handler(MessageHandler(filters.Regex(r'^\.deleteall\b'), delete_all_rooms))
    app.add_handler(MessageHandler(filters.Regex(r'^\.delete_rooms\b'), delete_rooms))
    app.add_handler(MessageHandler(filters.Regex(r'^\.newrooms\b'), create_new_rooms))
    app.add_handler(MessageHandler(filters.Regex(r'^\.ban\b'), ban_user))
    app.add_handler(MessageHandler(filters.Regex(r'^\.unban\b'), unban_user))
    app.add_handler(MessageHandler(filters.Regex(r'^\.gunban\b'), group_unban_user))
    app.add_handler(MessageHandler(filters.Regex(r'^\.banned\b'), list_banned))
    app.add_handler(MessageHandler(filters.Regex(r'^\.cmd\b'), cmd_list))
    app.add_handler(MessageHandler(filters.Regex(r'^\.setaddy\b'), set_address))
    app.add_handler(MessageHandler(filters.Regex(r'^\.wallets\b'), wallets_command))
    app.add_handler(MessageHandler(filters.Regex(r'^\.complete\b'), complete_deal))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("markactive", mark_active))
    app.add_handler(CommandHandler("markinactive", mark_inactive))
    app.add_handler(CommandHandler("manualadd", manual_add))
    app.add_handler(CommandHandler("changeaddy", changeaddy_command))
    app.add_handler(MessageHandler(filters.Regex(r'^\.review\b'), review_rooms))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(ChatMemberHandler(handle_chat_member_update, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(InlineQueryHandler(handle_inline_query))
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
