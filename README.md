# dailypost

IG 自動排程工具 ｜ IG 留言關鍵字自動回覆系統

---

## IG 留言關鍵字自動回覆系統

### 這個系統做什麼

當有人在你的 Instagram 貼文底下留言時，系統會自動偵測留言內容是否包含指定關鍵字，
若有比對到，就會自動在該則留言下方回覆你預先設定好的內容。

- 留言比對：關鍵字比對（可自行編輯 `config/keywords.json`）
- 不會回覆自己帳號的留言，避免無限迴圈
- 內建 webhook 簽章驗證，避免被冒用
- 同一位留言者在冷卻時間內只會被回覆一次，避免被洗版留言拖垮或觸發 IG 的異常行為偵測

### 事前準備（一定要先做，不然程式碼連不上 IG）

Instagram 沒有開放個人帳號直接串接留言 API，需要透過 **Meta 開發者平台** 申請權限，步驟如下：

#### 1. Instagram 帳號要是「專業帳號」

到 Instagram App → 設定 → 帳號類型與工具，把帳號切換成 **Business（商業）** 或 **Creator（創作者）** 帳號。

#### 2. 綁定一個 Facebook 粉絲專頁

Instagram 專業帳號必須連結一個 Facebook 粉絲專頁（Page）。
如果還沒有，先到 Facebook 建立一個粉絲專頁，再到 Instagram 設定裡連結它。

#### 3. 建立 Meta App

1. 前往 [Meta for Developers](https://developers.facebook.com/) 並登入
2. 建立新的 App，類型選擇「Business」
3. 在 App 內加入 **Instagram Graph API** 這個產品

#### 4. 取得 Page Access Token

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

#### 5. 取得 Instagram 專業帳號 ID

可透過 Graph API 呼叫：
```
GET https://graph.facebook.com/v21.0/{page-id}?fields=instagram_business_account&access_token={page-access-token}
```
回傳的 `instagram_business_account.id` 就是 `IG_BUSINESS_ACCOUNT_ID`。

#### 6. 部署本專案，取得公開 HTTPS 網址

Meta 的 Webhook 只接受公開的 HTTPS 網址（不能是 localhost）。
本專案已附上 `render.yaml`，推薦部署到 [Render](https://render.com)，步驟如下：

1. 到 [render.com](https://render.com) 註冊帳號（可用 GitHub 帳號登入）
2. 儀表板選 **New +** → **Blueprint**，選擇這個 GitHub repository（`dailypost`）
3. Render 會讀到 `render.yaml`，自動帶入 Build Command（`npm install`）與 Start Command（`npm start`）
4. 部署前它會請你填入標記 `sync: false` 的環境變數，也就是：
   - `VERIFY_TOKEN`
   - `IG_BUSINESS_ACCOUNT_ID`
   - `PAGE_ACCESS_TOKEN`
   - `APP_SECRET`

   這幾個是機密資料，不會存在程式碼或 GitHub 上，只存在 Render 的環境變數設定裡。
5. 按下部署，等待建置完成後，會拿到一個網址，例如 `https://dailypost-ig-autoreply.onrender.com`
6. 這個網址加上 `/webhook`（例如 `https://dailypost-ig-autoreply.onrender.com/webhook`）就是下一步要填給 Meta 的 Callback URL

> **免費方案會在沒有流量時自動休眠**，休眠後第一個請求要等 30~50 秒才會醒來，
> 期間如果剛好有留言進來，可能會因為 Meta 等待逾時而錯過那則自動回覆。
> 測試階段用免費方案沒問題；正式上線建議升級到付費方案（Starter，約 US$7/月），讓服務保持常駐、不休眠。

如果不想用 Render，也可以部署到 Railway、Fly.io，或自己的主機 + Nginx/HTTPS 憑證，原理都一樣：需要一個能公開存取的 HTTPS 網址指到這個 Express 伺服器。

#### 7. 到 Meta App 後台設定 Webhook

1. App 後台 → Webhooks → 選擇 Instagram
2. Callback URL 填：`https://你的網域/webhook`
3. Verify Token 填一組你自訂的字串（要跟 `.env` 裡的 `VERIFY_TOKEN` 一致）
4. 訂閱欄位（Subscription Fields）勾選 `comments`

Meta 會發送一次 GET 請求驗證你的網址，驗證成功後才能開始接收留言事件。

### 專案設定

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
| `COOLDOWN_MINUTES` | 同一位留言者幾分鐘內只回覆一次，預設 10 分鐘 |

### 編輯自動回覆的關鍵字規則

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

> 冷卻機制的紀錄目前存在記憶體中，伺服器重啟會清空，多台伺服器實例部署時也不會互相同步，
> 這對單一小規模部署已經足夠；未來若要多實例水平擴展，建議改存到 Redis 之類的共用儲存。

### 啟動

```bash
npm start
```

### 測試

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

---

## ✈️ 機票監控系統

自動監控桃園(TPE)出發、直飛、4-7天行程、來回票價 NT$4,000-18,000 的機票,
每天台灣時間 10:00 / 20:00 檢查一次,篩選出目前最佳的前3個目的地選項,並透過 LINE 推播通知。

### 運作方式

| 環節 | 使用服務 | 說明 |
|---|---|---|
| 機票資料 | [SerpApi Google Flights API](https://serpapi.com/google-flights-api) | 查詢直飛來回票價、航班時刻、Google Flights 連結 |
| 天氣估算 | [Open-Meteo Archive API](https://open-meteo.com/en/docs/historical-weather-api)(免費、免金鑰) | 用過去5年同期歷史氣象平均值估計「典型天氣」,僅供參考 |
| 推播 | [LINE Messaging API](https://developers.line.biz/en/docs/messaging-api/) | LINE Notify 已於2025年停止服務,改用 Messaging API 的 push/broadcast |
| 排程 | GitHub Actions | `.github/workflows/flight-monitor.yml`,cron 對應台灣時間 10:00/20:00 |

監控的日期區間、預算、目的地清單都可以直接編輯 [`config.yaml`](./config.yaml)。

### ⚠️ 費用與額度提醒 / 免費方案模式

這是「不指定單一目的地、從候選城市清單裡找最佳選項」的搜尋方式,呼叫量會隨目的地數量與每個
目的地嘗試的日期組合數增加,而 Google Flights 來回票查詢在 SerpApi 每組都要 2 次 API 呼叫
(去程 token + 回程 token)。若每次執行都把所有目的地、所有日期組合查一遍,一天內就會用掉數百次
額度,遠超過 SerpApi 免費方案的 **100 次/月**。

**`config.yaml` 預設已經啟用 `free_tier.enabled: true`,把「推播頻率」跟「實際刷新價格頻率」拆開:**

- 通知依然是台灣時間 **10:00 / 20:00 各推播一次**,滿足「一天檢查2次」的需求
- 但只有 **10:00 那次**會真的呼叫 SerpApi 刷新價格(20:00 那次用 `--no-refresh`,只重送快取內容,不佔額度)
- 每次刷新只**輪流**更新其中 `free_tier.max_searches_per_month ÷ free_tier.refresh_runs_per_month ÷ 2`
  個(梯次, 目的地)組合(預設算出來是 1 組),其餘沿用上次查到的價格
- 查到的價格會存進 [`data/price_cache.json`](./data/price_cache.json),並由 workflow 自動提交回這個分支,
  讓進度可以延續到下次執行
- 通知內容會附註「資料更新於 X 天前」,讓你知道這筆價格的新鮮度

以預設值(90次/月額度、每天1次刷新機會)估算,實際每月約消耗 **60次** SerpApi 查詢,在 100次免費
額度內還有餘裕。代價是候選目的地清單(約23個 x 2個梯次 = 46組)完整輪過一輪大約需要 **一個半月**,
也就是同一個目的地的價格大概每 4-6 週才會更新一次——但因為監控的是 7-9 個月後的機票,價格本來
就不會逐日劇烈變動,這個更新頻率是合理的取捨。

如果你升級了 SerpApi 付費方案,想要更即時、更全面的比較,把 `config.yaml` 的
`free_tier.enabled` 設為 `false` 即可,系統會改回「每次都完整查詢所有目的地與日期組合」的原始模式
(此時 `max_date_combos_per_destination` 才會生效)。也可以調整:
- `free_tier.max_searches_per_month`:依你的 SerpApi 方案額度調整(系統會自動換算每次刷新幾組)
- `destinations`:減少候選目的地數量,加快輪完一輪的速度
- `.github/workflows/flight-monitor.yml` 的 cron:改變檢查次數/時間

### 設定步驟

1. **取得 SerpApi 金鑰**:至 [serpapi.com](https://serpapi.com/) 註冊帳號,在 dashboard 取得 API Key。
2. **建立 LINE Messaging API 官方帳號**:
   - 到 [LINE Developers Console](https://developers.line.biz/console/) 建立 Provider 與 Messaging API channel
   - 在 channel 設定頁取得 **Channel access token(long-lived)**
   - 用手機 LINE 掃描該官方帳號的 QR code,加它為好友(這樣才收得到 broadcast 推播)
   - (選填)若只想推給自己一人而非所有好友,可在 channel 設定的 Webhook 中取得你的 `userId`,
     填入 `LINE_USER_ID`;不填則預設用 broadcast 推給所有好友。
3. **設定 GitHub Actions Secrets**(Repo Settings → Secrets and variables → Actions):
   - `SERPAPI_API_KEY`
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_USER_ID`(選填)
4. **依需求調整 `config.yaml`**(監控日期、預算、目的地清單等)。
5. Push 到此分支後,GitHub Actions 會依排程自動執行;也可以到 Actions 頁面手動觸發
   (workflow_dispatch)先測試一次。

### 本機測試(不需要任何金鑰)

```bash
pip install -r requirements.txt
python -m flight_monitor.main --mock
```

`--mock` 模式會用假資料跑完整流程並印出訊息格式,不會呼叫 SerpApi / Open-Meteo / LINE,
方便確認訊息格式與程式邏輯是否正確。

若已設定好金鑰但只想看查詢結果、不實際推播,可用:

```bash
python -m flight_monitor.main --no-notify
```

免費方案模式下,若只想測試「用快取資料組訊息、不刷新價格」的流程(對應 20:00 那次執行):

```bash
python -m flight_monitor.main --no-notify --no-refresh
```

### 已知限制

- Google Flights 沒有提供可直接帶入航班資料的「航空公司官網深層連結」,`airline_booking_url`
  只會連到官網首頁,需自行輸入日期查詢。
- 監控日期(2027年)距離現在較遠,許多航空公司(尤其傳統航空)的航班時刻表要提前約
  11-12個月才會開放訂票,初期可能會持續收到「本次未找到符合條件的選項」的通知,屬正常現象。
