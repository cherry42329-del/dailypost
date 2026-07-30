import datetime
import os
from dataclasses import dataclass, field

import yaml

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")


@dataclass
class Destination:
    code: str
    name: str
    lat: float
    lon: float


@dataclass
class Trip:
    name: str
    range_start: datetime.date
    range_end: datetime.date
    preferred_start: datetime.date
    preferred_end: datetime.date


@dataclass
class Config:
    origin: str
    trips: list
    duration_min_days: int
    duration_max_days: int
    budget_min_twd: int
    budget_max_twd: int
    direct_only: bool
    top_n: int
    max_date_combos_per_destination: int
    destinations: list
    free_tier_enabled: bool = False
    free_tier_max_searches_per_month: int = 90
    free_tier_refresh_runs_per_month: int = 30
    free_tier_cache_path: str = ""
    serpapi_api_key: str = ""
    line_channel_access_token: str = ""
    line_user_id: str = ""


def _parse_date(value: str) -> datetime.date:
    return datetime.date.fromisoformat(value)


def load_config(path: str = CONFIG_PATH) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    trips = [
        Trip(
            name=t["name"],
            range_start=_parse_date(t["range_start"]),
            range_end=_parse_date(t["range_end"]),
            preferred_start=_parse_date(t["preferred_start"]),
            preferred_end=_parse_date(t["preferred_end"]),
        )
        for t in raw["trips"]
    ]

    destinations = [
        Destination(code=d["code"], name=d["name"], lat=d["lat"], lon=d["lon"])
        for d in raw["destinations"]
    ]

    free_tier = raw.get("free_tier", {})
    repo_root = os.path.dirname(os.path.abspath(path))
    cache_path = free_tier.get("cache_path", "data/price_cache.json")
    if not os.path.isabs(cache_path):
        cache_path = os.path.join(repo_root, cache_path)

    return Config(
        origin=raw["origin"],
        trips=trips,
        duration_min_days=raw["duration_min_days"],
        duration_max_days=raw["duration_max_days"],
        budget_min_twd=raw["budget_min_twd"],
        budget_max_twd=raw["budget_max_twd"],
        direct_only=raw["direct_only"],
        top_n=raw["top_n"],
        max_date_combos_per_destination=raw["max_date_combos_per_destination"],
        destinations=destinations,
        free_tier_enabled=free_tier.get("enabled", False),
        free_tier_max_searches_per_month=free_tier.get("max_searches_per_month", 90),
        free_tier_refresh_runs_per_month=free_tier.get("refresh_runs_per_month", 30),
        free_tier_cache_path=cache_path,
        serpapi_api_key=os.environ.get("SERPAPI_API_KEY", ""),
        line_channel_access_token=os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", ""),
        line_user_id=os.environ.get("LINE_USER_ID", ""),
    )
