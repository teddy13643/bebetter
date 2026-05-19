---
description: 西洋占星本命 + 年運商品 — 幫客人認識自己、給出實際可用的生活建議
tags: [personal, product, bebetter]
examples:
  - "/bb-astro 1990-06-15 12:00 台北"
  - "/bb-astro 1988 5 27 05:30 女 台南 2026"
---

需要 `year/month/day/hour/minute/address`，可選 `gender`、`target_year`（預設今年）。缺必要欄位就問。

### 參數標準化

解析用戶輸入後，先轉換為標準格式再往下傳：

- 民國年 → 西元（加 1911）
- 時間口語 → 24 小時制（「下午兩點半」→ 14:30、「凌晨三點」→ 03:00）
- 缺分鐘 → 補 00（「兩點」→ 依上下文判斷 02:00 或 14:00）

### Phase 1：取資料（主對話 Bash）

直接在主對話用一次 Bash call 完成 CLI + jq + 驗證：

```bash
BB=/Users/teddy13643/Documents/workspace/personal/bebetter/bebetter

"$BB" astro-natal --year {Y} --month {M} --day {D} --hour {h} --minute {m} --address "{ADDR}" \
  > /tmp/bb_natal.json &

"$BB" astro-transit --year {Y} --month {M} --day {D} --hour {h} --minute {m} --address "{ADDR}" \
  --target-year {TY} --forecast-years 1 \
  | jq '{"外行星行運": [.["外行星行運"][] | select(.["重要性"] >= 6)], "逆行衝擊": .["逆行衝擊"], "次限推運": .["次限推運"], "小限法": .["小限法"], "太陽回歸": .["太陽回歸"], "年度總覽": .["年度總覽"]}' > /tmp/bb_transit.json &

wait

# 驗證
echo "natal: $(wc -c < /tmp/bb_natal.json) bytes, valid=$(jq '.' /tmp/bb_natal.json >/dev/null 2>&1 && echo yes || echo no), error=$(jq 'has(\"error\")' /tmp/bb_natal.json 2>/dev/null)"
echo "transit: $(wc -c < /tmp/bb_transit.json) bytes, valid=$(jq '.' /tmp/bb_transit.json >/dev/null 2>&1 && echo yes || echo no), error=$(jq 'has(\"error\")' /tmp/bb_transit.json 2>/dev/null)"
```

驗證通過（兩個都 valid=yes、error=false、非空）→ 進 Phase 2。任一失敗 → 停止，告訴用戶。

### Phase 2：寫報告（opus, maxTurns: 8）

發一個 sub-agent（model: opus），prompt：

```
Read .claude/skills/bb-astro/references/guide.md 並照做。
資料已在 /tmp/bb_natal.json 和 /tmp/bb_transit.json，直接讀取。
gender="{G}" target_year={TY}
```

回傳的 markdown 直接呈現，不要改寫、不要重組、不要追問細節。
