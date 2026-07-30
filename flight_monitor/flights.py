"""SerpApi Google Flights 查詢包裝。

Google Flights 的來回票查詢分兩段:
  1. 查詢去程,取得 best_flights/other_flights 與各選項的 departure_token
  2. 帶著 departure_token 再查一次,取得對應的回程選項與最終總價

這代表每一組「目的地 x 出發日 x 回程日」至少會消耗 2 次 SerpApi 額度
(若要再取訂票連結,還會再多 1 次)。請透過 config.yaml 的
max_date_combos_per_destination 與目的地清單控制總呼叫量與費用。
"""
import datetime
import logging

import requests

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
MAX_OUTBOUND_CANDIDATES = 3

# 常見航空公司官網,用於「官方訂票頁」欄位的 fallback 連結(Google Flights 不提供
# 可直接帶入航班資料的官網深層連結,只能連到官網首頁,需使用者自行輸入日期查詢)。
AIRLINE_HOMEPAGE = {
    "China Airlines": "https://www.china-airlines.com/tw/zh",
    "EVA Air": "https://www.evaair.com/zh-tw/",
    "Starlux Airlines": "https://www.starlux-airlines.com/zh-TW",
    "Tigerair Taiwan": "https://www.tigerairtw.com/zh-tw",
    "Scoot": "https://www.flyscoot.com/zh",
    "AirAsia": "https://www.airasia.com/zh/tw",
    "Cebu Pacific Air": "https://www.cebupacificair.com/zh-tw",
    "Peach Aviation": "https://www.flypeach.com/tw",
    "Jetstar": "https://www.jetstar.com/tw/zh",
    "Vietjet Air": "https://www.vietjetair.com/zh-hant",
    "Korean Air": "https://www.koreanair.com/tw/zh",
    "Asiana Airlines": "https://flyasiana.com/C/TW/ZH/index",
    "Cathay Pacific": "https://www.cathaypacific.com/cx/zh_TW.html",
    "Hong Kong Express": "https://www.hkexpress.com/zh-tw/",
    "Singapore Airlines": "https://www.singaporeair.com/zh_TW/tw/home",
    "Thai AirAsia": "https://www.airasia.com/zh/tw",
    "Philippine Airlines": "https://www.philippineairlines.com/zh-TW",
}

logger = logging.getLogger(__name__)


class FlightOption:
    def __init__(
        self,
        destination_code,
        depart_date,
        return_date,
        duration_days,
        price_twd,
        airline,
        outbound_depart_time,
        outbound_arrive_time,
        return_depart_time,
        return_arrive_time,
        has_checked_baggage,
        google_flights_url,
        notes,
    ):
        self.destination_code = destination_code
        self.depart_date = depart_date
        self.return_date = return_date
        self.duration_days = duration_days
        self.price_twd = price_twd
        self.airline = airline
        self.outbound_depart_time = outbound_depart_time
        self.outbound_arrive_time = outbound_arrive_time
        self.return_depart_time = return_depart_time
        self.return_arrive_time = return_arrive_time
        self.has_checked_baggage = has_checked_baggage
        self.google_flights_url = google_flights_url
        self.notes = notes

    @property
    def airline_booking_url(self):
        return AIRLINE_HOMEPAGE.get(self.airline, "")

    def is_redeye(self):
        for t in (self.outbound_depart_time, self.return_depart_time):
            if t is None:
                continue
            hour = t.hour
            if 0 <= hour < 6:
                return True
        return False


def _parse_dt(s):
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def _is_direct(leg_list):
    return isinstance(leg_list, list) and len(leg_list) == 1


def _extract_itinerary_fields(flights_field):
    leg = flights_field[0]
    airline = leg.get("airline", "未知")
    depart_time = _parse_dt(leg.get("departure_airport", {}).get("time"))
    arrive_time = _parse_dt(leg.get("arrival_airport", {}).get("time"))
    has_baggage = bool(leg.get("extensions")) and any(
        "checked bag" in e.lower() and "no" not in e.lower() for e in leg.get("extensions", [])
    )
    return airline, depart_time, arrive_time, has_baggage


def search_round_trip_flights(origin, destination, depart_date, return_date, api_key, mock=False):
    """回傳某目的地 + 某組日期的直飛來回票選項列表(list of FlightOption)。"""
    if mock:
        return _mock_flights(origin, destination, depart_date, return_date)

    if not api_key:
        logger.warning("缺少 SERPAPI_API_KEY,略過 %s %s~%s 的查詢", destination, depart_date, return_date)
        return []

    base_params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": depart_date.isoformat(),
        "return_date": return_date.isoformat(),
        "currency": "TWD",
        "hl": "zh-tw",
        "type": "1",
        "api_key": api_key,
    }

    try:
        resp = requests.get(SERPAPI_ENDPOINT, params=base_params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.warning("查詢去程失敗 %s: %s", destination, e)
        return []

    google_flights_url = data.get("search_metadata", {}).get("google_flights_url", "")
    outbound_candidates = (data.get("best_flights") or []) + (data.get("other_flights") or [])
    outbound_candidates = [c for c in outbound_candidates if _is_direct(c.get("flights", []))]
    outbound_candidates = outbound_candidates[:MAX_OUTBOUND_CANDIDATES]

    results = []
    for outbound in outbound_candidates:
        departure_token = outbound.get("departure_token")
        if not departure_token:
            continue

        step2_params = dict(base_params)
        step2_params["departure_token"] = departure_token
        try:
            resp2 = requests.get(SERPAPI_ENDPOINT, params=step2_params, timeout=30)
            resp2.raise_for_status()
            data2 = resp2.json()
        except requests.RequestException as e:
            logger.warning("查詢回程失敗 %s: %s", destination, e)
            continue

        return_candidates = (data2.get("best_flights") or []) + (data2.get("other_flights") or [])
        return_candidates = [c for c in return_candidates if _is_direct(c.get("flights", []))]

        for ret in return_candidates:
            price = ret.get("price") or outbound.get("price")
            if not price:
                continue
            out_airline, out_dep, out_arr, out_bag = _extract_itinerary_fields(outbound["flights"])
            ret_airline, ret_dep, ret_arr, ret_bag = _extract_itinerary_fields(ret["flights"])
            duration_days = (return_date - depart_date).days + 1
            results.append(
                FlightOption(
                    destination_code=destination,
                    depart_date=depart_date,
                    return_date=return_date,
                    duration_days=duration_days,
                    price_twd=price,
                    airline=out_airline if out_airline == ret_airline else f"{out_airline}/{ret_airline}",
                    outbound_depart_time=out_dep,
                    outbound_arrive_time=out_arr,
                    return_depart_time=ret_dep,
                    return_arrive_time=ret_arr,
                    has_checked_baggage=out_bag and ret_bag,
                    google_flights_url=google_flights_url,
                    notes="",
                )
            )

    return results


def _mock_flights(origin, destination, depart_date, return_date):
    """本機測試用假資料,不呼叫任何外部 API。"""
    duration_days = (return_date - depart_date).days + 1
    out_dep = datetime.datetime.combine(depart_date, datetime.time(8, 30))
    out_arr = out_dep + datetime.timedelta(hours=2, minutes=30)
    ret_dep = datetime.datetime.combine(return_date, datetime.time(19, 0))
    ret_arr = ret_dep + datetime.timedelta(hours=2, minutes=40)
    return [
        FlightOption(
            destination_code=destination,
            depart_date=depart_date,
            return_date=return_date,
            duration_days=duration_days,
            price_twd=9800,
            airline="Tigerair Taiwan",
            outbound_depart_time=out_dep,
            outbound_arrive_time=out_arr,
            return_depart_time=ret_dep,
            return_arrive_time=ret_arr,
            has_checked_baggage=False,
            google_flights_url=f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{destination}",
            notes="(mock data)",
        )
    ]
