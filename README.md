# dailypost

IG 自動排程工具 — 使用 Node.js + TypeScript，透過 Instagram Graph API 依排程時間自動發布貼文。

## 功能

- 新增排程貼文（圖片網址 + 文案 + 發布時間）
- 每分鐘自動檢查到期貼文並呼叫 Instagram Graph API 發布
- 網頁介面可查看貼文狀態（pending / publishing / published / failed）並取消尚未發布的貼文
- 貼文與發布紀錄儲存在本機 SQLite（`data/dailypost.sqlite`）

## 事前準備：取得 Instagram Graph API 權限

Instagram 內容發布 API 只支援 **Business** 或 **Creator** 帳號，且需綁定一個 Facebook 粉絲專頁。

1. 到 [Facebook for Developers](https://developers.facebook.com/) 建立一個 App，加入 `Instagram Graph API` 產品。
2. 將你的 Instagram 帳號轉為 Business/Creator 帳號，並連結到一個 Facebook 粉絲專頁。
3. 使用 [Graph API Explorer](https://developers.facebook.com/tools/explorer/) 取得具備以下權限的使用者存取權杖：
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
4. 呼叫 `GET /me/accounts` 取得粉絲專頁 ID，再呼叫 `GET /{page-id}?fields=instagram_business_account` 取得 `IG_USER_ID`。
5. 將短期權杖換成長期權杖（有效期約 60 天），填入 `.env` 的 `IG_ACCESS_TOKEN`。

> 注意：圖片必須是**公開可存取的網址**（IG API 會直接從該網址抓圖），無法上傳本機檔案。

## 安裝與啟動

```bash
npm install
cp .env.example .env   # 填入 IG_USER_ID / IG_ACCESS_TOKEN
npm run dev             # 開發模式（自動重啟）
# 或
npm run build && npm start   # 正式環境
```

啟動後開啟 http://localhost:3000 即可使用管理介面。

## API

| Method | Path              | 說明                         |
| ------ | ----------------- | ---------------------------- |
| GET    | `/api/posts`       | 取得所有排程貼文             |
| POST   | `/api/posts`       | 新增排程貼文（imageUrl、caption、scheduledTime） |
| DELETE | `/api/posts/:id`   | 取消尚未發布或發布失敗的貼文 |

## 專案結構

```
src/
  server.ts      # Express 伺服器入口
  db.ts          # SQLite 資料層
  igClient.ts    # Instagram Graph API 串接
  scheduler.ts   # node-cron 排程引擎
  routes/posts.ts
public/
  index.html     # 管理介面
```
