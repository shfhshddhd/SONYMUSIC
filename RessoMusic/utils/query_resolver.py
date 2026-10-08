import aiohttp
import config


DRX_API_BASE = "https://apidrx-music.vercel.app/api"


def seconds_to_min_str(seconds: int) -> str:
    try:
        seconds = int(seconds or 0)
    except (TypeError, ValueError):
        seconds = 0
    return f"{seconds // 60}:{seconds % 60:02d}"


def get_best_download_url(download_urls: list) -> str | None:
    quality_map = {}
    for item in download_urls or []:
        if not isinstance(item, dict):
            continue
        quality = str(item.get("quality", ""))
        url = item.get("url")
        if not url or not quality.endswith("kbps"):
            continue
        try:
            quality_map[int(quality[:-4])] = url
        except ValueError:
            continue

    for preferred in (160, 320, 96, 48, 12):
        if preferred in quality_map:
            return quality_map[preferred]

    for item in download_urls or []:
        if isinstance(item, dict) and item.get("url"):
            return item["url"]
    return None


def get_500x500_image(images: list):
    for img in images or []:
        if isinstance(img, dict) and img.get("quality") == "500x500" and img.get("url"):
            return img["url"]
    for img in images or []:
        if isinstance(img, dict) and img.get("url"):
            return img["url"]
    return config.PLAYLIST_IMG_URL


async def drx_search_songs(query: str):
    if not query:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{DRX_API_BASE}/search/songs",
                params={"query": query},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                results = data.get("data", {}).get("results")
                return results if data.get("success") and results else None
    except Exception:
        return None


async def resolve_query(query: str):
    """
    Resolve a normal text music query using the same source priority as /play:
    DRX first, then the existing YouTube.track fallback.

    Returns:
        (details, streamtype, track_id)
    """
    query = (query or "").strip()
    if not query:
        return None

    drx_results = await drx_search_songs(query)
    if drx_results:
        song = drx_results[0]
        audio_url = get_best_download_url(song.get("downloadUrl", []))
        if audio_url:
            duration_sec = song.get("duration", 0) or 0
            return (
                {
                    "title": song.get("name") or query,
                    "duration_min": seconds_to_min_str(duration_sec),
                    "thumb": get_500x500_image(song.get("image", [])),
                    "vidid": song.get("id", ""),
                    "filepath": audio_url,
                    "link": song.get("url", config.SUPPORT_CHAT),
                },
                "drx",
                song.get("id", ""),
            )

    from RessoMusic import YouTube

    details, track_id = await YouTube.track(query)
    return details, "youtube", track_id
