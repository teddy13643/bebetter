---
description: 印度占星人生諮詢 — 用 Vedic 盤面回答具體人生問題（事業、感情、財務、健康、學習、修行、前世、買房、活動），給時間軸和行動建議
tags: [personal, product, bebetter]
examples:
  - "/bb-vedic 1990-06-15 12:00 台北 工作 感情 財務 官司"
  - "/bb-vedic 1988 5 27 05:30 台南 適合創業嗎 何時跳槽"
  - "/bb-vedic 1995 3 8 14:00 高雄 感情 要主動還是等"
  - "/bb-vedic 1990 8 15 10:00 台北 學習 進修 適合考研所嗎"
  - "/bb-vedic 1985 12 3 21:00 台中 健康 要動手術嗎 體質怎樣"
  - "/bb-vedic 1992 2 20 06:30 高雄 前世 靈性修行 命格走向"
  - "/bb-vedic 1993 7 7 18:00 桃園 買房 換工作 何時最佳"
  - "/bb-vedic 1990 6 15 12:00 台北 命理 side project 能不能變現 何時生小孩"
  - "/bb-vedic 1988 9 15 11:00 台南 跟父母關係 要不要照顧長輩 家族業力"
  - "/bb-vedic 2027 事業"
---

需要 `year/month/day/hour/minute/address` + `questions`，可選 `target_year`（預設今年）或 `target_date`（YYYY-MM-DD，給了走流日模式）。缺必要欄位就問。

**模式判斷**：用戶問「今天」「明天」「N 月 N 日」等具體單日 → 走流日模式（傳 `target_date`，不傳 `target_year`）。問「今年」「2027」「明年」等年層級 → 走流年模式（傳 `target_year`）。

### 已存生辰優先用本檔

skill 自帶生辰存檔：`.claude/skills/bb-vedic/data/birth-profile.json`，結構：

```json
{
  "main": {"year": 1990, "month": 6, "day": 15, "hour": 12, "minute": 0, "address": "台北", "note": "範例", "resolved_lat": 25.0330, "resolved_lng": 121.5654},
  "<key>": { ... 其他人的生辰 }
}
```

**呼叫流程**：

1. 用戶只給 questions 沒給生辰 → `cat .claude/skills/bb-vedic/data/birth-profile.json` 取 `main` 欄位直接用，不要問
2. 用戶給了**新的人**（明說「我朋友」「我媽」等）或新的生辰參數 → 解析後**寫進 birth-profile.json** 對應 key（用戶沒指定 key 時用 `main`，會覆蓋）
3. 檔案不存在或 `main` 缺欄位 → 才向用戶問

寫入時用 `python3 -c "import json; ..."` 或 `jq` 安全更新，不要用 echo 覆蓋整檔。

API 有兩層快取：本命盤永久快取（含 17 張分盤、同一人的盤永不變）、流年行運年度快取。第一次呼叫 ~3-5 秒（計算 + 存檔），之後命中快取 < 0.1 秒。檔案落在 `cache/vedic/natal/{profile_key}_{hash}.json` 和 `cache/vedic/transit/{profile_key}_{hash}_{year}.json`，profile_key 帶進去就可以肉眼分辨是誰的盤。本檔只存 input（生辰 + 出生地 + resolved 經緯度），不存盤面摘要。

### 參數標準化

解析用戶輸入後，先轉換為標準格式再往下傳：

| 輸入 | 處理 |
|------|------|
| 民國年（年份 ≤ 130） | 加 1911 → 西元 |
| 西元年（年份 1900-2100） | 直接用 |
| 介於 131-1899 的年份 | 必問澄清，不猜 |
| 「下午兩點半」 | 14:30 |
| 「凌晨三點」 | 03:00 |
| 「兩點」（未指 AM/PM） | 必問或依上下文判斷 |
| 缺分鐘（如「兩點」） | 補 00（02:00 或 14:00） |

### questions 解析

從使用者輸入中識別問題意圖。**對應的 framework 由 sub-agent 依 `references/guide.md` 內表自動載入**，主對話只需把 questions 字串原樣傳下去。

| 關鍵字 | 類別 |
|--------|------|
| 工作、跳槽、離職、面試、創業、升職 | 事業 |
| 學習、進修、考試、留學、考研 | 學習 |
| 感情、交往、結婚、追人、被追、分手 | 感情 |
| 財務、投資、年終、加薪、收入 | 財運 |
| 買房、貸款、不動產、房產 | 居住 |
| 搬家、裝修、租屋 | 居住 |
| 官司、合約、糾紛、訴訟 | 法律 |
| 健康、體質、心理 | 健康 |
| 開刀、手術 | 健康 |
| 運動、鍛鍊、訓練 | 活動 |
| 社團、舞蹈、興趣、副業、樂器 | 活動 |
| 主動 vs 被動、何時、幾月、時機 | 時機 |
| 修行、冥想、玄學 | 靈性 |
| 前世、業力、命格走向、靈魂 | 前世 |
| 創作、IP、商品、課程、side project、子女、生育 | 創造 |
| 父母、家人、家族、繼承、祖傳、照顧長輩 | 家庭 |

問題模糊時不問確認，用最常見的解讀方向。

### Phase 1：取資料（主對話 Bash）

一次 CLI 拿完整資料（vedic-transit 已合併 natal + transit）：

```bash
TS=$(date +%s)
DATA="/tmp/bb_vedic_${TS}.json"
BB=/Users/teddy13643/Documents/workspace/personal/bebetter/bebetter

# 有 resolved_lat/lng 就傳 --lat/--lng（跳過 geocode），沒有才傳 --address
# --profile-key 帶當前用的 birth-profile key（main / friend-alice...），會出現在快取檔名上肉眼可辨
# 流年模式：傳 --target-year + --forecast-years
"$BB" vedic-transit --year {Y} --month {M} --day {D} --hour {h} --minute {m} \
  --lat {LAT} --lng {LNG} --target-year {TY} --forecast-years 1 \
  --profile-key {KEY} > "$DATA"

# 流日模式：傳 --target-date（YYYY-MM-DD），不傳 --target-year/--forecast-years
# response 會多 "流日" 欄位（含當天 9 行星），但不會有「逐年分析」「行星換座事件」
"$BB" vedic-transit --year {Y} --month {M} --day {D} --hour {h} --minute {m} \
  --lat {LAT} --lng {LNG} --target-date 2026-05-07 \
  --profile-key {KEY} > "$DATA"

# 驗證
SIZE=$(wc -c < "$DATA")
VALID=$(jq '.' "$DATA" >/dev/null 2>&1 && echo yes || echo no)
ERR=$(jq -r '.detail // "none"' "$DATA" 2>/dev/null)
echo "data: $DATA size=$SIZE bytes valid=$VALID error=$ERR"
```

**首次呼叫某人**（profile 沒有 `resolved_lat`/`resolved_lng`）：用 `address` 呼叫 API，成功後從 response 的 `resolved_coords` 寫回 profile：

```bash
# API response 頂層有 resolved_coords.lat / resolved_coords.lng
jq -r '.resolved_coords | "\(.lat) \(.lng)"' "$DATA"
# 用 jq 寫回 birth-profile.json
jq --argjson lat "$(jq '.resolved_coords.lat' "$DATA")" \
   --argjson lng "$(jq '.resolved_coords.lng' "$DATA")" \
   '.main.resolved_lat = $lat | .main.resolved_lng = $lng' \
   .claude/skills/bb-vedic/data/birth-profile.json > /tmp/bp.json \
   && mv /tmp/bp.json .claude/skills/bb-vedic/data/birth-profile.json
```

**驗證通過**（valid=yes、error=none、size > 10000）→ 進 Phase 2，把 `$DATA` 路徑傳給 sub-agent。

**失敗時的處理**：

| 錯誤 | 解決方式 |
|------|---------|
| `找不到地址` | 改傳更具體地址（加區 / 加國家），或改傳經緯度 `lat/lng` |
| `請檢查生辰參數` | 跟用戶確認年月日時是否正確 |
| size < 1000 | API 沒回完整 JSON，可能是 nominatim 超時，重跑一次 |
| HTTP 500 | API 內部錯誤，停止並告訴用戶 |

### Phase 2：寫報告（opus, maxTurns: 8）

發一個 sub-agent（model: opus），prompt：

```
Read .claude/skills/bb-vedic/references/guide.md 並照做。
依 questions 載入對應的 frameworks/*.md（guide 內有對照表）。
資料在 {DATA_PATH}，直接 cat 讀取。
questions="{QUESTIONS}" target_year={TY}  # 流日模式時改傳 target_date={YYYY-MM-DD}
```

**流日模式提示 sub-agent**：資料只有「流日」欄位（沒有「逐年分析」），解讀重點放在當天 9 行星位置 + nakshatra 27 宿 + 從本命月亮/上升起算的宮位 + dignity + 逆行，搭配 dasha「目前」推當天適合做什麼、避免什麼。**擇日類問題（手術 / 簽約 / 結婚 / 出行）必看 transit 月亮的 nakshatra 主題**（如 Ashwini = 醫療日、Pushya = 開始日、Mula = 拔除日），且要交叉 nakshatra lord 跟 dasha 主星是否對齊（對齊 = 訊號放大）。

回傳的 markdown 直接呈現，不要改寫、不要重組、不要追問細節。
