import cron from "node-cron";
import { db, Post } from "./db";
import { publishImagePost } from "./igClient";

const selectDuePosts = db.prepare(
  `SELECT * FROM posts WHERE status = 'pending' AND scheduledTime <= datetime('now') ORDER BY scheduledTime ASC`
);
const markPublishing = db.prepare(`UPDATE posts SET status = 'publishing' WHERE id = ?`);
const markPublished = db.prepare(
  `UPDATE posts SET status = 'published', igMediaId = ?, publishedAt = datetime('now'), errorMessage = NULL WHERE id = ?`
);
const markFailed = db.prepare(`UPDATE posts SET status = 'failed', errorMessage = ? WHERE id = ?`);

async function processDuePosts(): Promise<void> {
  const duePosts = selectDuePosts.all() as Post[];

  for (const post of duePosts) {
    markPublishing.run(post.id);
    try {
      const igMediaId = await publishImagePost(post.imageUrl, post.caption);
      markPublished.run(igMediaId, post.id);
      console.log(`[scheduler] 貼文 #${post.id} 發布成功 (igMediaId=${igMediaId})`);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      markFailed.run(message, post.id);
      console.error(`[scheduler] 貼文 #${post.id} 發布失敗: ${message}`);
    }
  }
}

export function startScheduler(): void {
  cron.schedule("* * * * *", () => {
    processDuePosts().catch((error) => {
      console.error("[scheduler] 執行排程時發生未預期錯誤:", error);
    });
  });
  console.log("[scheduler] 排程引擎已啟動，每分鐘檢查一次待發布貼文");
}
