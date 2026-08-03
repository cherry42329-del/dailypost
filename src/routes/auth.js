const express = require("express");
const axios = require("axios");
const { igAppId, appSecret, igRedirectUri } = require("../config/env");

const router = express.Router();

// Instagram Business Login 授權完成後，Instagram 會導回這裡並帶上 code
router.get("/callback", async (req, res) => {
  const { code, error, error_description: errorDescription } = req.query;

  if (error) {
    return res.status(400).send(`授權失敗：${errorDescription || error}`);
  }
  if (!code) {
    return res.status(400).send("缺少 code 參數");
  }

  try {
    const shortLived = await axios.post(
      "https://api.instagram.com/oauth/access_token",
      new URLSearchParams({
        client_id: igAppId,
        client_secret: appSecret,
        grant_type: "authorization_code",
        redirect_uri: igRedirectUri,
        code,
      })
    );

    const { access_token: shortLivedToken, user_id: userId } = shortLived.data;

    const longLived = await axios.get("https://graph.instagram.com/access_token", {
      params: {
        grant_type: "ig_exchange_token",
        client_secret: appSecret,
        access_token: shortLivedToken,
      },
    });

    const { access_token: longLivedToken, expires_in: expiresIn } = longLived.data;
    const expiresInDays = Math.round(expiresIn / 86400);

    res.send(`
      <h2>授權成功</h2>
      <p>把下面這兩個值填進 .env（或 Render 的環境變數）：</p>
      <p><b>IG_BUSINESS_ACCOUNT_ID</b> = ${userId}</p>
      <p><b>IG_ACCESS_TOKEN</b> = ${longLivedToken}</p>
      <p>這組長效 token 約 ${expiresInDays} 天後過期，到期前要重新走一次這個授權流程換新的。</p>
    `);
  } catch (err) {
    console.error("Token 交換失敗：", err.response?.data || err.message);
    res
      .status(500)
      .send(`Token 交換失敗：${JSON.stringify(err.response?.data || err.message)}`);
  }
});

module.exports = router;
