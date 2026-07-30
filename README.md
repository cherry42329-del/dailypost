# dailypost
IG自動排程工具

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
