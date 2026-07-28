const express = require("express");
const { port } = require("./config/env");
const webhookRouter = require("./routes/webhook");

const app = express();

app.use(
  express.json({
    verify: (req, res, buf) => {
      req.rawBody = buf;
    },
  })
);

app.get("/", (req, res) => {
  res.send("dailypost IG 自動回覆系統運作中");
});

app.use("/webhook", webhookRouter);

app.listen(port, () => {
  console.log(`伺服器已啟動，監聽埠號 ${port}`);
});
