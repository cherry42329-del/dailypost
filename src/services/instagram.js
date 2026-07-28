const axios = require("axios");
const { pageAccessToken, graphApiVersion } = require("../config/env");

async function replyToComment(commentId, message) {
  const url = `https://graph.facebook.com/${graphApiVersion}/${commentId}/replies`;

  const response = await axios.post(url, null, {
    params: {
      message,
      access_token: pageAccessToken,
    },
  });

  return response.data;
}

module.exports = { replyToComment };
