import html

from pyrogram.types import InlineKeyboardMarkup, LinkPreviewOptions

from RessoMusic import app
from RessoMusic.core.mongo import mongodb
from RessoMusic.misc import db
from RessoMusic.utils.inline.play import stream_markup

captiondb = mongodb.stream_captions


async def get_stream_caption(_, link, title, duration, user):
    """Build a safe now-playing caption without letting formatting break playback."""
    safe_link = html.escape(str(link or ""))
    safe_title = html.escape(str(title or "Unknown"))
    safe_duration = html.escape(str(duration or "00:00"))
    safe_user = html.escape(str(user or "Unknown"))

    try:
        data = await captiondb.find_one({"chat_id": "GLOBAL_CAPTION"})
        custom_html = data.get("text") if data else None
        if custom_html:
            try:
                return custom_html.format(
                    safe_link, safe_title, safe_duration, safe_user
                )
            except Exception:
                pass
    except Exception:
        pass

    try:
        return _["stream_1"].format(
            safe_link, safe_title, safe_duration, safe_user
        )
    except Exception:
        return (
            "<blockquote>▣ <b>Started Streaming♪</b></blockquote>\n"
            f"<blockquote><b>Title:</b> {safe_title}\n"
            f"<b>Duration:</b> {safe_duration} minutes\n"
            f"<b>Requested:</b> {safe_user}</blockquote>"
        )


async def send_now_playing(
    _,
    original_chat_id,
    chat_id,
    link,
    title,
    duration,
    user,
    markup_type="stream",
):
    """
    Send the now-playing card safely.

    A failure while building/sending the information card must NEVER propagate
    back into the playback path after the voice call has started.
    """
    cap = await get_stream_caption(_, link, title, duration, user)

    try:
        button = stream_markup(_, chat_id)
    except Exception:
        button = []

    # Preferred message: preserve the existing link-preview-above-text design.
    try:
        run = await app.send_message(
            original_chat_id,
            text=cap,
            link_preview_options=LinkPreviewOptions(
                is_disabled=False,
                show_above_text=True,
            ),
            reply_markup=InlineKeyboardMarkup(button) if button else None,
        )
    except Exception:
        run = None

    # Fallback 1: send the same card without LinkPreviewOptions.
    if run is None:
        try:
            run = await app.send_message(
                original_chat_id,
                text=cap,
                disable_web_page_preview=False,
                reply_markup=InlineKeyboardMarkup(button) if button else None,
            )
        except Exception:
            run = None

    # Fallback 2: plain safe text. Playback is already successful, so never
    # raise a notification exception back to /play.
    if run is None:
        try:
            run = await app.send_message(
                original_chat_id,
                text=(
                    "<blockquote>▣ <b>Started Streaming♪</b></blockquote>\n"
                    f"<blockquote><b>Title:</b> {html.escape(str(title or 'Unknown'))}\n"
                    f"<b>Duration:</b> {html.escape(str(duration or '00:00'))} minutes\n"
                    f"<b>Requested:</b> {html.escape(str(user or 'Unknown'))}</blockquote>"
                ),
            )
        except Exception:
            return None

    try:
        if db.get(chat_id):
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = markup_type
    except Exception:
        # Message bookkeeping must never break playback either.
        pass

    return run
