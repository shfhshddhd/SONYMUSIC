from pyrogram.types import InlineKeyboardButton

import config
from RessoMusic import app


async def get_owner_button():
    try:
        owner = await app.get_users(config.OWNER_ID)
        if owner.username:
            return InlineKeyboardButton(
                "˹ ϻʏ ϻᴧsᴛєʀ ˼ 👑",
                url=f"https://t.me/{owner.username}",
            )
    except Exception:
        pass

    return InlineKeyboardButton(
        "˹ ϻʏ ϻᴧsᴛєʀ ˼ 👑",
        url=f"tg://user?id={config.OWNER_ID}",
    )


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_GROUP),
        ],
    ]
    return buttons


async def private_panel(_):
    owner_button = await get_owner_button()
    buttons = [
        [
            InlineKeyboardButton(
                "˹ᴛᴧᴘ ᴛᴏ sєє ϻᴧɢɪᴄ˼",
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [InlineKeyboardButton("˹ʜєʟᴘ˼", callback_data="settings_back_helper"),
        InlineKeyboardButton("˹ᴄʜᴧɴɴєʟ˼", url="https://t.me/itzdhruv1060"),
            #InlineKeyboardButton(text=_["S_B_7"], url=config.UPSTREAM_REPO),
        ],
        [owner_button],
        
    ]
    return buttons


