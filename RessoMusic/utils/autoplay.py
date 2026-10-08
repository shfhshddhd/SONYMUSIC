import re

import aiohttp
from py_yt import VideosSearch


_INNERTUBE_KEY = "AIzaSyBOti4m-6x9WDnZIjIeyEU21OpBXqWBgw"
_INNERTUBE_CLIENT_VERSION = "2.20250101.01.00"
_VIDEO_ID_RE = re.compile(
    r"(?i)(?:youtube\\.com/(?:watch\\?v=|embed/|shorts/|live/)|youtu\\.be/)"
    r"([A-Za-z0-9_-]{11})"
)


def _video_id(value: str) -> str:
    if not value:
        return ""
    match = _VIDEO_ID_RE.search(value)
    if match:
        return match.group(1)
    return value if re.fullmatch(r"[A-Za-z0-9_-]{11}", value) else ""


def _dig(value, *path):
    cur = value
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _text(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("simpleText"), str):
            return value["simpleText"]
        runs = value.get("runs")
        if isinstance(runs, list):
            return "".join(
                str(item.get("text", "")) for item in runs if isinstance(item, dict)
            )
    return ""


def _track(renderer: dict) -> dict | None:
    video_id = renderer.get("videoId")
    title = _text(renderer.get("title"))
    if not video_id or not title:
        return None
    return {
        "id": video_id,
        "title": title,
        "duration": _text(renderer.get("lengthText")) or "00:00",
    }


def _walk(value, renderer_key: str, out: list[dict], limit: int) -> None:
    if len(out) >= limit:
        return
    if isinstance(value, list):
        for item in value:
            _walk(item, renderer_key, out, limit)
            if len(out) >= limit:
                return
    elif isinstance(value, dict):
        renderer = value.get(renderer_key)
        if isinstance(renderer, dict):
            track = _track(renderer)
            if track:
                out.append(track)
                if len(out) >= limit:
                    return
        for child in value.values():
            _walk(child, renderer_key, out, limit)
            if len(out) >= limit:
                return


async def _next(payload: dict) -> dict:
    url = f"https://m.youtube.com/youtubei/v1/next?key={_INNERTUBE_KEY}"
    context = {
        "client": {
            "clientName": "WEB",
            "clientVersion": _INNERTUBE_CLIENT_VERSION,
            "hl": "en-IN",
            "gl": "IN",
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            json={"context": context, **payload},
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            if response.status >= 400:
                raise RuntimeError(
                    f"YouTube recommendation HTTP {response.status}"
                )
            return await response.json()


async def _search_candidates(query: str, limit: int = 10) -> list[dict]:
    if not query:
        return []

    results = await VideosSearch(query, limit=limit).next()
    items = results.get("result") or []
    out = []

    for item in items:
        video_id = item.get("id")
        title = item.get("title")
        if not video_id or not title:
            continue
        out.append(
            {
                "id": video_id,
                "title": title,
                "duration": item.get("duration") or "00:00",
            }
        )
    return out


async def candidates(
    last_id: str,
    limit: int = 10,
    fallback_queries: list[str] | None = None,
) -> list[dict]:
    video_id = _video_id(last_id)
    if not video_id:
        return []

    out = []
    seen = set()

    try:
        result = await _next({"playlistId": "RD" + video_id})
        items = _dig(
            result,
            "contents",
            "twoColumnWatchNextResults",
            "playlist",
            "playlist",
            "contents",
        )
        _walk(items or [], "playlistPanelVideoRenderer", out, limit)
    except Exception:
        pass

    if len(out) < limit:
        try:
            result = await _next({"videoId": video_id})
            _walk(result, "compactVideoRenderer", out, limit)
            if len(out) < limit:
                _walk(result, "videoRenderer", out, limit)
        except Exception:
            pass

    unique = []
    for item in out:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique.append(item)

    if unique:
        return unique[:limit]

    # YouTube's recommendation endpoint can fail/change format. In that case
    # use normal multi-result search instead of the old single-result fallback.
    for query in fallback_queries or []:
        try:
            for item in await _search_candidates(query, limit):
                if item["id"] not in seen:
                    seen.add(item["id"])
                    unique.append(item)
                    if len(unique) >= limit:
                        return unique[:limit]
        except Exception:
            continue

    return unique[:limit]
