"""免費方案模式用的價格快取。

因為 SerpApi 免費額度有限,無法每次執行都把所有目的地都查一遍,
改成每次只「輪流」刷新其中幾個(trip, destination)組合,其餘沿用
上次查到的結果。快取存成 JSON 檔並由 workflow 提交回 repo,
讓下一次執行(甚至換一台機器執行)都能接續進度。
"""
import datetime
import json
import os

DEFAULT_CACHE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "price_cache.json"
)


def load_cache(path=DEFAULT_CACHE_PATH):
    if not os.path.exists(path):
        return {"rotation_index": 0, "entries": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(cache, path=DEFAULT_CACHE_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def entry_key(trip_name, destination_code):
    return f"{trip_name}|{destination_code}"


def get_rotation_batch(items, rotation_index, batch_size):
    """從 items 依 rotation_index 取出接下來 batch_size 個(可能繞回開頭),
    回傳 (batch, 下一次的 rotation_index)。"""
    if not items:
        return [], 0
    n = len(items)
    batch_size = min(batch_size, n)
    batch = [items[(rotation_index + i) % n] for i in range(batch_size)]
    next_index = (rotation_index + batch_size) % n
    return batch, next_index


def days_since(iso_timestamp):
    checked_at = datetime.datetime.fromisoformat(iso_timestamp)
    delta = datetime.datetime.now(checked_at.tzinfo) - checked_at
    return max(0, delta.days)
