from pyrogram import filters
from pyrogram.types import Message

from RessoMusic import app
from RessoMusic.misc import SUDOERS
from RessoMusic.utils.database import get_autoplay, get_lang, is_nonadmin_chat, set_autoplay
from config import BANNED_USERS, adminlist
from strings import get_string


@app.on_message(filters.command("autoplay") & ~BANNED_USERS)
async def autoplay_command(client, message: Message):
    chat_id = message.chat.id

    if message.chat.type != "private":
        is_non_admin = await is_nonadmin_chat(chat_id)
        if not is_non_admin and message.from_user.id not in SUDOERS:
            admins = adminlist.get(chat_id) or []
            if message.from_user.id not in admins:
                language = await get_lang(chat_id)
                _ = get_string(language)
                return await message.reply_text(_["admin_14"])

    enabled = not await get_autoplay(chat_id)
    await set_autoplay(chat_id, enabled)
    await message.reply_text(f"♫ Autoplay {'ON' if enabled else 'OFF'}")
