require("dotenv").config();

module.exports = {
  port: process.env.PORT || 3000,
  verifyToken: process.env.VERIFY_TOKEN,
  igBusinessAccountId: process.env.IG_BUSINESS_ACCOUNT_ID,
  igAccessToken: process.env.IG_ACCESS_TOKEN,
  graphApiVersion: process.env.GRAPH_API_VERSION || "v21.0",
  appSecret: process.env.APP_SECRET || null,
  cooldownMinutes: Number(process.env.COOLDOWN_MINUTES) || 10,
  igAppId: process.env.IG_APP_ID,
  igRedirectUri: process.env.IG_REDIRECT_URI,
};
