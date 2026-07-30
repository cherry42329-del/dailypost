import argparse
import datetime
import logging
import sys

from flight_monitor.config import load_config
from flight_monitor.dates import generate_candidates
from flight_monitor.flights import FlightOption, search_round_trip_flights
from flight_monitor.weather import estimate_weather
from flight_monitor.ranking import filter_and_rank
from flight_monitor.message import format_trip_message, chunk_message, build_run_timestamp_footer
from flight_monitor.notify_line import send_line_messages
from flight_monitor.cache import load_cache, save_cache, entry_key, get_rotation_batch, days_since

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_trip_full(cfg, trip, mock=False):
    """非免費方案模式:完整查詢該梯次所有目的地 x 所有日期組合(呼叫量較高)。"""
    combos = generate_candidates(
        trip, cfg.duration_min_days, cfg.duration_max_days, cfg.max_date_combos_per_destination
    )

    candidates = []
    for destination in cfg.destinations:
        for combo in combos:
            options = search_round_trip_flights(
                cfg.origin, destination.code, combo.depart, combo.return_, cfg.serpapi_api_key, mock=mock
            )
            for flight in options:
                weather = estimate_weather(destination.lat, destination.lon, combo.depart, combo.return_, mock=mock)
                candidates.append(
                    {
                        "destination": destination,
                        "flight": flight,
                        "weather": weather,
                        "in_preferred_window": combo.in_preferred_window,
                    }
                )

    ranked = filter_and_rank(candidates, cfg.budget_min_twd, cfg.budget_max_twd, cfg.top_n)
    logger.info("%s：找到 %d 個候選, 篩選後 %d 個最佳選項", trip.name, len(candidates), len(ranked))
    return ranked


def refresh_free_tier_cache(cfg, cache, do_refresh):
    """免費方案模式:輪流刷新一小批(trip, destination),其餘沿用快取。"""
    items = [(trip, destination) for trip in cfg.trips for destination in cfg.destinations]
    items_per_run = max(
        1, cfg.free_tier_max_searches_per_month // cfg.free_tier_refresh_runs_per_month // 2
    )

    if not do_refresh:
        logger.info("本次執行不刷新價格(沿用快取),下次刷新批次大小=%d", items_per_run)
        return cache

    batch, next_index = get_rotation_batch(items, cache.get("rotation_index", 0), items_per_run)
    logger.info("本次刷新 %d 組(trip, destination): %s", len(batch), [(t.name, d.code) for t, d in batch])

    for trip, destination in batch:
        combos = generate_candidates(trip, cfg.duration_min_days, cfg.duration_max_days, max_combos=1)
        if not combos:
            continue
        combo = combos[0]
        options = search_round_trip_flights(
            cfg.origin, destination.code, combo.depart, combo.return_, cfg.serpapi_api_key
        )
        key = entry_key(trip.name, destination.code)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if options:
            best = min(options, key=lambda o: o.price_twd)
            entry = best.to_cache_dict()
            entry["in_preferred_window"] = combo.in_preferred_window
            entry["checked_at"] = now
            cache["entries"][key] = entry
        else:
            cache["entries"][key] = {"no_result": True, "checked_at": now}

    cache["rotation_index"] = next_index
    return cache


def build_ranked_from_cache(cfg, trip, cache):
    candidates = []
    for destination in cfg.destinations:
        entry = cache["entries"].get(entry_key(trip.name, destination.code))
        if not entry or entry.get("no_result"):
            continue

        flight = FlightOption.from_cache_dict(entry)
        weather = estimate_weather(destination.lat, destination.lon, flight.depart_date, flight.return_date)

        age_days = days_since(entry["checked_at"])
        staleness_note = f"資料更新於{age_days}天前"
        flight.notes = f"{flight.notes}；{staleness_note}" if flight.notes else staleness_note

        candidates.append(
            {
                "destination": destination,
                "flight": flight,
                "weather": weather,
                "in_preferred_window": entry.get("in_preferred_window", False),
            }
        )

    ranked = filter_and_rank(candidates, cfg.budget_min_twd, cfg.budget_max_twd, cfg.top_n)
    logger.info(
        "%s：快取中有 %d 個目的地資料, 篩選後 %d 個最佳選項", trip.name, len(candidates), len(ranked)
    )
    return ranked


def main():
    parser = argparse.ArgumentParser(description="機票監控系統")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="使用假資料執行(不呼叫 SerpApi/Open-Meteo,僅用於本機測試訊息格式與流程)",
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="只印出結果,不實際推播 LINE(--mock 模式下仍會印出訊息內容)",
    )
    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="免費方案模式專用:本次執行不呼叫 SerpApi 刷新價格,只用快取裡的舊資料組訊息",
    )
    args = parser.parse_args()

    cfg = load_config()

    all_messages = []

    if cfg.free_tier_enabled and not args.mock:
        cache = load_cache(cfg.free_tier_cache_path)
        cache = refresh_free_tier_cache(cfg, cache, do_refresh=not args.no_refresh)
        save_cache(cache, cfg.free_tier_cache_path)

        for trip in cfg.trips:
            ranked = build_ranked_from_cache(cfg, trip, cache)
            text = format_trip_message(trip, ranked) + build_run_timestamp_footer()
            all_messages.extend(chunk_message(text))
    else:
        for trip in cfg.trips:
            ranked = run_trip_full(cfg, trip, mock=args.mock)
            text = format_trip_message(trip, ranked) + build_run_timestamp_footer()
            all_messages.extend(chunk_message(text))

    if args.no_notify and not args.mock:
        for m in all_messages:
            print(m)
        return

    ok = send_line_messages(
        all_messages,
        cfg.line_channel_access_token,
        user_id=cfg.line_user_id or None,
        mock=args.mock or args.no_notify,
    )
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
