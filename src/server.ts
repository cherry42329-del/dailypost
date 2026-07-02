import "dotenv/config";
import express from "express";
import path from "path";
import { postsRouter } from "./routes/posts";
import { startScheduler } from "./scheduler";

const app = express();
const port = process.env.PORT ? Number(process.env.PORT) : 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, "..", "public")));
app.use("/api/posts", postsRouter);

app.listen(port, () => {
  console.log(`[server] dailypost 已啟動: http://localhost:${port}`);
  startScheduler();
});
