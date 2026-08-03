const axios = require("axios");
const { igAccessToken, graphApiVersion } = require("../config/env");

async function replyToComment(commentId, message) {
  const url = `https://graph.instagram.com/${graphApiVersion}/${commentId}/replies`;

  const response = await axios.post(url, null, {
    params: {
      message,
      access_token: igAccessToken,
    },
  });

  return response.data;
}

module.exports = { replyToComment };
