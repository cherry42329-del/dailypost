import Database from "better-sqlite3";
import fs from "fs";
import path from "path";

const dataDir = path.join(process.cwd(), "data");
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

export const db = new Database(path.join(dataDir, "dailypost.sqlite"));
db.pragma("journal_mode = WAL");

db.exec(`
  CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    imageUrl TEXT NOT NULL,
    caption TEXT NOT NULL DEFAULT '',
    scheduledTime TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    igMediaId TEXT,
    errorMessage TEXT,
    createdAt TEXT NOT NULL DEFAULT (datetime('now')),
    publishedAt TEXT
  )
`);

export type PostStatus = "pending" | "publishing" | "published" | "failed";

export interface Post {
  id: number;
  imageUrl: string;
  caption: string;
  scheduledTime: string;
  status: PostStatus;
  igMediaId: string | null;
  errorMessage: string | null;
  createdAt: string;
  publishedAt: string | null;
}
