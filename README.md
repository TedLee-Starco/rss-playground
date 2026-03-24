# YT Tracker

自動追蹤 YouTube 頻道新影片，並發送通知到 Discord。部署在 Cloudflare Workers，每 5 分鐘自動執行一次。

## 功能

- 追蹤多個 YouTube 頻道
- 有新影片時自動發送 Discord 通知（含 @everyone）
- 自動過濾 Shorts（≤ 120 秒的影片不通知）
- 每個頻道可設定不同的 Discord Webhook
- 每個頻道可自訂通知文字
- 可自動擷取影片 description 內的連結（支援前綴過濾）

## 專案結構

```
├── src/index.ts          # Cloudflare Worker 主程式
├── channels.json         # 追蹤的頻道設定
├── scripts/
│   └── get_description.py  # 取得影片描述的本地工具腳本
├── wrangler.toml         # Cloudflare Worker 設定
└── .dev.vars             # 本地開發用環境變數（不 commit）
```

## 設定

### channels.json

新增或移除頻道只需編輯此檔案，修改後重新部署即可。

```json
[
  {
    "id": "UCxxxxxxxxxxxxxxx",
    "name": "頻道顯示名稱",
    "webhookKey": "STRATEGY_WEBHOOK",
    "message": "自訂通知文字",
    "showDescriptionUrls": true,
    "descriptionUrlFilter": "https://link.clashofclans.com/en/"
  }
]
```

| 欄位 | 必填 | 說明 |
|------|------|------|
| `id` | ✅ | YouTube 頻道 ID（`UC` 開頭） |
| `name` | ✅ | 顯示名稱 |
| `webhookKey` | ✅ | 對應 Cloudflare Secret 的名稱（如 `STRATEGY_WEBHOOK`） |
| `message` | | 自訂通知文字，預設為 `各位成員快去學習新打法新戰術` |
| `showDescriptionUrls` | | 是否附上影片 description 的連結，預設 `false` |
| `descriptionUrlFilter` | | 搭配 `showDescriptionUrls`，只保留指定前綴的連結 |

**取得頻道 ID：** 頻道 URL 若為 `youtube.com/channel/UCxxxxxx` 可直接複製；若為 `@username` 格式，可用以下指令查詢：
```bash
curl "https://www.googleapis.com/youtube/v3/channels?part=id&forHandle=USERNAME&key=YOUR_API_KEY"
```

## 部署

### 首次部署

**1. 安裝依賴**
```bash
npm install
```

**2. 建立 KV namespace**
```bash
npx wrangler kv namespace create STATE
# 將回傳的 id 填入 wrangler.toml 的 [[kv_namespaces]] id 欄位
```

**3. 設定 Secrets**
```bash
npx wrangler secret put YOUTUBE_API_KEY   # YouTube Data API v3 Key
npx wrangler secret put STRATEGY_WEBHOOK         # Discord Webhook URL（對應 channels.json 的 webhookKey）
npx wrangler secret put BASE_WEBHOOK         # 第二個 Discord Webhook URL（如有）
npx wrangler secret put CHANNEL_WEBHOOK
```

**4. 開通 workers.dev subdomain（一次性）**

前往 Cloudflare Dashboard → Workers，進入頁面後會自動建立 subdomain。

**5. 部署**
```bash
npm run deploy
```

### 日後更新頻道

編輯 `channels.json` 後重新部署：
```bash
npm run deploy
```

## 本地測試

建立 `.dev.vars`：
```
YOUTUBE_API_KEY=AIza...
STRATEGY_WEBHOOK=https://discord.com/api/webhooks/...
BASE_WEBHOOK=https://discord.com/api/webhooks/...
CHANNEL_WEBHOOK=https://discord.com/api/webhooks/...
```

啟動本地 dev server：
```bash
npx wrangler dev --test-scheduled
```

在另一個 terminal 觸發測試：
```bash
# 指定頻道（只對該頻道發送通知）
curl "http://localhost:8787/seed-test?name=LegendClashLover"

# 所有頻道
curl "http://localhost:8787/seed-test"

# 觸發 cron
curl "http://localhost:8787/__scheduled"
```

## 工具腳本

取得指定影片的 description：
```bash
# 在 .env 設定 YOUTUBE_API_KEY=AIza...
uv run python scripts/get_description.py <video_id>
```
