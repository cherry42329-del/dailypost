const express = require("express");
const axios = require("axios");
const {
  verifyToken,
  igBusinessAccountId,
  igAccessToken,
  graphApiVersion,
} = require("../config/env");

const router = express.Router();

// 手動觸發一次，把你的 IG 帳號訂閱到這個 App，之後才會開始收到留言等 webhook 事件。
// 用 ?token= 帶入 VERIFY_TOKEN 做簡單防護，避免網址被亂猜到就能亂觸發。
router.get("/subscribe", async (req, res) => {
  if (req.query.token !== verifyToken) {
    const serverTokenSet = Boolean(verifyToken);
    const serverTokenLength = verifyToken ? verifyToken.length : 0;
    const givenTokenLength = req.query.token ? req.query.token.length : 0;
    return res
      .status(403)
      .send(
        `Forbidden - 伺服器有讀到 VERIFY_TOKEN：${serverTokenSet}（長度 ${serverTokenLength}），` +
          `你網址帶的 token 長度：${givenTokenLength}`
      );
  }
  if (!igBusinessAccountId || !igAccessToken) {
    return res
      .status(400)
      .send("缺少 IG_BUSINESS_ACCOUNT_ID 或 IG_ACCESS_TOKEN，請先完成授權流程");
  }

  try {
    const url = `https://graph.instagram.com/${graphApiVersion}/${igBusinessAccountId}/subscribed_apps`;
    const response = await axios.post(url, null, {
      params: {
        subscribed_fields: "comments",
        access_token: igAccessToken,
      },
    });
    res.send(`
      <h2>訂閱結果</h2>
      <pre>${JSON.stringify(response.data, null, 2)}</pre>
      <p>看到 <code>success: true</code> 就代表訂閱成功，之後留言才會觸發 webhook。</p>
    `);
  } catch (err) {
    console.error("訂閱失敗：", err.response?.data || err.message);
    res
      .status(500)
      .send(`訂閱失敗：${JSON.stringify(err.response?.data || err.message)}`);
  }
});

module.exports = router;
