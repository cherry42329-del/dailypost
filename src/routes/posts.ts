import { Router } from "express";
import { db, Post } from "../db";

export const postsRouter = Router();

const insertPost = db.prepare(
  `INSERT INTO posts (imageUrl, caption, scheduledTime) VALUES (?, ?, ?)`
);
const selectAllPosts = db.prepare(`SELECT * FROM posts ORDER BY scheduledTime DESC`);
const selectPostById = db.prepare(`SELECT * FROM posts WHERE id = ?`);
const deletePost = db.prepare(`DELETE FROM posts WHERE id = ? AND status IN ('pending', 'failed')`);

postsRouter.get("/", (_req, res) => {
  const posts = selectAllPosts.all() as Post[];
  res.json(posts);
});

postsRouter.post("/", (req, res) => {
  const { imageUrl, caption, scheduledTime } = req.body ?? {};

  if (typeof imageUrl !== "string" || !/^https?:\/\//.test(imageUrl)) {
    return res.status(400).json({ error: "imageUrl 必須是有效的 http(s) 網址" });
  }
  if (typeof scheduledTime !== "string" || Number.isNaN(Date.parse(scheduledTime))) {
    return res.status(400).json({ error: "scheduledTime 必須是有效的日期時間" });
  }

  const isoScheduledTime = new Date(scheduledTime).toISOString().slice(0, 19).replace("T", " ");
  const result = insertPost.run(imageUrl, typeof caption === "string" ? caption : "", isoScheduledTime);
  const created = selectPostById.get(result.lastInsertRowid) as Post;
  res.status(201).json(created);
});

postsRouter.delete("/:id", (req, res) => {
  const id = Number(req.params.id);
  const post = selectPostById.get(id) as Post | undefined;
  if (!post) {
    return res.status(404).json({ error: "找不到貼文" });
  }
  if (post.status !== "pending" && post.status !== "failed") {
    return res.status(409).json({ error: "只能取消尚未發布或發布失敗的貼文" });
  }
  deletePost.run(id);
  res.status(204).send();
});
