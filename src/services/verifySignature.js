const crypto = require("crypto");
const { appSecret } = require("../config/env");

// Meta 建議驗證 X-Hub-Signature-256，避免有人假冒 Meta 打你的 webhook。
// 沒設定 APP_SECRET 時就跳過驗證（僅建議用於本機測試）。
function isValidSignature(req) {
  if (!appSecret) return true;

  const signature = req.get("x-hub-signature-256");
  if (!signature || !req.rawBody) return false;

  const expected =
    "sha256=" +
    crypto.createHmac("sha256", appSecret).update(req.rawBody).digest("hex");

  const sigBuf = Buffer.from(signature);
  const expBuf = Buffer.from(expected);
  if (sigBuf.length !== expBuf.length) return false;

  return crypto.timingSafeEqual(sigBuf, expBuf);
}

module.exports = { isValidSignature };
