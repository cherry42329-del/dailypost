import logging

import requests

PUSH_ENDPOINT = "https://api.line.me/v2/bot/message/push"
BROADCAST_ENDPOINT = "https://api.line.me/v2/bot/message/broadcast"
LINE_MAX_MESSAGES_PER_CALL = 5

logger = logging.getLogger(__name__)


def send_line_messages(texts, channel_access_token, user_id=None, mock=False):
    """依 LINE Messaging API 限制,每次最多帶 5 則訊息,超過就分批呼叫。
    若提供 user_id 使用 push(推給指定使用者),否則使用 broadcast(推給官方帳號所有好友)。
    """
    if mock:
        for t in texts:
            print("=== [MOCK LINE MESSAGE] ===")
            print(t)
        return True

    if not channel_access_token:
        logger.warning("缺少 LINE_CHANNEL_ACCESS_TOKEN,無法推播")
        return False

    endpoint = PUSH_ENDPOINT if user_id else BROADCAST_ENDPOINT
    headers = {
        "Authorization": f"Bearer {channel_access_token}",
        "Content-Type": "application/json",
    }

    ok = True
    for i in range(0, len(texts), LINE_MAX_MESSAGES_PER_CALL):
        batch = texts[i : i + LINE_MAX_MESSAGES_PER_CALL]
        payload = {"messages": [{"type": "text", "text": t} for t in batch]}
        if user_id:
            payload["to"] = user_id

        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error("LINE 推播失敗: %s / %s", e, getattr(e.response, "text", ""))
            ok = False

    return ok
