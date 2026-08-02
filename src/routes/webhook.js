const express = require("express");
const { verifyToken, igBusinessAccountId } = require("../config/env");
const { isValidSignature } = require("../services/verifySignature");
const { findReply } = require("../services/matcher");
const { replyToComment } = require("../services/instagram");
const { isThrottled } = require("../services/rateLimiter");

const router = express.Router();

// Meta 在你設定 Webhook URL 時，會發 GET 請求做一次性驗證
router.get("/", (req, res) => {
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];

  if (mode === "subscribe" && token === verifyToken) {
    return res.status(200).send(challenge);
  }
  return res.sendStatus(403);
});

// 之後每次有新留言，Meta 會打這個 POST 過來
router.post("/", (req, res) => {
  if (!isValidSignature(req)) {
    return res.sendStatus(401);
  }

  // 先回 200，避免 Meta 因逾時重送同一事件
  res.sendStatus(200);

  const entries = req.body.entry || [];
  for (const entry of entries) {
    const changes = entry.changes || [];
    for (const change of changes) {
      if (change.field !== "comments") continue;
      handleComment(change.value).catch((err) => {
        console.error("處理留言失敗：", err.response?.data || err.message);
      });
    }
  }
});

async function handleComment(comment) {
  if (!comment || !comment.id || !comment.text) return;

  // 避免回覆到自己帳號發出的留言（例如自動回覆本身），造成無限迴圈
  if (comment.from && comment.from.id === igBusinessAccountId) return;

  const reply = findReply(comment.text);
  if (!reply) return;

  const commenterId = comment.from && comment.from.id;
  if (commenterId && isThrottled(commenterId)) {
    console.log(`已略過留言 ${comment.id}：留言者 ${commenterId} 冷卻中`);
    return;
  }

  await replyToComment(comment.id, reply);
  console.log(`已回覆留言 ${comment.id}：${reply}`);
}

module.exports = router;
