import datetime

LINE_MAX_CHARS = 4800  # LINE 單則文字上限 5000,留一點餘裕


def _fmt_time(dt):
    if dt is None:
        return "時間未知"
    return dt.strftime("%H:%M")


def _fmt_date(d):
    return d.strftime("%Y/%m/%d")


def format_option_block(rank, option):
    f = option.flight
    w = option.weather
    baggage = "含托運行李" if f.has_checked_baggage else "不含托運行李"

    notes = []
    if f.is_redeye():
        notes.append("紅眼班機(起飛時間為凌晨0-6點)")
    if option.in_preferred_window:
        notes.append("落在優先日期區間")
    if f.notes:
        notes.append(f.notes)
    notes_text = "、".join(notes) if notes else "無"

    lines = [
        f"【選項 {rank}】",
        f"🌏 目的地：{option.destination_name}（{option.destination_code}）",
        f"💰 來回票價：NT${f.price_twd:,.0f}",
        f"✈️ 航空公司：{f.airline}",
        f"🛫 去程：{_fmt_date(f.depart_date)} {_fmt_time(f.outbound_depart_time)} 起飛／{_fmt_time(f.outbound_arrive_time)} 降落",
        f"🛬 回程：{_fmt_date(f.return_date)} {_fmt_time(f.return_depart_time)} 起飛／{_fmt_time(f.return_arrive_time)} 降落",
        f"📅 行程天數：{f.duration_days} 天",
        f"🧳 行李：{baggage}",
        f"🌤️ 預估天氣：{w.label}",
        f"🔗 Google Flights：{f.google_flights_url or '（無法取得連結）'}",
        f"🔗 航空公司官方訂票頁：{f.airline_booking_url or '（請於Google Flights頁面內比較訂票平台）'}",
        f"📝 備註：{notes_text}",
    ]
    return "\n".join(lines)


def format_trip_message(trip, ranked_options):
    header = f"✈️ 機票監控通知－{trip.name}\n區間：{_fmt_date(trip.range_start)}～{_fmt_date(trip.range_end)}"

    if not ranked_options:
        return header + "\n\n本次未找到符合預算(NT$4,000-18,000)且直飛的選項，系統會持續監控。"

    blocks = [format_option_block(i + 1, opt) for i, opt in enumerate(ranked_options)]
    return header + "\n\n" + "\n\n".join(blocks)


def chunk_message(text, max_chars=LINE_MAX_CHARS):
    """若單則訊息超過 LINE 字數上限,依段落切分成多則訊息。"""
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for p in paragraphs:
        candidate = (current + "\n\n" + p) if current else p
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = p
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def build_run_timestamp_footer():
    now = datetime.datetime.now()
    return f"\n\n（查詢時間：{now.strftime('%Y-%m-%d %H:%M')}）"
