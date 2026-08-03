import datetime
from dataclasses import dataclass


@dataclass
class DateCombo:
    depart: datetime.date
    return_: datetime.date
    duration_days: int
    in_preferred_window: bool


def generate_candidates(trip, duration_min_days: int, duration_max_days: int, max_combos: int):
    """列出某梯次所有合法的(出發,回程)組合,優先窗口內的組合排在前面,並截斷到 max_combos 筆。

    行程天數以「頭尾都算一天」計算,例如出發當天到回程當天共4天即為 duration=4
    (回程 - 出發 = 3 天差)。
    """
    combos = []
    span_days = (trip.range_end - trip.range_start).days
    for offset in range(span_days + 1):
        depart = trip.range_start + datetime.timedelta(days=offset)
        for duration in range(duration_min_days, duration_max_days + 1):
            return_date = depart + datetime.timedelta(days=duration - 1)
            if return_date > trip.range_end:
                continue
            in_preferred = (
                trip.preferred_start <= depart <= trip.preferred_end
                and trip.preferred_start <= return_date <= trip.preferred_end
            )
            combos.append(
                DateCombo(
                    depart=depart,
                    return_=return_date,
                    duration_days=duration,
                    in_preferred_window=in_preferred,
                )
            )

    combos.sort(key=lambda c: (not c.in_preferred_window, c.depart, c.duration_days))
    return combos[:max_combos]
