import argparse
import logging
import sys

from flight_monitor.config import load_config
from flight_monitor.dates import generate_candidates
from flight_monitor.flights import search_round_trip_flights
from flight_monitor.weather import estimate_weather
from flight_monitor.ranking import filter_and_rank
from flight_monitor.message import format_trip_message, chunk_message, build_run_timestamp_footer
from flight_monitor.notify_line import send_line_messages

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_trip(cfg, trip, mock=False):
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
    args = parser.parse_args()

    cfg = load_config()

    all_messages = []
    for trip in cfg.trips:
        ranked = run_trip(cfg, trip, mock=args.mock)
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
