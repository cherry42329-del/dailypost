# dailypost

IG 自動排程工具 ｜ IG 留言關鍵字自動回覆系統

## 這個系統做什麼

當有人在你的 Instagram 貼文底下留言時，系統會自動偵測留言內容是否包含指定關鍵字，
若有比對到，就會自動在該則留言下方回覆你預先設定好的內容。

- 留言比對：關鍵字比對（可自行編輯 `config/keywords.json`）
- 不會回覆自己帳號的留言，避免無限迴圈
- 內建 webhook 簽章驗證，避免被冒用

## 事前準備（一定要先做，不然程式碼連不上 IG）

Instagram 沒有開放個人帳號直接串接留言 API，需要透過 **Meta 開發者平台** 申請權限，步驟如下：

### 1. Instagram 帳號要是「專業帳號」

到 Instagram App → 設定 → 帳號類型與工具，把帳號切換成 **Business（商業）** 或 **Creator（創作者）** 帳號。

### 2. 綁定一個 Facebook 粉絲專頁

Instagram 專業帳號必須連結一個 Facebook 粉絲專頁（Page）。
如果還沒有，先到 Facebook 建立一個粉絲專頁，再到 Instagram 設定裡連結它。

### 3. 建立 Meta App

1. 前往 [Meta for Developers](https://developers.facebook.com/) 並登入
2. 建立新的 App，類型選擇「Business」
3. 在 App 內加入 **Instagram Graph API** 這個產品

### 4. 取得 Page Access Token

1. 到 App 的 Graph API Explorer，或使用 OAuth 流程取得權限
2. 需要申請的權限（permissions）至少包含：
   - `instagram_basic`
   - `instagram_manage_comments`
   - `pages_show_list`
   - `pages_read_engagement`
3. 用取得的使用者 token 換取「粉絲專頁」的 Page Access Token（該粉絲專頁需已連結你的 IG 帳號）
4. 建議申請「永久有效」的 Token（Long-Lived Page Access Token），一般用戶測試階段的 token 只有短期效期

> 這階段如果 App 還在「開發模式」，只有你自己（App 角色成員）能測試；
> 要正式給其他 IG 帳號使用，需要送交 Meta 的 App 審核（App Review），
> 審核 `instagram_manage_comments` 權限時需提供操作示範影片與使用情境說明。

### 5. 取得 Instagram 專業帳號 ID

可透過 Graph API 呼叫：
```
GET https://graph.facebook.com/v21.0/{page-id}?fields=instagram_business_account&access_token={page-access-token}
```
回傳的 `instagram_business_account.id` 就是 `IG_BUSINESS_ACCOUNT_ID`。

### 6. 部署本專案，取得公開 HTTPS 網址

Meta 的 Webhook 只接受公開的 HTTPS 網址（不能是 localhost）。
可以部署到 Render、Railway、Fly.io、Vercel（需改寫成 serverless handler）或自己的主機 + Nginx/HTTPS 憑證。

### 7. 到 Meta App 後台設定 Webhook

1. App 後台 → Webhooks → 選擇 Instagram
2. Callback URL 填：`https://你的網域/webhook`
3. Verify Token 填一組你自訂的字串（要跟 `.env` 裡的 `VERIFY_TOKEN` 一致）
4. 訂閱欄位（Subscription Fields）勾選 `comments`

Meta 會發送一次 GET 請求驗證你的網址，驗證成功後才能開始接收留言事件。

## 專案設定

```bash
npm install
cp .env.example .env
```

編輯 `.env`：

| 變數 | 說明 |
|---|---|
| `PORT` | 伺服器埠號，預設 3000 |
| `VERIFY_TOKEN` | 自訂字串，要跟 Meta 後台設定的一致 |
| `IG_BUSINESS_ACCOUNT_ID` | 步驟 5 取得的 IG 專業帳號 ID |
| `PAGE_ACCESS_TOKEN` | 步驟 4 取得的 Page Access Token |
| `GRAPH_API_VERSION` | Graph API 版本，預設 `v21.0` |
| `APP_SECRET` | Meta App 的 App Secret，用來驗證 webhook 請求來源，強烈建議設定 |

## 編輯自動回覆的關鍵字規則

編輯 `config/keywords.json`：

```json
{
  "rules": [
    { "keywords": ["價格", "多少錢"], "reply": "您好，詳細價格請私訊我們喔！" }
  ],
  "defaultReply": null
}
```

- 一個留言符合任一個 `keywords` 就會回覆對應的 `reply`
- 由上到下比對，符合第一條規則就停止
- `defaultReply` 設成字串的話，完全沒比對到關鍵字的留言也會回覆這則預設訊息；維持 `null` 則不回覆

修改後不用重啟伺服器，下一次留言進來就會套用新規則。

## 啟動

```bash
npm start
```

## 測試

正式串接前，可以先用假資料打自己的 `/webhook`，確認關鍵字比對邏輯正確：

```bash
curl -X POST http://localhost:3000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "123",
      "changes": [{
        "field": "comments",
        "value": { "id": "cid1", "text": "請問多少錢", "from": { "id": "999" } }
      }]
    }]
  }'
```

（本機測試若 `.env` 有設定 `APP_SECRET`，會因為缺少簽章而回 401，屬正常行為；
測試時可暫時不設 `APP_SECRET`，正式上線再設定回去。）
