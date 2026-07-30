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

### ⚠️ 費用與額度提醒

這是「不指定單一目的地、從候選城市清單裡找最佳選項」的搜尋方式,呼叫量會隨目的地數量與每個
目的地嘗試的日期組合數增加。Google Flights 來回票查詢在 SerpApi 需要 2 次 API 呼叫(去程 + 回程)。
以預設設定(約23個目的地 x 每個目的地最多3組日期 x 2個梯次 x 每天2次)估算,**每天可能消耗數百次
SerpApi 查詢**,遠超過 SerpApi 免費方案的 100 次/月額度,需要訂閱付費方案
(參考 [SerpApi 定價](https://serpapi.com/pricing))。

若想降低費用,可以調整 `config.yaml` 中的:
- `destinations`:減少候選目的地數量
- `max_date_combos_per_destination`:減少每個目的地嘗試的日期組合數
- 或修改 `.github/workflows/flight-monitor.yml` 的 cron,改成一天檢查1次

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

### 已知限制

- Google Flights 沒有提供可直接帶入航班資料的「航空公司官網深層連結」,`airline_booking_url`
  只會連到官網首頁,需自行輸入日期查詢。
- 監控日期(2027年)距離現在較遠,許多航空公司(尤其傳統航空)的航班時刻表要提前約
  11-12個月才會開放訂票,初期可能會持續收到「本次未找到符合條件的選項」的通知,屬正常現象。
