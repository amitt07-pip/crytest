import os
import random
import asyncio
import json
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
    ChatJoinRequestHandler, CallbackQueryHandler, MessageHandler, filters
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
from telethon.tl.types import ChatAdminRights, Channel, ChatBannedRights  # noqa: E402


API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
PHONE = os.environ.get("PHONE")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

ESCROW_ADDRESSES_LINK = "https://t.me/c/1469665894/124973/138374"
ALLOWED_USERS_FILE = "allowed_users.json"
GROUP_DATA_FILE = "group_data.json"
DEALS_FILE = "deals.json"
ROOMS_FILE = "rooms.json"
BSC_QR_IMAGES = ["bsc_deposit_qr.jpg", "bsc_qr_2.jpg"]
POLYGON_QR_IMAGES = ["polygon_deposit_qr.jpg", "polygon_qr_2.jpg"]
SOL_QR_IMAGES = ["sol_deposit_qr.jpg", "sol_qr_2.jpg"]

BSC_DEPOSIT_ADDRESSES = [
    "0xAe6313dE2fDD754734074D8a6F4835c10827115b",
    "0xf282e789e835ed379aea84ece204d2d643e6774f"
]

POLYGON_DEPOSIT_ADDRESSES = [
    "0xAe6313dE2fDD754734074D8a6F4835c10827115b",
    "0xf282e789e835ed379aea84ece204d2d643e6774f"
]

SOL_DEPOSIT_ADDRESSES = [
    "8wb1YshTFu5r3f9bzmMxKXRL9Lijphif1MUfDmEptnFy",
    "5KDFAQ6p1ofPWZBGaxWTSu2EziyX9GyQ36H547zxBou3"
]

USDC_BSC_QR_IMAGES = ["usdc_bsc_qr.jpg", "usdc_bsc_qr_2.jpg"]
USDC_BSC_DEPOSIT_ADDRESSES = [
    "0xAe6313dE2fDD754734074D8a6F4835c10827115b",
    "0xf282e789e835ed379aea84ece204d2d643e6774f"
]

USDC_POLYGON_DEPOSIT_ADDRESS = "0xAe6313dE2fDD754734074D8a6F4835c10827115b"
USDC_POLYGON_QR_IMAGE = "usdc_polygon_qr.jpg"

USDC_SOL_DEPOSIT_ADDRESS = "8wb1YshTFu5r3f9bzmMxKXRL9Lijphif1MUfDmEptnFy"
USDC_SOL_QR_IMAGE = "usdc_sol_qr.jpg"

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

ADMIN_USER_IDS = [7338429782, 8346781181, 6662820986]

BSCSCAN_API_KEY = os.environ.get("BSCSCAN_API_KEY", "")
POLYGONSCAN_API_KEY = os.environ.get("POLYGONSCAN_API_KEY", "")
HELIUS_API_KEY = os.environ.get("HELIUS_API_KEY", "")

USDT_CONTRACTS = {
    "BSC": "0x55d398326f99059fF775485246999027B3197955",
    "POLYGON": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "SOL": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
}

BLOCKCHAIN_APIS = {
    "BSC": "https://api.bscscan.com/api",
    "POLYGON": "https://api.polygonscan.com/api",
    "SOL": "https://api.solscan.io"
}

active_monitors = {}

userbot_client = None
allowed_users = {}
group_data = {}
deals = {}
rooms = {}


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
                    "USDC[BSC]", callback_data=f"network_{deal_id}_USDC_BSC"
                ),
                InlineKeyboardButton(
                    "USDC[POLYGON]", callback_data=f"network_{deal_id}_USDC_POLYGON"
                )
            ],
            [
                InlineKeyboardButton(
                    "USDC[SOL]", callback_data=f"network_{deal_id}_USDC_SOL"
                )
            ],
            [
                InlineKeyboardButton(
                    "Cancel", callback_data=f"cancel_{deal_id}"
                )
            ]
        ]
    else:
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
                "Cancel", callback_data=f"cancel_{deal_id}"
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
                "CANCEL", callback_data=f"depositcancel_{deal_id}"
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
                "Cancel", callback_data=f"admincancel_{deal_id}"
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

    if network == "BSC":
        deposit_address, qr_image = get_bsc_deposit_info()
        deal['deposit_address'] = deposit_address
        deal['qr_image'] = qr_image
    elif network == "POLYGON":
        deposit_address, qr_image = get_polygon_deposit_info()
        deal['deposit_address'] = deposit_address
        deal['qr_image'] = qr_image
    elif network == "SOL":
        deposit_address, qr_image = get_sol_deposit_info()
        deal['deposit_address'] = deposit_address
        deal['qr_image'] = qr_image
    elif network == "USDC_BSC":
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
        f"Deal [{deal_id}]\n"
        f"NOTE: {seller} [Seller] <b>DEPOSIT EXACT</b> "
        f"<b><u>{amount}</u></b> <b>{currency}</b>. "
        f"DO NOT INCLUDE NETWORK FEE, make sure the amount received is "
        f"exact!\n"
        f"<b>Example</b>: If your withdrawal fee is 0.2 {currency} then send "
        f"<b><u>{float(amount) + 0.2:.1f}</u></b>{currency} so the received "
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


async def check_bsc_transactions(deposit_address, usdt_contract):
    """Check BSC blockchain for USDT transactions to deposit address."""
    api_url = BLOCKCHAIN_APIS["BSC"]
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": usdt_contract,
        "address": deposit_address,
        "sort": "desc",
        "apikey": BSCSCAN_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "1" and data.get("result"):
                        return data["result"]
    except Exception as e:
        log_error(f"BSC API error: {e}")

    return []


async def check_polygon_transactions(deposit_address, usdt_contract):
    """Check Polygon blockchain for USDT transactions."""
    api_url = BLOCKCHAIN_APIS["POLYGON"]
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": usdt_contract,
        "address": deposit_address,
        "sort": "desc",
        "apikey": POLYGONSCAN_API_KEY
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "1" and data.get("result"):
                        return data["result"]
    except Exception as e:
        log_error(f"Polygon API error: {e}")

    return []


async def check_solana_transactions(deposit_address):
    """Check Solana blockchain for USDT transactions using Helius API."""
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


async def get_transactions_for_network(network, deposit_address):
    """Get transactions based on network type."""
    usdt_contract = USDT_CONTRACTS.get(network, "")

    if network == "BSC":
        return await check_bsc_transactions(deposit_address, usdt_contract)
    elif network == "POLYGON":
        return await check_polygon_transactions(deposit_address, usdt_contract)
    elif network == "SOL":
        return await check_solana_transactions(deposit_address)

    return []


def parse_transaction_amount(tx, network):
    """Parse transaction amount from API response."""
    if network in ["BSC", "POLYGON"]:
        value = tx.get("value", "0")
        decimals = int(tx.get("tokenDecimal", "18"))
        amount = int(value) / (10 ** decimals)
        return amount
    elif network == "SOL":
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
                "CANCEL", callback_data=f"dealcancel_{deal_id}"
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


async def monitor_blockchain(deal_id, chat_id, bot):
    """Monitor blockchain for incoming transactions."""
    global deals, active_monitors

    if deal_id not in deals:
        return

    deal = deals[deal_id]
    network = deal.get('network', 'BSC')
    deposit_address = deal.get('deposit_address', DEPOSIT_ADDRESSES.get(network, ''))
    deal_amount = deal.get('amount_crypto', '0')
    currency = deal['currency']
    start_time = asyncio.get_event_loop().time()
    check_interval = 30
    max_duration = 300

    while deal_id in active_monitors:
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > max_duration:
            break

        transactions = await get_transactions_for_network(
            network, deposit_address
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

            detected_msg = build_payment_detected_message(
                deal_id, latest_amount, total_received, deal_amount, currency
            )
            await bot.send_message(
                chat_id=chat_id,
                text=detected_msg,
                parse_mode="HTML"
            )

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
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_id,
                    caption=details_msg,
                    parse_mode="HTML"
                )
            else:
                details_msg = build_payment_details_message(deal, deal_id)
                await bot.send_message(
                    chat_id=chat_id,
                    text=details_msg,
                    parse_mode="HTML"
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

        await query.edit_message_text(
            text=new_text,
            parse_mode="HTML",
            reply_markup=get_cancel_only_button(deal_id)
        )

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
            if username != seller_clean:
                await query.answer("Only the seller can confirm!")
                return
            deal['seller_confirmed'] = True
        elif confirm_type == "buyer":
            if username != buyer_clean:
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
                await query.edit_message_text(
                    text=summary_text,
                    parse_mode="HTML"
                )
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
            network = deal.get('network', 'BSC')

            if network in ['BSC', 'POLYGON', 'SOL', 'USDC_BSC', 'USDC_POLYGON', 'USDC_SOL']:
                import os
                qr_image = deal.get('qr_image')
                qr_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    qr_image
                )
                try:
                    with open(qr_path, 'rb') as qr_file:
                        sent_deposit = await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=qr_file,
                            caption=deposit_text,
                            parse_mode="HTML",
                            reply_markup=get_deposit_buttons(deal_id)
                        )
                except FileNotFoundError:
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
                await query.message.delete()
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
                await query.edit_message_text(
                    text=summary_text,
                    parse_mode="HTML",
                    reply_markup=get_confirm_buttons(deal_id)
                )
        return

    if data.startswith("ihavepaid_"):
        parts = data.split("_")
        deal_id = parts[1]

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean:
            await query.answer("Only the seller can click this button!")
            return

        deposit_text = build_deposit_message(deal, deal_id)
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

        payment_check_msg = (
            f"<b><u>Deal</u></b> [{deal_id}]\n\n"
            f"Payment will Be checked on Blockchain for next 5 mins. "
            f"You will be notified once payment is confirmed. Thanks!"
        )

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=payment_check_msg,
            parse_mode="HTML",
            reply_markup=get_payment_check_buttons(deal_id)
        )

        deal['status'] = 'payment_checking'
        save_deals()

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
            await query.edit_message_text(
                text="Deal has been cancelled.",
                parse_mode="HTML"
            )
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean:
            await query.answer("Only the seller can cancel the deal!")
            return

        if deal_id in active_monitors:
            del active_monitors[deal_id]

        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

        del deals[deal_id]
        save_deals()

        await query.edit_message_text(
            text="Deal has been cancelled.",
            parse_mode="HTML"
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

        deal_amount = float(deal.get('amount_crypto', '0'))
        currency = deal['currency']

        deal['received_amount'] = deal_amount
        deal['admin_confirmed'] = True
        deal['status'] = 'payment_received'
        save_deals()

        await query.message.delete()

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
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=photo_id,
                caption=details_msg,
                parse_mode="HTML"
            )
        else:
            details_msg = build_payment_details_message(deal, deal_id)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=details_msg,
                parse_mode="HTML"
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

        await query.edit_message_text(
            text="Deal cancelled by admin.",
            parse_mode="HTML"
        )
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

        await query.edit_message_text(
            text="Deal cancelled by admin.",
            parse_mode="HTML"
        )
        return

    if data.startswith("release_") and not data.startswith("release_confirm_"):
        parts = data.split("_")
        deal_id = parts[1]

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean:
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
        await query.edit_message_reply_markup(reply_markup=None)

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

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=confirm_msg,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("release_confirm_"):
        parts = data.split("_")
        deal_id = parts[2]

        if deal_id not in deals:
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean:
            await query.answer("Only the seller can confirm release!")
            return

        # Remove buttons from confirmation message
        await query.edit_message_reply_markup(reply_markup=None)

        seller = deal['seller']
        buyer = deal['buyer']
        currency = deal['currency']
        amount = deal.get('amount_crypto', '0')
        escrow_fee = calculate_escrow_fee(float(amount))
        withdrawal_amount = float(amount) - escrow_fee
        buyer_address = deal.get('buyer_address', 'N/A')

        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

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
            await query.edit_message_text(
                text="Deal has been cancelled.",
                parse_mode="HTML"
            )
            return

        deal = deals[deal_id]
        seller_clean = deal['seller'].lstrip('@').lower()

        if username != seller_clean:
            await query.answer("Only the seller can cancel the deal!")
            return

        room_num = get_room_by_channel_id(query.message.chat_id)
        if room_num:
            mark_room_free(room_num)

        del deals[deal_id]
        save_deals()

        await query.edit_message_text(
            text="Deal has been cancelled.",
            parse_mode="HTML"
        )
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

            if username != seller_clean:
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

                if username != buyer_clean:
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

            if (deal.get('seller_address_msg_id') == reply_to_msg_id and
                    deal.get('chat_id') == chat_id):
                seller_clean = deal['seller'].lstrip('@').lower()

                if username != seller_clean:
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

                if username != seller_clean:
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
            reply_markup=get_network_buttons(deal_id, currency)
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

    if chat_id in allowed_users:
        allowed = allowed_users[chat_id]
        if username and username in allowed:
            await join_request.approve()
            log_info(f"Join approved: @{username}")

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
    else:
        await join_request.decline()


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

    room_num, room_data = get_free_room()

    if room_num is None:
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
        "room_number": room_num
    }
    save_group_data()

    mark_room_busy(room_num, None, sender_username, mentioned_user)

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


async def setup_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to create all 20 escrow rooms."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id not in ADMIN_USER_IDS:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Only admins can use this command."
        )
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text="🔄 Creating 20 escrow rooms... This may take a few minutes."
    )

    bot_info = await context.bot.get_me()
    bot_username = bot_info.username

    created_count = 0
    for room_number in range(1, 21):
        if str(room_number) in rooms:
            continue

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
        text=f"✅ Setup complete! Created {created_count} new rooms. "
             f"Total rooms: {len(rooms)}"
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


async def main():
    load_allowed_users()
    load_group_data()
    load_deals()
    load_rooms()

    # Log room status
    total_rooms = len(rooms)
    free_rooms = sum(1 for r in rooms.values() if r.get('status') == 'free')
    busy_rooms = total_rooms - free_rooms
    log_info(f"Rooms loaded: {total_rooms} total, {free_rooms} free, {busy_rooms} busy")

    # Log active deals
    active_deals = len(deals)
    if active_deals > 0:
        log_info(f"Active deals: {active_deals}")

    await init_userbot()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("escrow", escrow))
    app.add_handler(CommandHandler("setup_rooms", setup_rooms))
    app.add_handler(CommandHandler("exampleform", exampleform))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
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
