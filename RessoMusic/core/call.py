# -----------------------------------------------
# 🔸 StrangerMusic Project
# 🔹 Developed & Maintained by: Shashank AMBOTOP (https://github.com/itzAMBOTOP)
# 📅 Copyright © 2022 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by ItzAMBOTOP
# -----------------------------------------------
import asyncio
import os
from datetime import datetime, timedelta
from typing import Union
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, LinkPreviewOptions
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    TelegramServerError,
)
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, MediumQualityVideo
from pytgcalls.types.stream import StreamAudioEnded
import config
from RessoMusic import LOGGER, YouTube, app
from RessoMusic.misc import db
from RessoMusic.core.mongo import mongodb
from RessoMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    get_autoplay,
    get_autoplay_history,
    add_autoplay_history,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from RessoMusic.utils.exceptions import AssistantErr
from RessoMusic.utils.formatters import check_duration, seconds_to_min, speed_converter, time_to_seconds
from RessoMusic.utils.inline.play import stream_markup
from RessoMusic.utils.autoplay import candidates as autoplay_candidates
from RessoMusic.utils.stream.autoclear import auto_clean
from RessoMusic.utils.thumbnails import FIXED_THUMBNAIL_URL, get_thumb
from strings import get_string

autoend = {}
counter = {}

# --- CUSTOM CAPTION LOGIC ---
captiondb = mongodb.stream_captions

async def get_stored_caption():
    """Fetches the custom caption from MongoDB."""
    data = await captiondb.find_one({"chat_id": "GLOBAL_CAPTION"})
    if data and "text" in data:
        return data["text"]
    return None

async def send_now_playing(original_chat_id, caption, button):
    return await app.send_photo(
        original_chat_id,
        photo=FIXED_THUMBNAIL_URL,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(button),
    )

async def get_caption(_, link, title, duration, user):
    """Generates the final caption string, formatted with arguments."""
    custom_html = await get_stored_caption()
    if custom_html:
        try:
            return custom_html.format(link, title, duration, user)
        except Exception:
            pass 
    return _["stream_1"].format(link, title, duration, user)

async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)

class Call(PyTgCalls):
    def __init__(self):
        self.userbot1 = Client(
            name="AMBOTOPAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(
            self.userbot1,
            cache_duration=100,
        )
        self.userbot2 = Client(
            name="AMBOTOPAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
        )
        self.two = PyTgCalls(
            self.userbot2,
            cache_duration=100,
        )
        self.userbot3 = Client(
            name="AMBOTOPAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
        )
        self.three = PyTgCalls(
            self.userbot3,
            cache_duration=100,
        )
        self.userbot4 = Client(
            name="AMBOTOPAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
        )
        self.four = PyTgCalls(
            self.userbot4,
            cache_duration=100,
        )
        self.userbot5 = Client(
            name="AMBOTOPAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
        )
        self.five = PyTgCalls(
            self.userbot5,
            cache_duration=100,
        )
        # Prevent StreamAudioEnded and manual Skip from advancing the same chat twice.
        self._transitioning = set()

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def stop_stream_force(self, chat_id: int):
        try:
            if config.STRING1:
                await self.one.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING2:
                await self.two.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING3:
                await self.three.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING4:
                await self.four.leave_group_call(chat_id)
        except:
            pass
        try:
            if config.STRING5:
                await self.five.leave_group_call(chat_id)
        except:
            pass
        try:
            await _clear_(chat_id)
        except:
            pass

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        if str(speed) != str("1.0"):
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                if str(speed) == str("0.5"):
                    vs = 2.0
                if str(speed) == str("0.75"):
                    vs = 1.35
                if str(speed) == str("1.5"):
                    vs = 0.68
                if str(speed) == str("2.0"):
                    vs = 0.5
                proc = await asyncio.create_subprocess_shell(
                    cmd=(
                        "ffmpeg "
                        "-i "
                        f"{file_path} "
                        "-filter:v "
                        f"setpts={vs}*PTS "
                        "-filter:a "
                        f"atempo={speed} "
                        f"{out}"
                    ),
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
            else:
                pass
        else:
            out = file_path
        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        stream = (
            AudioVideoPiped(
                out,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
            if playing[0]["streamtype"] == "video"
            else AudioPiped(
                out,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {played} -to {duration}",
            )
        )
        if str(db[chat_id][0]["file"]) == str(file_path):
            await assistant.change_stream(chat_id, stream)
        else:
            raise AssistantErr("Umm")
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        if video:
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = AudioPiped(link, audio_parameters=HighQualityAudio())
        await assistant.change_stream(
            chat_id,
            stream,
        )

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        stream = (
            AudioVideoPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
            if mode == "video"
            else AudioPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
                additional_ffmpeg_parameters=f"-ss {to_seek} -to {duration}",
            )
        )
        await assistant.change_stream(chat_id, stream)

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOGGER_ID)
        await assistant.join_group_call(
            config.LOGGER_ID,
            AudioVideoPiped(link),
            stream_type=StreamType().pulse_stream,
        )
        await asyncio.sleep(0.2)
        await assistant.leave_group_call(config.LOGGER_ID)

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        language = await get_lang(chat_id)
        _ = get_string(language)
        if video:
            stream = AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
        else:
            stream = (
                AudioVideoPiped(
                    link,
                    audio_parameters=HighQualityAudio(),
                    video_parameters=MediumQualityVideo(),
                )
                if video
                else AudioPiped(link, audio_parameters=HighQualityAudio())
            )
        try:
            await assistant.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

    async def get_autoplay_item(self, chat_id: int, last_item: dict):
        if not last_item or not await get_autoplay(chat_id):
            return None

        last_id = str(last_item.get("vidid") or "")
        last_title = str(last_item.get("title") or "").strip()
        if not last_id and not last_title:
            return None

        history = await get_autoplay_history(chat_id)
        fallback_queries = []
        if last_title:
            fallback_queries = [
                last_title,
                f"{last_title} song",
            ]

        recommendations = []
        try:
            recommendations = await autoplay_candidates(
                last_id,
                limit=10,
                fallback_queries=fallback_queries,
            )
        except Exception as ex:
            LOGGER(__name__).error(
                f"Autoplay engine failed in {chat_id}: "
                f"{type(ex).__name__}: {ex}"
            )

        for item in recommendations:
            video_id = item.get("id")
            if not video_id or video_id == last_id or video_id in history:
                continue

            duration = item.get("duration") or "00:00"
            try:
                duration_seconds = time_to_seconds(duration)
            except Exception:
                duration_seconds = 0
                duration = "00:00"

            await add_autoplay_history(chat_id, video_id)
            LOGGER(__name__).info(
                f"Autoplay selected: {item.get('title', 'Unknown')} "
                f"({video_id}) in {chat_id}"
            )

            return {
                "title": item.get("title") or last_title or "Autoplay",
                "dur": duration,
                "streamtype": "autoplay_query",
                "by": "♫ Autoplay",
                "user_id": 0,
                "chat_id": last_item.get("chat_id", chat_id),
                "file": item.get("title") or last_title or "Autoplay",
                "vidid": video_id,
                "seconds": duration_seconds,
                "played": 0,
            }

        LOGGER(__name__).warning(
            f"Autoplay found no usable recommendation for {chat_id}; "
            f"last_id={last_id!r}"
        )
        return None

    async def change_stream(self, client, chat_id):
        if chat_id in self._transitioning:
            return
        self._transitioning.add(chat_id)
        try:
            return await self._change_stream(client, chat_id)
        finally:
            self._transitioning.discard(chat_id)

    async def _change_stream(self, client, chat_id):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)
            # Remove the completed song's group message before showing the next track.
            if popped:
                try:
                    old_message = popped.get("mystic")
                    if old_message:
                        await old_message.delete()
                except Exception:
                    pass
            await auto_clean(popped)
            if not check:
                autoplay_item = await self.get_autoplay_item(chat_id, popped)
                if autoplay_item:
                    db[chat_id].append(autoplay_item)
                    check = db[chat_id]
                else:
                    await _clear_(chat_id)
                    return await client.leave_group_call(chat_id)
        except:
            try:
                await _clear_(chat_id)
                return await client.leave_group_call(chat_id)
            except:
                return
        else:
            queued = check[0]["file"]
            language = await get_lang(chat_id)
            _ = get_string(language)
            title = (check[0]["title"]).title()
            user = check[0]["by"]
            original_chat_id = check[0]["chat_id"]
            streamtype = check[0]["streamtype"]
            videoid = check[0]["vidid"]
            db[chat_id][0]["played"] = 0
            exis = (check[0]).get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = check[0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0
            video = True if str(streamtype) == "video" else False
            
            # Link preview settings for "above text" logic
            preview_options = LinkPreviewOptions(is_disabled=False, show_above_text=True)

            if streamtype == "autoplay_query":
                # Autoplay only selects the next query. Resolve playback through
                # the same DRX -> YouTube source pipeline used by normal /play.
                try:
                    resolved = await resolve_query(queued)
                except Exception as ex:
                    LOGGER(__name__).error(
                        f"Autoplay playback resolution failed in {chat_id}: "
                        f"{type(ex).__name__}: {ex}"
                    )
                    return await app.send_message(original_chat_id, text=_["call_6"])

                if not resolved:
                    return await app.send_message(original_chat_id, text=_["call_6"])

                details, resolved_type, resolved_id = resolved
                video = bool(str(last_item.get("streamtype", "audio")) == "video")

                if resolved_type == "drx":
                    file_path = details["filepath"]
                else:
                    mystic = await app.send_message(original_chat_id, _["call_7"])
                    try:
                        file_path, direct = await YouTube.download(
                            resolved_id,
                            mystic,
                            videoid=True,
                            video=video,
                        )
                    except Exception:
                        try:
                            await mystic.delete()
                        except Exception:
                            pass
                        return await app.send_message(original_chat_id, text=_["call_6"])
                    try:
                        await mystic.delete()
                    except Exception:
                        pass

                stream = (
                    AudioVideoPiped(
                        file_path,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                    if video
                    else AudioPiped(
                        file_path,
                        audio_parameters=HighQualityAudio(),
                    )
                )
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    return await app.send_message(original_chat_id, text=_["call_6"])

                button = stream_markup(_, chat_id)
                link = details.get(
                    "link",
                    f"https://t.me/{app.username}?start=info_{resolved_id}",
                )
                cap = await get_caption(
                    _,
                    link,
                    details.get("title", title)[:23],
                    details.get("duration_min", check[0]["dur"]),
                    user,
                )
                run = await send_now_playing(original_chat_id, cap, button)
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

            elif "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                if video:
                    stream = AudioVideoPiped(
                        link,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        link,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except Exception:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                
                button = stream_markup(_, chat_id)
                vid_link = f"https://t.me/{app.username}?start=info_{videoid}"
                cap = await get_caption(_, vid_link, title[:23], check[0]["dur"], user)

                run = await send_now_playing(original_chat_id, cap, button)
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            elif "vid_" in queued:
                mystic = await app.send_message(original_chat_id, _["call_7"])
                try:
                    file_path, direct = await YouTube.download(
                        videoid,
                        mystic,
                        videoid=True,
                        video=True if str(streamtype) == "video" else False,
                    )
                except:
                    return await mystic.edit_text(
                        _["call_6"], link_preview_options=LinkPreviewOptions(is_disabled=True)
                    )
                if video:
                    stream = AudioVideoPiped(
                        file_path,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        file_path,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                
                button = stream_markup(_, chat_id)
                await mystic.delete()
                vid_link = f"https://t.me/{app.username}?start=info_{videoid}"
                cap = await get_caption(_, vid_link, title[:23], check[0]["dur"], user)

                run = await send_now_playing(original_chat_id, cap, button)
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            elif "index_" in queued:
                stream = (
                    AudioVideoPiped(
                        videoid,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                    if str(streamtype) == "video"
                    else AudioPiped(videoid, audio_parameters=HighQualityAudio())
                )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                button = stream_markup(_, chat_id)
                run = await app.send_message(
                    chat_id=original_chat_id,
                    text=_["stream_2"].format(user),
                    link_preview_options=preview_options,
                    reply_markup=InlineKeyboardMarkup(button),
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            else:
                if video:
                    stream = AudioVideoPiped(
                        queued,
                        audio_parameters=HighQualityAudio(),
                        video_parameters=MediumQualityVideo(),
                    )
                else:
                    stream = AudioPiped(
                        queued,
                        audio_parameters=HighQualityAudio(),
                    )
                try:
                    await client.change_stream(chat_id, stream)
                except:
                    return await app.send_message(
                        original_chat_id,
                        text=_["call_6"],
                    )
                if videoid == "telegram":
                    button = stream_markup(_, chat_id)
                    cap = await get_caption(_, config.SUPPORT_CHAT, title[:23], check[0]["dur"], user)

                    run = await send_now_playing(original_chat_id, cap, button)
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                elif videoid == "soundcloud":
                    button = stream_markup(_, chat_id)
                    cap = await get_caption(_, config.SUPPORT_CHAT, title[:23], check[0]["dur"], user)

                    run = await send_now_playing(original_chat_id, cap, button)
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                else:
                    button = stream_markup(_, chat_id)
                    vid_link = f"https://t.me/{app.username}?start=info_{videoid}"
                    cap = await get_caption(_, vid_link, title[:23], check[0]["dur"], user)

                    run = await send_now_playing(original_chat_id, cap, button)
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"

    async def ping(self):
        pings = []
        if config.STRING1:
            pings.append(await self.one.ping)
        if config.STRING2:
            pings.append(await self.two.ping)
        if config.STRING3:
            pings.append(await self.three.ping)
        if config.STRING4:
            pings.append(await self.four.ping)
        if config.STRING5:
            pings.append(await self.five.ping)
        return str(round(sum(pings) / len(pings), 3))

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        if config.STRING1:
            await self.one.start()
        if config.STRING2:
            await self.two.start()
        if config.STRING3:
            await self.three.start()
        if config.STRING4:
            await self.four.start()
        if config.STRING5:
            await self.five.start()

    async def decorators(self):
        @self.one.on_kicked()
        @self.two.on_kicked()
        @self.three.on_kicked()
        @self.four.on_kicked()
        @self.five.on_kicked()
        @self.one.on_closed_voice_chat()
        @self.two.on_closed_voice_chat()
        @self.three.on_closed_voice_chat()
        @self.four.on_closed_voice_chat()
        @self.five.on_closed_voice_chat()
        @self.one.on_left()
        @self.two.on_left()
        @self.three.on_left()
        @self.four.on_left()
        @self.five.on_left()
        async def stream_services_handler(_, chat_id: int):
            await self.stop_stream(chat_id)

        @self.one.on_stream_end()
        @self.two.on_stream_end()
        @self.three.on_stream_end()
        @self.four.on_stream_end()
        @self.five.on_stream_end()
        async def stream_end_handler1(client, update: Update):
            if not isinstance(update, StreamAudioEnded):
                return
            await self.change_stream(client, update.chat_id)


AMBOTOP = Call()
