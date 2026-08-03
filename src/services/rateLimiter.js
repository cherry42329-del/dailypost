const { cooldownMinutes } = require("../config/env");

// 記錄每個留言者上次被自動回覆的時間，避免同一人短時間內被連續回覆洗版。
// 注意：這是記憶體內的暫存，重啟伺服器或多台實例部署時不會共用資料。
const lastReplyAt = new Map();

function cooldownMs() {
  return cooldownMinutes * 60 * 1000;
}

function isThrottled(userId) {
  const last = lastReplyAt.get(userId);
  const now = Date.now();

  if (last && now - last < cooldownMs()) {
    return true;
  }

  lastReplyAt.set(userId, now);
  return false;
}

// 定期清除已過冷卻時間的紀錄，避免長時間運作、大量不同留言者湧入時 Map 無限增長
setInterval(() => {
  const now = Date.now();
  for (const [userId, last] of lastReplyAt) {
    if (now - last >= cooldownMs()) {
      lastReplyAt.delete(userId);
    }
  }
}, cooldownMs()).unref();

module.exports = { isThrottled };
