import axios from "axios";

const GRAPH_API_VERSION = "v21.0";
const GRAPH_API_BASE = `https://graph.facebook.com/${GRAPH_API_VERSION}`;

function getConfig() {
  const igUserId = process.env.IG_USER_ID;
  const accessToken = process.env.IG_ACCESS_TOKEN;
  if (!igUserId || !accessToken) {
    throw new Error("缺少 IG_USER_ID 或 IG_ACCESS_TOKEN 環境變數，請參考 .env.example 設定");
  }
  return { igUserId, accessToken };
}

async function waitUntilContainerReady(containerId: string, accessToken: string): Promise<void> {
  const maxAttempts = 10;
  const delayMs = 3000;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const { data } = await axios.get(`${GRAPH_API_BASE}/${containerId}`, {
      params: { fields: "status_code", access_token: accessToken },
    });
    if (data.status_code === "FINISHED") return;
    if (data.status_code === "ERROR") {
      throw new Error(`Instagram 媒體容器處理失敗 (container ${containerId})`);
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  throw new Error(`Instagram 媒體容器處理逾時 (container ${containerId})`);
}

export async function publishImagePost(imageUrl: string, caption: string): Promise<string> {
  const { igUserId, accessToken } = getConfig();

  const createRes = await axios.post(`${GRAPH_API_BASE}/${igUserId}/media`, null, {
    params: { image_url: imageUrl, caption, access_token: accessToken },
  });
  const creationId: string = createRes.data.id;

  await waitUntilContainerReady(creationId, accessToken);

  const publishRes = await axios.post(`${GRAPH_API_BASE}/${igUserId}/media_publish`, null, {
    params: { creation_id: creationId, access_token: accessToken },
  });

  return publishRes.data.id as string;
}
