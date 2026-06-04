#!/usr/bin/env python3
"""
🎬 Netflix & Prime Premium Referral Bot v5.0
- Normal emojis (no premium Telegram custom emoji IDs)
- Persistent user data in SQLite (survives bot restarts)
- Mandatory channel join before using bot
- Admin can add/remove channels via admin panel
- Big animated "N" logo with random letters/numbers
- 2 Admins, Gift Codes, Dual Stock, Payout Channel
"""

import asyncio
import json
import os
import random
import string
import sqlite3
import time
import logging
from collections import defaultdict
from datetime import datetime
from typing import Tuple, List, Optional, Dict, Any

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

# ============================================================
# 🛠️ CONFIGURATION - EDIT THESE VALUES
# ============================================================
TOKEN = "8876770602:AAELuZ9iG6qzG6V3nT57wd47C6N42PjPk3g"  # ← YOUR BOT TOKEN
ADMIN_IDS = [5487009658, 8326158961]  # ← YOUR ADMIN IDs
ADMIN_USERNAMES = ["cuddleneedd", "maxxahere1"]  # ← YOUR USERNAMES
PAYOUT_CHANNEL = "@your_payout_channel"  # ← YOUR PAYOUT CHANNEL

POINTS_PER_REFERRAL = 1
POINTS_NEEDED_FOR_NETFLIX = 3
POINTS_NEEDED_FOR_PRIME = 4
DB_FILE = "premium_referral.db"

# ============================================================
# 📝 LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# 🏷️ EMOJI RENDER HELPER - NORMAL EMOJIS ONLY
# ============================================================
EMOJIS = {
    "netflix": "🎬", "prime": "🍿", "premium": "💎", "star": "⭐",
    "crown": "👑", "fire": "🔥", "gift": "🎁", "ticket": "🎟️",
    "key": "🔑", "lock": "🔐", "check": "✅", "cross": "❌",
    "warning": "⚠️", "mail": "📩", "link": "🔗", "chart": "📊",
    "trophy": "🏆", "medal1": "🥇", "medal2": "🥈", "medal3": "🥉",
    "gear": "⚙️", "people": "👥", "user": "👤", "money": "💰",
    "bank": "🏦", "support": "📞", "question": "❓", "back": "🔙",
    "forward": "➡️", "refresh": "🔄", "add": "➕", "remove": "➖",
    "admin": "🛡️", "broadcast": "📢", "stock": "📦", "code": "🔢",
    "time": "⏳", "clock": "🕐", "boom": "💥", "sparkle": "✨",
    "zap": "⚡", "heart": "💜", "folder": "📁", "clipboard": "📋",
    "payout": "💰", "channel": "📣", "join": "🔔", "unlock": "🔓",
    "target": "🎯", "point_up": "⬆️", "point_down": "⬇️",
}

def E(name: str) -> str:
    """Return a normal emoji by name."""
    return EMOJIS.get(name, "")

# ============================================================
# 👑 ADMIN HELPER
# ============================================================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ============================================================
# 🗄️ DATABASE
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        points INTEGER DEFAULT 0, referrals INTEGER DEFAULT 0,
        referrer_id INTEGER DEFAULT NULL, joined_date TEXT DEFAULT NULL,
        netflix_redeemed INTEGER DEFAULT 0, prime_redeemed INTEGER DEFAULT 0,
        joined_channels TEXT DEFAULT ''
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        type TEXT DEFAULT 'netflix', points_used INTEGER DEFAULT 3,
        status TEXT DEFAULT 'pending', created_at TEXT DEFAULT NULL,
        fulfilled_at TEXT DEFAULT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS netflix_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT, login_link TEXT NOT NULL,
        service TEXT DEFAULT 'netflix', added_by INTEGER,
        added_at TEXT DEFAULT NULL, status TEXT DEFAULT 'available',
        assigned_to INTEGER DEFAULT NULL, assigned_at TEXT DEFAULT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS prime_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT, login_link TEXT NOT NULL,
        service TEXT DEFAULT 'prime', added_by INTEGER,
        added_at TEXT DEFAULT NULL, status TEXT DEFAULT 'available',
        assigned_to INTEGER DEFAULT NULL, assigned_at TEXT DEFAULT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS gift_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE,
        points INTEGER DEFAULT 3, created_by INTEGER,
        created_at TEXT DEFAULT NULL, redeemed_by INTEGER DEFAULT NULL,
        redeemed_at TEXT DEFAULT NULL, status TEXT DEFAULT 'active'
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS payouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        type TEXT, points_used INTEGER, details TEXT,
        created_at TEXT DEFAULT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS required_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT UNIQUE,
        channel_username TEXT,
        channel_link TEXT,
        added_by INTEGER,
        added_at TEXT DEFAULT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_data (
        user_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT DEFAULT NULL,
        PRIMARY KEY (user_id, key)
    )""")
    conn.commit()
    conn.close()

# ---- Persistent User Data ----
def set_user_data(user_id: int, key: str, value: Any):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    json_value = json.dumps(value)
    c.execute("INSERT OR REPLACE INTO user_data (user_id, key, value) VALUES (?, ?, ?)",
              (user_id, key, json_value))
    conn.commit()
    conn.close()

def get_user_data(user_id: int, key: str, default: Any = None) -> Any:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM user_data WHERE user_id = ? AND key = ?", (user_id, key))
    row = c.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except:
            return row[0]
    return default

def del_user_data(user_id: int, key: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM user_data WHERE user_id = ? AND key = ?", (user_id, key))
    conn.commit()
    conn.close()

def get_user_flags(user_id: int) -> Dict[str, Any]:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, value FROM user_data WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    result = {}
    for key, value in rows:
        try:
            result[key] = json.loads(value)
        except:
            result[key] = value
    return result

# ---- Standard DB Helpers ----
def get_user(user_id: int) -> Tuple:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    u = c.fetchone()
    conn.close()
    return u

def create_user(user_id: int, username: str, first_name: str, referrer_id: int = None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id,username,first_name,points,referrals,referrer_id,joined_date,netflix_redeemed,prime_redeemed,joined_channels) VALUES (?,?,?,0,0,?,?,0,0,'')",
              (user_id, username, first_name, referrer_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def add_points(user_id: int, points: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

def deduct_points(user_id: int, points: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET points = points - ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

def increment_referrals(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def increment_netflix_redeemed(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET netflix_redeemed = netflix_redeemed + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def increment_prime_redeemed(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET prime_redeemed = prime_redeemed + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_joined_channels(user_id: int, channel_id: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT joined_channels FROM users WHERE user_id = ?", (user_id,))
    r = c.fetchone()
    channels = r[0] if r and r[0] else ''
    if channel_id not in channels:
        channels = channels + ',' + channel_id if channels else channel_id
        c.execute("UPDATE users SET joined_channels = ? WHERE user_id = ?", (channels, user_id))
    conn.commit()
    conn.close()

def create_withdrawal(user_id: int, service_type: str = 'netflix', points_used: int = 3):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO withdrawals (user_id,type,points_used,status,created_at) VALUES (?,?,?,'pending',?)",
              (user_id, service_type, points_used, datetime.now().isoformat()))
    wid = c.lastrowid
    conn.commit()
    conn.close()
    return wid

def get_pending_withdrawals(service_type: str = None) -> list:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if service_type:
        c.execute("SELECT * FROM withdrawals WHERE status='pending' AND type=? ORDER BY created_at ASC", (service_type,))
    else:
        c.execute("SELECT * FROM withdrawals WHERE status='pending' ORDER BY created_at ASC")
    w = c.fetchall()
    conn.close()
    return w

def fulfill_withdrawal(wid: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE withdrawals SET status='fulfilled',fulfilled_at=? WHERE id=?", (datetime.now().isoformat(), wid))
    conn.commit()
    conn.close()

def add_stock(login_link: str, added_by: int, service: str = 'netflix'):
    table = 'netflix_stock' if service == 'netflix' else 'prime_stock'
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"INSERT INTO {table} (login_link,service,added_by,added_at,status) VALUES (?,?,?,?,'available')",
              (login_link, service, added_by, datetime.now().isoformat()))
    sid = c.lastrowid
    conn.commit()
    conn.close()
    return sid

def get_available_stock(service: str = 'netflix'):
    table = 'netflix_stock' if service == 'netflix' else 'prime_stock'
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table} WHERE status='available' ORDER BY added_at ASC LIMIT 1")
    s = c.fetchone()
    conn.close()
    return s

def get_all_stock(service: str = 'netflix'):
    table = 'netflix_stock' if service == 'netflix' else 'prime_stock'
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table} ORDER BY added_at DESC")
    s = c.fetchall()
    conn.close()
    return s

def assign_stock(stock_id: int, user_id: int, service: str = 'netflix'):
    table = 'netflix_stock' if service == 'netflix' else 'prime_stock'
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"UPDATE {table} SET status='assigned',assigned_to=?,assigned_at=? WHERE id=? AND status='available'",
              (user_id, datetime.now().isoformat(), stock_id))
    a = c.rowcount
    conn.commit()
    conn.close()
    return a > 0

def get_stock_count(service: str = 'netflix'):
    table = 'netflix_stock' if service == 'netflix' else 'prime_stock'
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM {table} WHERE status='available'")
    avail = c.fetchone()[0]
    c.execute(f"SELECT COUNT(*) FROM {table} WHERE status='assigned'")
    assigned = c.fetchone()[0]
    c.execute(f"SELECT COUNT(*) FROM {table}")
    total = c.fetchone()[0]
    conn.close()
    return {"available": avail, "assigned": assigned, "total": total}

def generate_gift_code(points: int, created_by: int) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=12))
        code = f"{code[:4]}-{code[4:8]}-{code[8:]}"
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO gift_codes (code,points,created_by,created_at,status) VALUES (?,?,?,?,'active')",
                      (code, points, created_by, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return code
        except sqlite3.IntegrityError:
            conn.close()
            continue

def redeem_gift_code(code: str, user_id: int) -> Tuple[bool, str]:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM gift_codes WHERE code=? AND status='active'", (code,))
    gift = c.fetchone()
    if not gift:
        conn.close()
        return False, f"{E('cross')} Invalid or already redeemed code!"
    points = gift[2]
    gid = gift[0]
    c.execute("UPDATE gift_codes SET status='redeemed',redeemed_by=?,redeemed_at=? WHERE id=?",
              (user_id, datetime.now().isoformat(), gid))
    c.execute("UPDATE users SET points=points+? WHERE user_id=?", (points, user_id))
    conn.commit()
    conn.close()
    return True, f"{E('check')} **Code Redeemed!** +**{points} points** {E('star')}"

def get_all_gift_codes() -> list:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM gift_codes ORDER BY created_at DESC")
    g = c.fetchall()
    conn.close()
    return g

def log_payout(user_id: int, service_type: str, points_used: int, details: str = ""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO payouts (user_id,type,points_used,details,created_at) VALUES (?,?,?,?,?)",
              (user_id, service_type, points_used, details, datetime.now().isoformat()))
    p = c.lastrowid
    conn.commit()
    conn.close()
    return p

def get_stats() -> dict:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*),SUM(points),SUM(referrals),SUM(netflix_redeemed),SUM(prime_redeemed) FROM users")
    r = c.fetchone()
    c.execute("SELECT COUNT(*) FROM withdrawals WHERE status='pending'")
    pw = c.fetchone()[0] or 0
    nfs = get_stock_count('netflix')
    prs = get_stock_count('prime')
    c.execute("SELECT COUNT(*) FROM gift_codes WHERE status='active'")
    ac = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM gift_codes WHERE status='redeemed'")
    rc = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM required_channels")
    ch = c.fetchone()[0] or 0
    conn.close()
    return {"total_users": r[0] or 0, "total_points": r[1] or 0, "total_referrals": r[2] or 0,
            "total_netflix": r[3] or 0, "total_prime": r[4] or 0, "pending_withdrawals": pw,
            "stock_netflix_avail": nfs["available"], "stock_netflix_total": nfs["total"],
            "stock_prime_avail": prs["available"], "stock_prime_total": prs["total"],
            "active_codes": ac, "redeemed_codes": rc, "channels": ch}

def get_all_users() -> list:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY points DESC")
    u = c.fetchall()
    conn.close()
    return u

# ---- Channel Management ----
def add_required_channel(channel_id: str, channel_username: str, channel_link: str, added_by: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO required_channels (channel_id,channel_username,channel_link,added_by,added_at) VALUES (?,?,?,?,?)",
                  (channel_id, channel_username, channel_link, added_by, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True, "Channel added!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Channel already exists!"

def remove_required_channel(channel_id: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM required_channels WHERE channel_id = ?", (channel_id,))
    r = c.rowcount
    conn.commit()
    conn.close()
    return r > 0

def get_required_channels() -> list:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM required_channels")
    r = c.fetchall()
    conn.close()
    return r

# ============================================================
# ✅ CHANNEL VERIFICATION
# ============================================================
async def check_user_channels(bot, user_id: int) -> Tuple[bool, list]:
    channels = get_required_channels()
    if not channels:
        return True, []
    
    missing = []
    for ch in channels:
        ch_id = ch[1]
        ch_username = ch[2]
        try:
            if ch_id.startswith('-'):
                chat_id = int(ch_id)
            else:
                chat_id = ch_id
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in ['left', 'kicked', 'restricted']:
                missing.append(ch)
        except Exception:
            try:
                if ch_username:
                    member = await bot.get_chat_member(chat_id=f"@{ch_username}", user_id=user_id)
                    if member.status in ['left', 'kicked', 'restricted']:
                        missing.append(ch)
                else:
                    missing.append(ch)
            except Exception:
                missing.append(ch)
    
    return len(missing) == 0, missing

async def require_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if is_admin(user_id):
        return True
    
    allowed, missing = await check_user_channels(context.bot, user_id)
    if allowed:
        return True
    
    kb = []
    for ch in missing:
        ch_id = ch[1]
        ch_username = ch[2]
        ch_link = ch[3]
        btn_text = f"{E('join')} Join {ch_username or ch_id}"
        url = ch_link if ch_link else f"https://t.me/{ch_username}" if ch_username else None
        if url:
            kb.append([InlineKeyboardButton(btn_text, url=url)])
    
    kb.append([InlineKeyboardButton(f"{E('refresh')} I've Joined {E('check')}", callback_data="check_joined")])
    
    text = (
        f"{E('lock')} **Access Restricted** {E('lock')}\n\n"
        f"To use this bot, you must join our channel(s) first:\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"• Tap each channel button below\n"
        f"• Click **Join** in the channel\n"
        f"• Come back and tap **I've Joined**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{E('join')} After joining, tap the button below!"
    )
    
    markup = InlineKeyboardMarkup(kb)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)
    
    return False

# ============================================================
# 🎬 BIG "N" LOGO ANIMATION — BOLD WITH NORMAL EMOJIS
# ============================================================
def generate_big_n(char: str = None):
    """Generates a bold 'N' logo using Markdown bold markers."""
    if char is None:
        char = random.choice(string.ascii_uppercase + string.digits)
    
    n_lines = [
        f"**{char}**       **{char}**",
        f"**{char}****{char}**      **{char}**",
        f"**{char}** **{char}**     **{char}**",
        f"**{char}**  **{char}**    **{char}**",
        f"**{char}**   **{char}**   **{char}**",
        f"**{char}**    **{char}**  **{char}**",
        f"**{char}**     **{char}** **{char}**",
        f"**{char}**      **{char}****{char}**",
        f"**{char}**       **{char}**",
    ]
    
    top = f"╔═══ {E('netflix')} **NETFLIX** {E('netflix')} ═══╗"
    bottom = f"╚{'═'*25}╝"
    lines = [top]
    for line in n_lines:
        lines.append(f"║   {line}   ║")
    lines.append(bottom)
    lines.append("")
    lines.append(f"{E('time')} Initializing Premium Services...")
    return "\n".join(lines)

async def netflix_start_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    first_name = update.effective_user.first_name
    
    msg = await update.message.reply_text(
        f"╔═══ {E('netflix')} **NETFLIX** {E('netflix')} ═══╗\n\n{E('time')} Starting...",
        parse_mode="HTML"
    )
    
    chars_pool = string.ascii_uppercase + string.digits
    for i in range(12):
        rand_char = random.choice(chars_pool)
        logo = generate_big_n(rand_char)
        try:
            pct = min(100, (i + 1) * 9)
            bar = "▓" * (pct // 10) + "░" * (10 - pct // 10)
            frame = logo + f"\n`[{bar}]` {pct}%"
            await msg.edit_text(frame, parse_mode="HTML")
        except Exception:
            pass
        await asyncio.sleep(0.3)
    
    final_logo = generate_big_n("N")
    welcome = (
        f"{final_logo}\n\n"
        f"{E('sparkle')} **WELCOME, {first_name.upper()}** {E('sparkle')}\n"
        f"{E('premium')} **PREMIUM SERVICE READY** {E('premium')}"
    )
    try:
        await msg.edit_text(welcome, parse_mode="HTML")
    except Exception:
        pass
    await asyncio.sleep(1)
    return msg

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, msg=None):
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name or "User"
    
    ud = get_user(user_id)
    pts = ud[3] if ud else 0
    refs = ud[4] if ud else 0
    nf = ud[7] if ud else 0
    pr = ud[8] if ud else 0
    
    text = (
        f"{E('netflix')}{E('prime')} **PREMIUM BOT** {E('premium')}\n\n"
        f"{E('user')} **{first_name}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{E('star')} `{pts}` | {E('people')} `{refs}` | {E('netflix')}`{nf}` | {E('prime')}`{pr}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{E('netflix')} 3pts | {E('prime')} 4pts | {E('link')} 1pt/ref"
    )
    
    kb = [
        [InlineKeyboardButton(f"{E('user')} Profile", callback_data="profile"),
         InlineKeyboardButton(f"{E('link')} Referral", callback_data="referral")],
        [InlineKeyboardButton(f"{E('netflix')} Netflix (3pts)", callback_data="redeem_netflix"),
         InlineKeyboardButton(f"{E('prime')} Prime (4pts)", callback_data="redeem_prime")],
        [InlineKeyboardButton(f"{E('trophy')} Leaderboard", callback_data="leaderboard"),
         InlineKeyboardButton(f"{E('key')} Redeem Code", callback_data="redeem_code")],
        [InlineKeyboardButton(f"{E('support')} Support", callback_data="support"),
         InlineKeyboardButton(f"{E('question')} Help", callback_data="help")],
    ]
    if is_admin(user_id):
        kb.append([InlineKeyboardButton(f"{E('admin')} Admin Panel", callback_data="admin_panel")])
    
    markup = InlineKeyboardMarkup(kb)
    
    if msg:
        await msg.edit_text(text, parse_mode="HTML", reply_markup=markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)

# ============================================================
# 🏠 START COMMAND
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or ""
    first_name = user.first_name or "User"

    allowed, _ = await check_user_channels(context.bot, user_id)
    if not allowed and not is_admin(user_id):
        await require_channels(update, context)
        return

    referrer_id = None
    if context.args and len(context.args) > 0:
        try:
            ref_arg = context.args[0]
            if ref_arg.startswith("ref_"):
                referrer_id = int(ref_arg.replace("ref_", ""))
                if referrer_id == user_id:
                    referrer_id = None
        except:
            pass

    existing = get_user(user_id)
    if not existing:
        create_user(user_id, username, first_name, referrer_id)
        if referrer_id:
            ref_user = get_user(referrer_id)
            if ref_user:
                add_points(referrer_id, POINTS_PER_REFERRAL)
                increment_referrals(referrer_id)
                try:
                    await context.bot.send_message(
                        referrer_id,
                        f"{E('gift')} **New Referral!** {E('gift')}\n"
                        f"**{first_name}** joined!\n"
                        f"{E('star')} +**{POINTS_PER_REFERRAL} point**\n"
                        f"Total: `{ref_user[3] + 1}`",
                        parse_mode="HTML",
                    )
                except:
                    pass

    anim_msg = await netflix_start_animation(update, context)
    await send_main_menu(update, context, msg=anim_msg)

# ============================================================
# ✅ CHECK JOINED CALLBACK
# ============================================================
async def handle_check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.callback_query
    
    allowed, missing = await check_user_channels(context.bot, user_id)
    
    if allowed:
        await query.answer(f"{E('check')} Verified! Welcome! 🎉", show_alert=True)
        await send_main_menu(update, context)
    else:
        await query.answer(f"{E('cross')} You haven't joined all channels yet!", show_alert=True)
        await require_channels(update, context)

# ============================================================
# 📣 PAYOUT CHANNEL NOTIFICATION
# ============================================================
async def send_payout_notification(context: ContextTypes.DEFAULT_TYPE, user_data: tuple, service_type: str, points_used: int, details: str = ""):
    if not PAYOUT_CHANNEL:
        return
    uid, uname, fname = user_data[0], user_data[1] or "N/A", user_data[2] or "User"
    icon = E('netflix') if service_type == 'netflix' else E('prime')
    sname = "Netflix" if service_type == 'netflix' else "Prime Video"
    text = (
        f"{E('payout')} **New Payout** {E('boom')}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"{E('user')} {fname} (@{uname}) `{uid}`\n"
        f"{icon} **{sname}** | {E('star')}`{points_used}` pts\n"
        f"{E('clock')} {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"━━━━━━━━━━━━━━━━━\n"
    )
    if details:
        text += f"\n{E('mail')} `{details}`\n"
    text += f"\n{E('check')} Auto-processed {E('check')}"
    try:
        await context.bot.send_message(chat_id=PAYOUT_CHANNEL, text=text, parse_mode="HTML")
    except Exception as e:
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(aid, f"{E('warning')} Payout channel error: `{e}`\nCheck `{PAYOUT_CHANNEL}`", parse_mode="HTML")
            except:
                pass

# ============================================================
# 🔄 CALLBACK HANDLER
# ============================================================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = user.id
    data = query.data

    if data != "check_joined":
        allowed, _ = await check_user_channels(context.bot, user_id)
        if not allowed and not is_admin(user_id):
            await require_channels(update, context)
            return

    if data == "check_joined":
        await handle_check_joined(update, context)
        return

    if data == "profile":
        ud = get_user(user_id)
        if not ud:
            await query.edit_message_text(f"{E('cross')} Use /start first.")
            return
        pts, refs, jn, nf, pr = ud[3], ud[4], ud[6], ud[7], ud[8]
        bn = "▓"*min(pts,3) + "░"*max(0,3-min(pts,3))
        bp = "▓"*min(pts,4) + "░"*max(0,4-min(pts,4))
        text = (
            f"{E('user')} **Profile** {E('premium')}\n"
            f"🆔 `{user_id}` | **{ud[2]}**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{E('star')} Points: `{pts}`\n"
            f"{E('people')} Referrals: `{refs}`\n"
            f"{E('netflix')} Netflix: `{nf}` | {E('prime')} Prime: `{pr}`\n"
            f"{E('clock')} Joined: `{jn[:10] if jn else 'N/A'}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{E('netflix')} {bn} `{min(pts,3)}/3`\n"
            f"{E('prime')} {bp} `{min(pts,4)}/4`"
        )
        kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "referral":
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        text = f"{E('link')} **Your Referral Link**\n\n`{link}`\n\n1️⃣ Share → 2️⃣ Friend joins → 3️⃣ {E('star')}**+1 pt**"
        kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "redeem_netflix":
        sv, need = 'netflix', POINTS_NEEDED_FOR_NETFLIX
        ud = get_user(user_id)
        if not ud:
            await query.edit_message_text(f"{E('cross')} Use /start first.")
            return
        pts = ud[3]
        if pts >= need:
            st = get_available_stock(sv)
            if not st:
                text = f"{E('netflix')} **Netflix**\n{E('star')}`{pts}` pts | {E('warning')} **Out of Stock!**"
                kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]
            else:
                text = f"{E('netflix')} **Netflix**\n{E('star')}`{pts}` pts | Cost: `{need}` | {E('stock')}**In Stock**\n\n**Redeem now?**"
                kb = [[InlineKeyboardButton(f"{E('check')} Confirm", callback_data="confirm_redeem_netflix")],
                      [InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]
        else:
            text = f"{E('netflix')} **Netflix**\n{E('star')}`{pts}/{need}` | Need `{need-pts}` more pts"
            kb = [[InlineKeyboardButton(f"{E('link')} Referral", callback_data="referral"),
                   InlineKeyboardButton(f"{E('key')} Code", callback_data="redeem_code")],
                  [InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "redeem_prime":
        sv, need = 'prime', POINTS_NEEDED_FOR_PRIME
        ud = get_user(user_id)
        if not ud:
            await query.edit_message_text(f"{E('cross')} Use /start first.")
            return
        pts = ud[3]
        if pts >= need:
            st = get_available_stock(sv)
            if not st:
                text = f"{E('prime')} **Prime Video**\n{E('star')}`{pts}` pts | {E('warning')} **Out of Stock!**"
                kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]
            else:
                text = f"{E('prime')} **Prime Video**\n{E('star')}`{pts}` pts | Cost: `{need}` | {E('stock')}**In Stock**\n\n**Redeem now?**"
                kb = [[InlineKeyboardButton(f"{E('check')} Confirm", callback_data="confirm_redeem_prime")],
                      [InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]
        else:
            text = f"{E('prime')} **Prime Video**\n{E('star')}`{pts}/{need}` | Need `{need-pts}` more pts"
            kb = [[InlineKeyboardButton(f"{E('link')} Referral", callback_data="referral"),
                   InlineKeyboardButton(f"{E('key')} Code", callback_data="redeem_code")],
                  [InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data in ["confirm_redeem_netflix", "confirm_redeem_prime"]:
        sv = 'netflix' if 'netflix' in data else 'prime'
        need = POINTS_NEEDED_FOR_NETFLIX if sv == 'netflix' else POINTS_NEEDED_FOR_PRIME
        icon = E('netflix') if sv == 'netflix' else E('prime')
        sname = "Netflix" if sv == 'netflix' else "Prime Video"
        
        ud = get_user(user_id)
        if not ud or ud[3] < need:
            await query.edit_message_text(f"{E('cross')} Not enough points!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]))
            return
        
        st = get_available_stock(sv)
        if not st:
            await query.edit_message_text(f"{E('warning')} **Out of Stock!**",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]))
            return
        
        deduct_points(user_id, need)
        if sv == 'netflix':
            increment_netflix_redeemed(user_id)
        else:
            increment_prime_redeemed(user_id)
        
        sid, link = st[0], st[1]
        assign_stock(sid, user_id, sv)
        wid = create_withdrawal(user_id, sv, need)
        log_payout(user_id, sv, need, link)
        
        text = (
            f"{icon} **{sname} Delivered!** {E('premium')}\n\n"
            f"{E('check')} Request `#{wid}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{E('key')} **Login:**\n"
            f"`{link}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{E('lock')} Change password!\n"
            f"{E('heart')} Enjoy!"
        )
        kb = [[InlineKeyboardButton(f"{E('back')} Menu", callback_data="back_home")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        
        await send_payout_notification(context, ud, sv, need, link)
        for aid in ADMIN_IDS:
            try:
                await context.bot.send_message(aid,
                    f"{icon} **{sname} Auto-Redeemed** {E('check')}\n"
                    f"{E('user')} {user.first_name} (@{user.username or 'N/A'}) `{user_id}`\n"
                    f"{E('stock')} Stock ID: `{sid}`",
                    parse_mode="HTML")
            except:
                pass

    elif data == "redeem_code":
        text = f"{E('key')} **Redeem Code** {E('gift')}\n\nEnter code: `XXXX-XXXX-XXXX`"
        kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        set_user_data(user_id, "awaiting_code", True)

    elif data == "leaderboard":
        all_u = get_all_users()[:10]
        if not all_u:
            text = f"{E('trophy')} **Leaderboard**\n\nNo users yet!"
        else:
            text = f"{E('trophy')} **Top 10** {E('premium')}\n━━━━━━━━━━━━━━━━━━━━━\n"
            medals = [E('medal1'), E('medal2'), E('medal3')]
            for i, u in enumerate(all_u):
                m = medals[i] if i < 3 else f"`{i+1}.`"
                text += f"{m} **{u[2]}** {E('star')}{u[3]} {E('people')}{u[4]} {E('netflix')}{u[7]} {E('prime')}{u[8]}\n"
        kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "help":
        text = (
            f"{E('question')} **Help**\n\n"
            f"{E('forward')} **Earn:** Share referral link\n"
            f"{E('netflix')} **Netflix:** 3 pts\n"
            f"{E('prime')} **Prime:** 4 pts\n"
            f"{E('key')} **Codes:** Redeem gift codes\n"
            f"`/start` - Menu\n`/points` - Stats"
        )
        kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "support":
        am = " & ".join([f"@{a}" for a in ADMIN_USERNAMES])
        text = f"{E('support')} **Support**\n\nAdmins: {am}\n\nTap to message:"
        kb = [
            [InlineKeyboardButton(f"📩 @{ADMIN_USERNAMES[0]}", url=f"tg://user?id={ADMIN_IDS[0]}"),
             InlineKeyboardButton(f"📩 @{ADMIN_USERNAMES[1]}", url=f"tg://user?id={ADMIN_IDS[1]}")],
            [InlineKeyboardButton(f"{E('back')} Back", callback_data="back_home")],
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "back_home":
        await send_main_menu(update, context)

    elif data == "admin_panel":
        if not is_admin(user_id):
            await query.answer(f"{E('cross')} Unauthorized!", show_alert=True)
            return
        s = get_stats()
        text = (
            f"{E('admin')} **Admin Panel**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{E('people')} Users: `{s['total_users']}` | {E('star')} Points: `{s['total_points']}`\n"
            f"{E('netflix')} Netflix: `{s['stock_netflix_avail']}/{s['stock_netflix_total']}` stock\n"
            f"{E('prime')} Prime: `{s['stock_prime_avail']}/{s['stock_prime_total']}` stock\n"
            f"{E('time')} Pending: `{s['pending_withdrawals']}`\n"
            f"{E('gift')} Codes: `{s['active_codes']}` active | `{s['redeemed_codes']}` used\n"
            f"{E('channel')} Channels: `{s['channels']}` required\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{E('user')} {' & '.join(['@'+a for a in ADMIN_USERNAMES])}"
        )
        kb = [
            [InlineKeyboardButton(f"{E('netflix')} +Netflix Stock", callback_data="admin_addstock_netflix"),
             InlineKeyboardButton(f"{E('prime')} +Prime Stock", callback_data="admin_addstock_prime")],
            [InlineKeyboardButton(f"{E('gift')} Generate Code", callback_data="admin_gen_code")],
            [InlineKeyboardButton(f"{E('time')} Pending Req", callback_data="admin_pending")],
            [InlineKeyboardButton(f"{E('people')} Users", callback_data="admin_users")],
            [InlineKeyboardButton(f"{E('broadcast')} Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton(f"{E('gift')} Codes List", callback_data="admin_codes_list")],
            [InlineKeyboardButton(f"{E('stock')} Stock Lists", callback_data="admin_stock_lists")],
            [InlineKeyboardButton(f"{E('channel')} Channels", callback_data="admin_channels")],
            [InlineKeyboardButton(f"{E('payout')} Payout Channel", callback_data="admin_payout_info")],
            [InlineKeyboardButton(f"{E('back')} Menu", callback_data="back_home")],
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "admin_payout_info":
        if not is_admin(user_id):
            return
        text = f"{E('payout')} **Payout Channel**\n\nChannel: `{PAYOUT_CHANNEL}`\n\nBot must be admin in channel!"
        kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "admin_channels":
        if not is_admin(user_id):
            return
        channels = get_required_channels()
        if not channels:
            text = f"{E('channel')} **Required Channels**\n\nNo channels set yet.\n\nTo add: Use `/addchannel @username` or `/addchannel -1001234567890`"
        else:
            text = f"{E('channel')} **Required Channels ({len(channels)})**\n\n"
            for ch in channels:
                cid = ch[1]
                username = ch[2]
                link = ch[3]
                text += f"{E('join')} `{username or cid}`\n  Link: `{link or 'N/A'}`\n  ID: `{cid}`\n\n"
        kb = [
            [InlineKeyboardButton(f"{E('add')} Add Channel", callback_data="admin_add_channel")],
            [InlineKeyboardButton(f"{E('remove')} Remove Channel", callback_data="admin_remove_channel")],
            [InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")],
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "admin_add_channel":
        if not is_admin(user_id):
            return
        text = (
            f"{E('add')} **Add Required Channel**\n\n"
            f"Send the channel username or ID:\n\n"
            f"Format: `@channelusername` or `-1001234567890`\n\n"
            f"Or use command: `/addchannel @username`\n\n"
            f"{E('warning')} Bot must be admin in the channel!"
        )
        kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_channels")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        set_user_data(user_id, "awaiting_channel_add", True)

    elif data == "admin_remove_channel":
        if not is_admin(user_id):
            return
        channels = get_required_channels()
        if not channels:
            await query.edit_message_text(f"{E('cross')} No channels to remove!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_channels")]]))
            return
        text = f"{E('remove')} **Select channel to remove:**\n\n"
        kb = []
        for ch in channels:
            cid = ch[1]
            username = ch[2]
            display = username or cid
            kb.append([InlineKeyboardButton(f"{E('cross')} Remove {display}", callback_data=f"remove_ch_{cid}")])
        kb.append([InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_channels")])
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("remove_ch_"):
        if not is_admin(user_id):
            return
        ch_id = data.replace("remove_ch_", "")
        removed = remove_required_channel(ch_id)
        if removed:
            await query.answer(f"{E('check')} Channel removed!", show_alert=True)
        else:
            await query.answer(f"{E('cross')} Failed to remove!", show_alert=True)
        channels = get_required_channels()
        if not channels:
            text = f"{E('channel')} **Required Channels**\n\nNo channels set."
        else:
            text = f"{E('channel')} **Required Channels ({len(channels)})**\n\n"
            for ch in channels:
                cid = ch[1]
                username = ch[2]
                text += f"{E('join')} `{username or cid}`\n"
        kb = [
            [InlineKeyboardButton(f"{E('add')} Add Channel", callback_data="admin_add_channel")],
            [InlineKeyboardButton(f"{E('remove')} Remove Channel", callback_data="admin_remove_channel")],
            [InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")],
        ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data in ["admin_addstock_netflix", "admin_addstock_prime"]:
        sv = 'netflix' if 'netflix' in data else 'prime'
        icon = E('netflix') if sv == 'netflix' else E('prime')
        if not is_admin(user_id):
            return
        await query.edit_message_text(
            f"{icon} **Add {sv.title()} Stock**\n\nUse: `/addstock {sv}`\nThen send login link.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")]])
        )

    elif data == "admin_stock_lists":
        if not is_admin(user_id):
            return
        kb = [
            [InlineKeyboardButton(f"{E('netflix')} Netflix Stock", callback_data="admin_stock_list_netflix")],
            [InlineKeyboardButton(f"{E('prime')} Prime Stock", callback_data="admin_stock_list_prime")],
            [InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")],
        ]
        await query.edit_message_text(f"{E('stock')} **Stock Lists**", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "admin_stock_list_netflix":
        if not is_admin(user_id):
            return
        items = get_all_stock('netflix')
        if not items:
            text = f"{E('netflix')} **No Netflix stock**"
        else:
            text = f"{E('netflix')} **Netflix Stock ({len(items)})**\n\n"
            for s in items[:15]:
                sid = s[0]
                link_preview = str(s[1])[:30]
                status_text = f"{E('check')} avail" if s[5] == 'available' else f"{E('key')} → {s[6]}"
                text += f"`#{sid}` {status_text} `{link_preview}...`\n"
        kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_stock_lists")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "admin_stock_list_prime":
        if not is_admin(user_id):
            return
        items = get_all_stock('prime')
        if not items:
            text = f"{E('prime')} **No Prime stock**"
        else:
            text = f"{E('prime')} **Prime Stock ({len(items)})**\n\n"
            for s in items[:15]:
                sid = s[0]
                link_preview = str(s[1])[:30]
                status_text = f"{E('check')} avail" if s[5] == 'available' else f"{E('key')} → {s[6]}"
                text += f"`#{sid}` {status_text} `{link_preview}...`\n"
        kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_stock_lists")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "admin_gen_code":
        if not is_admin(user_id):
            return
        await query.edit_message_text(
            f"{E('gift')} **Generate Code**\n\nSend number of points (1-100):",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('back')} Cancel", callback_data="admin_panel")]])
        )
        set_user_data(user_id, "awaiting_code_points", True)

    elif data == "admin_codes_list":
        if not is_admin(user_id):
            return
        codes = get_all_gift_codes()
        if not codes:
            text = f"{E('gift')} **No codes yet**"
        else:
            act = len([c for c in codes if c[6] == 'active'])
            red = len([c for c in codes if c[6] == 'redeemed'])
            text = f"{E('gift')} **Codes: {act} active | {red} redeemed**\n\n"
            for c in codes[:10]:
                status_icon = f"{E('check')}" if c[6] == 'active' else f"{E('key')}"
                redeemed_info = f" → `{c[5]}`" if c[5] else ""
                text += f"{status_icon} `{c[1]}` {E('star')}{c[2]}{redeemed_info}\n"
        kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "admin_pending":
        if not is_admin(user_id):
            return
        pend = get_pending_withdrawals()
        if not pend:
            text = f"{E('time')} **No pending requests** {E('check')}"
            kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")]]
        else:
            text = f"{E('time')} **Pending ({len(pend)})**\n\n"
            for w in pend:
                u = get_user(w[1])
                un = u[2] if u else "?"
                ic = E('netflix') if w[2] == 'netflix' else E('prime')
                text += f"{ic} `#{w[0]}` **{un}** `{w[1]}` {w[5][:16]}\n"
            kb = [
                [InlineKeyboardButton(f"{E('check')} Fulfill", callback_data="admin_fulfill_menu")],
                [InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")],
            ]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "admin_fulfill_menu":
        if not is_admin(user_id):
            return
        pend = get_pending_withdrawals()
        if not pend:
            await query.edit_message_text(f"{E('check')} All done!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")]]))
            return
        kb = []
        for w in pend[:10]:
            u = get_user(w[1])
            un = u[2] if u else "?"
            ic = E('netflix') if w[2] == 'netflix' else E('prime')
            kb.append([InlineKeyboardButton(f"#{w[0]} {un} {ic}", callback_data=f"fulfill_{w[0]}")])
        kb.append([InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_pending")])
        await query.edit_message_text(f"{E('check')} **Select to fulfill:**", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("fulfill_"):
        if not is_admin(user_id):
            return
        wid = int(data.replace("fulfill_", ""))
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT user_id, type, points_used FROM withdrawals WHERE id=?", (wid,))
        r = c.fetchone()
        conn.close()
        if r:
            uid, wtype, pts = r
            sv = wtype if wtype in ['netflix', 'prime'] else 'netflix'
            st = get_available_stock(sv)
            try:
                if st:
                    assign_stock(st[0], uid, sv)
                    await context.bot.send_message(uid,
                        f"{E(sv)} **{sv.title()} Delivered!**\n"
                        f"{E('check')} Request `#{wid}`\n"
                        f"{E('key')} `{st[1]}`\n"
                        f"{E('lock')} Change password!",
                        parse_mode="HTML")
                else:
                    await context.bot.send_message(uid,
                        f"{E(sv)} **{sv.title()} Delivered!**\n"
                        f"Contact @{ADMIN_USERNAMES[0]} for details.",
                        parse_mode="HTML")
            except:
                pass
            fulfill_withdrawal(wid)

        await query.answer(f"{E('check')} #{wid} fulfilled!", show_alert=True)
        pend = get_pending_withdrawals()
        if not pend:
            text = f"{E('time')} **All fulfilled!** {E('check')}"
            kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")]]
        else:
            text = f"{E('time')} **Pending ({len(pend)})**\n\n"
            for w in pend:
                u = get_user(w[1])
                un = u[2] if u else "?"
                text += f"`#{w[0]}` **{un}** `{w[1]}`\n"
            kb = [[InlineKeyboardButton(f"{E('check')} Fulfill", callback_data="admin_fulfill_menu")],
                  [InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "admin_users":
        if not is_admin(user_id):
            return
        all_u = get_all_users()
        text = f"{E('people')} **All Users ({len(all_u)})**\n\n"
        for u in all_u[:20]:
            text += f"`{u[0]}` **{u[2]}** {E('star')}{u[3]} {E('people')}{u[4]} {E('netflix')}{u[7]} {E('prime')}{u[8]}\n"
        if len(all_u) > 20:
            text += f"\n... +{len(all_u)-20} more"
        kb = [[InlineKeyboardButton(f"{E('back')} Back", callback_data="admin_panel")]]
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "admin_broadcast":
        if not is_admin(user_id):
            return
        await query.edit_message_text(
            f"{E('broadcast')} **Broadcast** {E('warning')}\n\nSend message for ALL users:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('back')} Cancel", callback_data="admin_panel")]])
        )
        set_user_data(user_id, "awaiting_broadcast", True)


# ============================================================
# 📝 TEXT HANDLER - PERSISTENT STATE FROM DB
# ============================================================
async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    text = update.message.text.strip()

    flags = get_user_flags(uid)

    # Add channel via text
    if flags.get("awaiting_channel_add") and is_admin(uid):
        del_user_data(uid, "awaiting_channel_add")
        ch_input = text
        ch_username = ""
        ch_link = ""
        ch_id = ""

        if ch_input.startswith('-100') or ch_input.startswith('-'):
            ch_id = ch_input
            ch_username = ch_input
            ch_link = ""
        elif ch_input.startswith('@'):
            ch_username = ch_input.replace('@', '')
            ch_id = ch_username
            ch_link = f"https://t.me/{ch_username}"
        else:
            await update.message.reply_text(
                f"{E('cross')} Invalid format!\nUse `@channelusername` or `-1001234567890`",
                parse_mode="HTML"
            )
            return

        # ============================================================
# 📦 /addstock CONVERSATION
# ============================================================
ADD_LINK, ADD_CONF = range(2)

async def addstock_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text(f"{E('cross')} Admins only")
        return ConversationHandler.END
    sv = 'netflix'
    if context.args and context.args[0].lower() in ['prime', 'netflix']:
        sv = context.args[0].lower()
    context.user_data["addstock_svc"] = sv
    ic = E('netflix') if sv == 'netflix' else E('prime')
    await update.message.reply_text(
        f"{ic} **Add {sv.title()} Stock**\n\nSend login link or `/cancel`:",
        parse_mode="HTML")
    return ADD_LINK

async def addstock_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()
    if link == "/cancel":
        await update.message.reply_text(
            f"{E('cross')} Cancelled",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('admin')} Panel", callback_data="admin_panel")]])
        )
        return ConversationHandler.END
    context.user_data["pending_link"] = link
    sv = context.user_data.get("addstock_svc", "netflix")
    ic = E('netflix') if sv == 'netflix' else E('prime')
    await update.message.reply_text(
        f"{ic} **Confirm**\n`{link[:50]}{'...' if len(link) > 50 else ''}`",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(f"{E('check')} Confirm"), KeyboardButton(f"{E('cross')} Cancel")]],
            resize_keyboard=True, one_time_keyboard=True))
    return ADD_CONF

async def addstock_conf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text.strip()
    link = context.user_data.get("pending_link", "")
    sv = context.user_data.get("addstock_svc", "netflix")
    if E('check') in t or "confirm" in t.lower():
        sid = add_stock(link, update.effective_user.id, sv)
        sc = get_stock_count(sv)
        await update.message.reply_text(
            f"{E('check')} **{sv.title()} Added!**\n`#{sid}` | Available: `{sc['available']}`",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove())
        return ADD_LINK
    else:
        await update.message.reply_text(f"{E('cross')} Cancelled", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def addstock_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"{E('cross')} Cancelled")
    return ConversationHandler.END

# ============================================================
# 📋 COMMANDS
# ============================================================
async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = get_user(update.effective_user.id)
    if not ud:
        await update.message.reply_text(f"{E('cross')} Use /start")
        return
    t = f"{E('star')} **Stats**\n{E('star')}`{ud[3]}` | {E('people')}`{ud[4]}` | {E('netflix')}`{ud[7]}` | {E('prime')}`{ud[8]}`"
    await update.message.reply_text(t, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('back')} Menu", callback_data="back_home")]]))

async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = f"https://t.me/{context.bot.username}?start=ref_{update.effective_user.id}"
    await update.message.reply_text(f"{E('link')} **Your Link**\n`{link}`", parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('back')} Menu", callback_data="back_home")]]))

async def addchannel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text(f"{E('cross')} Admins only")
        return
    if not context.args:
        await update.message.reply_text(f"{E('cross')} Usage: `/addchannel @channelusername`", parse_mode="HTML")
        return
    ch_input = context.args[0]
    ch_username = ""; ch_link = ""; ch_id = ""
    if ch_input.startswith('@'):
        ch_username = ch_input.replace('@', '')
        ch_id = ch_username
        ch_link = f"https://t.me/{ch_username}"
    elif ch_input.startswith('-'):
        ch_id = ch_input
        ch_username = ch_input
    else:
        await update.message.reply_text(f"{E('cross')} Invalid format!\nUse `@channelusername` or `-1001234567890`", parse_mode="HTML")
        return
    success, msg = add_required_channel(ch_id, ch_username, ch_link, uid)
    await update.message.reply_text(f"{E('check') if success else E('cross')} {msg}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('admin')} Panel", callback_data="admin_panel")]]))

async def removechannel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text(f"{E('cross')} Admins only")
        return
    if not context.args:
        await update.message.reply_text(f"{E('cross')} Usage: `/removechannel @channelusername`", parse_mode="HTML")
        return
    ch_input = context.args[0]
    ch_id = ch_input.replace('@', '') if ch_input.startswith('@') else ch_input
    removed = remove_required_channel(ch_id)
    if removed:
        await update.message.reply_text(f"{E('check')} Channel removed!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{E('admin')} Panel", callback_data="admin_panel")]]))
    else:
        await update.message.reply_text(f"{E('cross')} Channel not found!")

async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = get_required_channels()
    if not channels:
        await update.message.reply_text(f"{E('channel')} **No required channels set.**", parse_mode="HTML")
        return
    text = f"{E('channel')} **Required Channels ({len(channels)})**\n\n"
    for ch in channels:
        cid, username, link = ch[1], ch[2], ch[3]
        text += f"{E('join')} `{username or cid}`\n  Link: `{link or 'N/A'}`\n\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)

# ============================================================
# 🚀 MAIN
# ============================================================
def main():
    init_db()
    logger.info("Database initialized")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("points", points_command))
    app.add_handler(CommandHandler("referral", referral_command))
    app.add_handler(CommandHandler("addchannel", addchannel_command))
    app.add_handler(CommandHandler("removechannel", removechannel_command))
    app.add_handler(CommandHandler("channels", channels_command))

    conv = ConversationHandler(
        entry_points=[CommandHandler("addstock", addstock_start)],
        states={
            ADD_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, addstock_link)],
            ADD_CONF: [MessageHandler(filters.TEXT & ~filters.COMMAND, addstock_conf)],
        },
        fallbacks=[CommandHandler("cancel", addstock_cancel)]
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    app.add_error_handler(error_handler)

    logger.info(f"Bot starting - Admins: {ADMIN_USERNAMES}")
    logger.info(f"Payout Channel: {PAYOUT_CHANNEL}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()