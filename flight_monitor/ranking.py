from dataclasses import dataclass


@dataclass
class RankedOption:
    destination_name: str
    destination_code: str
    flight: object  # flights.FlightOption
    weather: object  # weather.WeatherEstimate
    in_preferred_window: bool
    score: float


def score_option(flight, weather, budget_min, budget_max, in_preferred_window):
    price_range = max(1, budget_max - budget_min)
    price_score = 40 * (budget_max - flight.price_twd) / price_range
    price_score = max(0, min(40, price_score))

    weather_score = weather.comfort_score  # 0-40

    preferred_bonus = 15 if in_preferred_window else 0
    redeye_penalty = 10 if flight.is_redeye() else 0

    return price_score + weather_score + preferred_bonus - redeye_penalty


def filter_and_rank(candidates, budget_min, budget_max, top_n):
    """candidates: list of dict{destination, flight, weather, in_preferred_window}
    回傳依分數排序、每個目的地只取最佳一筆的前 top_n 名。
    """
    valid = []
    for c in candidates:
        flight = c["flight"]
        if not (budget_min <= flight.price_twd <= budget_max):
            continue
        score = score_option(flight, c["weather"], budget_min, budget_max, c["in_preferred_window"])
        valid.append(
            RankedOption(
                destination_name=c["destination"].name,
                destination_code=c["destination"].code,
                flight=flight,
                weather=c["weather"],
                in_preferred_window=c["in_preferred_window"],
                score=score,
            )
        )

    valid.sort(key=lambda r: r.score, reverse=True)

    best_per_destination = {}
    for r in valid:
        if r.destination_code not in best_per_destination:
            best_per_destination[r.destination_code] = r

    return list(best_per_destination.values())[:top_n]
