import threading
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from security import get_current_phone

router = APIRouter(prefix="/geo", tags=["Location"])

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim asks every app to identify itself with a User-Agent
USER_AGENT = "BloodLink-hackathon/1.0 (student project)"
CACHE_SECONDS = 24 * 3600     # the same search is not sent again for a day
MIN_GAP_SECONDS = 1.1         # Nominatim allows 1 request per second

_cache = {}
_lock = threading.Lock()
_last_call = 0.0


def _place(item: dict) -> dict:
    address = item.get("address", {})
    city = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("county")
        or address.get("state_district")
        or ""
    )
    return {
        "name": item.get("name") or item.get("display_name", "").split(",")[0],
        "display_name": item.get("display_name", ""),
        "city": city,
        "state": address.get("state", ""),
        "latitude": float(item["lat"]),
        "longitude": float(item["lon"]),
    }


def _lookup(query: str, limit: int) -> list:
    global _last_call
    cache_key = (query.lower(), limit)
    hit = _cache.get(cache_key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]

    with _lock:
        # keep at least ~1 second between two calls to Nominatim
        wait = MIN_GAP_SECONDS - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        try:
            response = httpx.get(
                NOMINATIM_URL,
                params={
                    "q": query,
                    "format": "jsonv2",
                    "addressdetails": 1,
                    "limit": limit,
                    "countrycodes": "in",     # India only
                },
                headers={"User-Agent": USER_AGENT},
                timeout=8.0,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(
                status_code=503,
                detail="Location search is not available right now. Please try again.",
            )
        finally:
            _last_call = time.time()

    places = []
    seen = set()
    for item in response.json():
        place = _place(item)
        # Same name and same address = the same place, show it only once
        place_key = (place["name"].lower(), place["display_name"].lower())
        if place_key in seen:
            continue
        seen.add(place_key)
        places.append(place)

    if places:
        _cache[cache_key] = (time.time(), places)
    return places


@router.get("/search")
def search_place(
    q: str = Query(..., min_length=3, max_length=120),
    limit: int = Query(5, ge=1, le=10),
    phone: str = Depends(get_current_phone),
):
    """Place or hospital name in, a list of matching places out.

    Each place has a latitude and longitude. The app lets the user pick one
    and sends its latitude and longitude to POST /requests (hospital) or
    POST /donors/register (donor's location).
    """
    return _lookup(q.strip(), limit)