# 行星力量速查表（Dignity）

> sub-agent 判斷行星力量強弱、行星間互動關係的對照表。
> API 端在 `core/vedic_constants.py` 的 EXALTATION / DEBILITATION / OWN_SIGNS / NAISARGIKA_MAITRI。

---

## 高揚 / 落陷 / 廟旺

| 行星 | 高揚（最強）| 落陷（最弱）| 廟旺 / 自宮 |
|------|------------|-------------|----------|
| Sun | 牡羊 Ari | 天秤 Lib | 獅子 Leo |
| Moon | 金牛 Tau | 天蠍 Sco | 巨蟹 Can |
| Mars | 摩羯 Cap | 巨蟹 Can | 牡羊 Ari / 天蠍 Sco |
| Mercury | 處女 Vir | 雙魚 Pis | 雙子 Gem / 處女 Vir |
| Jupiter | 巨蟹 Can | 摩羯 Cap | 射手 Sag / 雙魚 Pis |
| Venus | 雙魚 Pis | 處女 Vir | 金牛 Tau / 天秤 Lib |
| Saturn | 天秤 Lib | 牡羊 Ari | 摩羯 Cap / 水瓶 Aqu |
| Rahu | 金牛 Tau | 天蠍 Sco | 水瓶 Aqu |
| Ketu | 天蠍 Sco | 金牛 Tau | 天蠍 Sco |

**力量級別**（從強到弱）：
1. **Vargottama**（本命和 D-9 同星座）— 最強
2. **高揚**（Exaltation）— 最強表現潛力
3. **廟旺 / 自宮**（Own / Moolatrikona）— 穩定強勢
4. **友星座**（Friend's sign）— 一般強
5. **中性**（Neutral）— 普通
6. **敵星座**（Enemy's sign）— 一般弱
7. **落陷**（Debilitation）— 最弱表現潛力
8. **焦傷**（Combust）— 力量被太陽光遮蔽

---

## 行星自然友敵（Naisargika Maitri）

| 行星 | 朋友 | 中性 | 敵人 |
|------|------|------|------|
| **Sun** | Moon, Mars, Jupiter | Mercury | Venus, Saturn |
| **Moon** | Sun, Mercury | Mars, Jupiter, Venus, Saturn | （無） |
| **Mars** | Sun, Moon, Jupiter | Venus, Saturn | Mercury |
| **Mercury** | Sun, Venus | Mars, Jupiter, Saturn | Moon |
| **Jupiter** | Sun, Moon, Mars | Saturn | Mercury, Venus |
| **Venus** | Mercury, Saturn | Mars, Jupiter | Sun, Moon |
| **Saturn** | Mercury, Venus | Jupiter | Sun, Moon, Mars |

**判讀重點**：
- 行星在「朋友的星座」= 力量加分
- 行星在「敵人的星座」= 力量減分
- 廟旺 / 高揚優先於友敵判斷

**範例**：火星在金牛（金星守護的中性星座）— 力量「一般」，不算強也不算弱。

---

## 焦傷距離（Combustion Orb）

行星太靠近太陽（經度差）= 焦傷 = 力量受損。

| 行星 | 焦傷距離 | 註 |
|------|---------|---|
| Mercury | 14° | 逆行時 12° |
| Venus | 10° | 逆行時 8° |
| Mars | 17° | |
| Jupiter | 11° | |
| Saturn | 15° | |

**判讀**：焦傷的行星不能完全當「該宮位的 yoga 主角」。例如焦傷的水星即使形成 Budha-Aditya，效果大幅打折。

---

## Yoga Karaka（天然吉星）

只有 6 個上升有「天生 Yoga Karaka」— 該行星既是角宮主又是三方宮主。

| 上升 | Yoga Karaka | 守護宮位 |
|------|-----------|---------|
| 金牛 Tau | Saturn | 9 + 10 |
| 巨蟹 Can | Mars | 5 + 10 |
| 獅子 Leo | Mars | 4 + 9 |
| 天秤 Lib | Saturn | 4 + 5 |
| 摩羯 Cap | Venus | 5 + 10 |
| 水瓶 Aqu | Venus | 4 + 9 |

**意義**：該命主的 yoga karaka 行星是天然大吉星。不需要其他條件，只要這顆星不弱，就是命主的核心資源。

**範例**：天蠍上升沒有天然 yoga karaka — 必須靠後天行星組合（Raja yoga / Dhana yoga 等）。

---

## Maraka（死亡點）

### Maraka Houses
**2 / 7** 宮主在凶大限時可能成為「殺手」（對命主或重要他人）。

### Marana Karaka Sthana（行星的死亡位置）
行星在這些宮位**天生效力衰弱**（不論 dignity）：

| 行星 | 死亡位置 |
|------|---------|
| Sun | 12 宮 |
| Moon | 8 宮 |
| Mars | 7 宮 |
| Mercury | 7 宮 |
| Jupiter | 3 宮 |
| Venus | 6 宮 |
| Saturn | 1 宮 |
| Rahu | 9 宮 |
| Ketu | 6 宮 |

**注意**：「死亡位置」不是「會死」的意思，是「該行星的能量在那個位置最難發揮」。例如 Mars 在 7 宮的人，在伴侶 / 合作關係中容易感到無力或衝突。

---

## 宮位分類（Bhava 性質）

| 類型 | 宮位 | 性質 |
|------|------|------|
| **Kendra**（角宮）| 1, 4, 7, 10 | 行動的舞台 — 行星在這裡力量強且立即發揮 |
| **Trikona**（三方宮）| 1, 5, 9 | 法性與福德 — 永遠吉的宮位 |
| **Upachaya**（增長宮）| 3, 6, 10, 11 | 越老越好的宮位，凶星在此反而 OK |
| **Dushtana**（凶宮）| 6, 8, 12 | 困難領域 — 行星在此一般效力減弱 |
| **Maraka**（死亡宮）| 2, 7 | 凶大限觸發時的殺手宮 |

### 角宮 + 三方宮的特別性
- **1 宮**同時是角 + 三方 + Lagna，最強
- **角宮主 + 三方宮主合 = Raja Yoga**
- **角宮主弱 ≠ 命格弱**，要看補強

### 凶宮主的反向邏輯
- 凶宮主（6/8/12）落入凶宮 = Vipareeta Raja Yoga（凶轉吉）
- 凶宮主強反而不好 — 強化的是「敵人 / 困難 / 損失」

---

## 用法提醒

1. **dignity 不等於兌現** — 高揚 / 廟旺是「容器強」，要 Dasha 啟動才會發功
2. **D-1 落陷壓垮分盤強** — 即使 D-9 / D-10 該星廟旺，D-1 落陷會壓住整體表現
3. **判讀順序**：D-1 dignity → 友敵 → 焦傷 → Marana Karaka Sthana → Yoga Karaka 加持
