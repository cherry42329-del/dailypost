"""用 Open-Meteo 免費歷史氣象 API 估算某目的地在某月份的「典型天氣」。

因為監控的旅遊日期遠在未來(無法查即時預報),改用過去5年同一段日期
(月/日相同、年份不同)的歷史觀測平均值來估計典型氣候,僅供參考。
Open-Meteo Archive API 不需要 API key。
"""
import datetime
import logging

import requests

ARCHIVE_ENDPOINT = "https://archive-api.open-meteo.com/v1/archive"
YEARS_LOOKBACK = 5


logger = logging.getLogger(__name__)


class WeatherEstimate:
    def __init__(self, avg_max_c, avg_min_c, avg_daily_precip_mm, comfort_score, label):
        self.avg_max_c = avg_max_c
        self.avg_min_c = avg_min_c
        self.avg_daily_precip_mm = avg_daily_precip_mm
        self.comfort_score = comfort_score
        self.label = label


def _classify(avg_max, avg_min, avg_precip):
    score = 40
    notes = []

    if avg_max >= 33 or avg_min <= 8:
        score -= 25
        notes.append("偏熱" if avg_max >= 33 else "偏冷")
    elif avg_max >= 30 or avg_min <= 12:
        score -= 10
        notes.append("稍熱" if avg_max >= 30 else "稍涼")
    else:
        notes.append("舒適")

    if avg_precip >= 8:
        score -= 15
        notes.append("多雨")
    elif avg_precip >= 4:
        score -= 5
        notes.append("偶有降雨")
    else:
        notes.append("降雨機率低")

    score = max(0, score)
    label = f"{avg_min:.0f}–{avg_max:.0f}°C，{('、').join(notes)}（日均雨量約{avg_precip:.1f}mm）"
    return score, label


def estimate_weather(lat, lon, depart_date, return_date, mock=False):
    if mock:
        return WeatherEstimate(29, 24, 2.0, 35, "24–29°C，舒適、降雨機率低（mock data）")

    month = depart_date.month
    day = depart_date.day
    current_year = datetime.date.today().year

    highs, lows, precs = [], [], []
    for years_back in range(1, YEARS_LOOKBACK + 1):
        year = current_year - years_back
        try:
            hist_start = datetime.date(year, month, day)
        except ValueError:
            hist_start = datetime.date(year, month, 28)
        hist_end = hist_start + datetime.timedelta(days=(return_date - depart_date).days)

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": hist_start.isoformat(),
            "end_date": hist_end.isoformat(),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto",
        }
        try:
            resp = requests.get(ARCHIVE_ENDPOINT, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            logger.warning("查詢歷史氣象失敗 (%s,%s) %s: %s", lat, lon, hist_start, e)
            continue

        daily = data.get("daily", {})
        highs.extend([v for v in daily.get("temperature_2m_max", []) if v is not None])
        lows.extend([v for v in daily.get("temperature_2m_min", []) if v is not None])
        precs.extend([v for v in daily.get("precipitation_sum", []) if v is not None])

    if not highs or not lows:
        return WeatherEstimate(0, 0, 0, 20, "查無歷史氣象資料")

    avg_max = sum(highs) / len(highs)
    avg_min = sum(lows) / len(lows)
    avg_precip = (sum(precs) / len(precs)) if precs else 0.0

    score, label = _classify(avg_max, avg_min, avg_precip)
    return WeatherEstimate(avg_max, avg_min, avg_precip, score, label)
