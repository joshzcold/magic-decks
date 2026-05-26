#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import quote, urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.scryfall.com"
USER_AGENT = "MagicDeckBuilder/1.0 (https://github.com/; contact: local)"
ACCEPT_HEADER = "application/json"
REQUEST_DELAY_SECONDS = 0.11
MAX_RETRIES = 3
BACKOFF_SECONDS = 0.5


class ScryfallError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScryfallResponse:
    json: dict[str, Any]
    status: int


_last_request_ts = 0.0


def _throttle() -> None:
    global _last_request_ts
    now = time.time()
    wait = REQUEST_DELAY_SECONDS - (now - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.time()


def _fetch_json(url: str) -> ScryfallResponse:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": ACCEPT_HEADER})
    for attempt in range(MAX_RETRIES + 1):
        _throttle()
        try:
            with urlopen(req, timeout=30) as resp:
                status = resp.status
                data = json.loads(resp.read().decode("utf-8"))
            if status >= 400:
                message = data.get("details") if isinstance(data, dict) else None
                raise ScryfallError(message or f"Scryfall request failed ({status}).")
            if isinstance(data, dict) and data.get("object") == "error":
                raise ScryfallError(data.get("details", "Scryfall error."))
            return ScryfallResponse(json=data, status=status)
        except HTTPError as exc:
            retry_after = None
            if exc.headers is not None:
                retry_after = exc.headers.get("Retry-After")
            if exc.code in {429, 503} and attempt < MAX_RETRIES:
                delay = float(retry_after) if retry_after else BACKOFF_SECONDS * (2 ** attempt)
                time.sleep(delay)
                continue
            body = exc.read().decode("utf-8") if exc.fp else ""
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                data = {}
            message = data.get("details") if isinstance(data, dict) else None
            raise ScryfallError(message or f"Scryfall request failed ({exc.code}).") from exc
        except URLError as exc:
            raise ScryfallError("Network error contacting Scryfall.") from exc
    raise ScryfallError("Scryfall request failed after retries.")


def get_card_by_name(name: str) -> dict[str, Any]:
    url = f"{BASE_URL}/cards/named?exact={quote(name)}"
    return _fetch_json(url).json


def get_card_by_id(card_id: str) -> dict[str, Any]:
    url = f"{BASE_URL}/cards/{quote(card_id)}"
    return _fetch_json(url).json


def get_prices_by_name(name: str) -> dict[str, Any]:
    card = get_card_by_name(name)
    prices = card.get("prices")
    if not isinstance(prices, dict):
        raise ScryfallError("Prices not found for card.")
    return prices


def get_prices_by_id(card_id: str) -> dict[str, Any]:
    card = get_card_by_id(card_id)
    prices = card.get("prices")
    if not isinstance(prices, dict):
        raise ScryfallError("Prices not found for card.")
    return prices


def search_cards(query: str, unique: str = "cards", order: str = "name") -> dict[str, Any]:
    params = urlencode({"q": query, "unique": unique, "order": order})
    url = f"{BASE_URL}/cards/search?{params}"
    return _fetch_json(url).json


def iter_search_cards(query: str, unique: str = "cards", order: str = "name") -> Iterable[dict[str, Any]]:
    data = search_cards(query, unique=unique, order=order)
    while True:
        if data.get("object") != "list":
            raise ScryfallError("Unexpected search response.")
        for item in data.get("data", []):
            yield item
        if not data.get("has_more"):
            return
        next_url = data.get("next_page")
        if not next_url:
            return
        data = _fetch_json(next_url).json


def _example() -> None:
    card = get_card_by_name("Lightning Bolt")
    print(card["name"], card.get("set"), card.get("prices", {}).get("usd"))


if __name__ == "__main__":
    _example()
