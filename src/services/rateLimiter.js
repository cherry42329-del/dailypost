const { cooldownMinutes } = require("../config/env");

// 記錄每個留言者上次被自動回覆的時間，避免同一人短時間內被連續回覆洗版。
// 注意：這是記憶體內的暫存，重啟伺服器或多台實例部署時不會共用資料。
const lastReplyAt = new Map();

function isThrottled(userId) {
  const cooldownMs = cooldownMinutes * 60 * 1000;
  const last = lastReplyAt.get(userId);
  const now = Date.now();

  if (last && now - last < cooldownMs) {
    return true;
  }

  lastReplyAt.set(userId, now);
  return false;
}

module.exports = { isThrottled };
