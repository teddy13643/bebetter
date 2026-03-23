import os
import json

import numpy as np
from dotenv import load_dotenv


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def _build_prompt(mode: str, question: str | None,
                  provided: list, checklist: str, data_blocks: str) -> str:
    """根據 mode 組裝不同的 LLM prompt"""

    # 各系統在不同模式下的解讀框架
    FRAMEWORK_SHARED = """
奇門遁甲：
- 日干 = 問盤人，時干 = 對方/問的事
- 八門：開/休/生=吉，死/驚/傷=凶，杜=封閉，景=中看不中用
- 值符+值使門 = 整盤主旋律
- 空亡 = 該元素「懸空」，能量不實際

大六壬：
- 三傳 = 初傳(開頭) → 中傳(過程) → 末傳(結局)
- 六親：財=對象/錢，官=正式關係/工作，兄=競爭/阻礙，父=長輩/約束，子=想法/計劃
- 天將：青龍=最吉，玄武=曖昧，白虎=壓力，天后=感情

太乙神數：
- 主算 vs 客算 = 你 vs 對方/環境的資源（直接比大小）
- 主將/客將 = 王牌，主參/客參 = 後援
- 三才足數 = 天時地利人和齊全；無天=沒想清楚，無地=根基不穩
- 君基=理智，臣基=執行力，民基=身體

梅花易數：
- 本卦 = 格局，互卦 = 隱藏特質，變卦 = 發展方向
- 體 = 你的本質，用 = 你面對的對象/環境
- 體用關係：用生體=有助力，體剋用=有掌控力，用剋體=有壓力，體生用=付出型，比和=穩定

八字：
- 日主 = 核心（五行+陰陽=基本性格）
- 十神 = 角色分配（正官=規矩、七殺=壓力爆發、食神=才華、傷官=叛逆創意、正印=貴人、偏印=偏門技能、正財=穩定、偏財=意外、比肩=同儕、劫財=競爭）
- 五行分布 = 多的是天賦/資源，少的是缺乏的

西洋占星（回歸黃道）：
- 太陽 = 核心自我，月亮 = 情感需求，上升(第1宮) = 外在形象
- 宮位 = 人生哪個領域被啟動
- 逆行 = 該領域需要重新審視

印度占星（恆星黃道）：
- 月亮星座比太陽更重要
- 與西洋占星交叉比對，兩邊都強調的主題 = 高度確定
"""

    if mode == "natal":
        context = """## 模式：本命解讀（認識自己）

這是此人出生時刻排出的盤，目的是分析其天生格局、性格特質、人生主題。

各系統的本命解讀角度：
- 奇門遁甲 — 天生的行動模式與決策風格
- 大六壬 — 人生劇本的基調（三傳=人生三階段的主題）
- 太乙神數 — 天生的資源條件與大環境對你的態度
- 梅花易數 — 天生體質：本卦=原廠設定，互卦=中年後浮現的隱藏面，變卦=後天發展方向，動爻=人生關鍵轉變點
- 八字 — 先天五行體質與命格結構
- 西洋占星 — 性格藍圖與人生主題
- 印度占星 — 業力模式與命定傾向"""

        steps = """## 解讀步驟（請嚴格按順序執行）

### 步驟一：逐盤摘要
對每個提供的系統，各用 2-3 句話提取關鍵發現。

### 步驟二：交叉比對
1. **共識**：多個系統指向同一方向的結論（標註來源）
2. **獨特洞察**：只有某個系統看到的重要資訊
3. **矛盾**：系統之間說法不同時，指出來並分析

### 步驟三：統整解讀

#### 一、你的原廠設定
綜合所有盤，描繪這個人天生是什麼樣的人 — 性格、能量、行為模式。

#### 二、天生的優勢與資源
哪些能力和機運是與生俱來的？多個盤都指向的=高度確定。

#### 三、天生的挑戰與功課
人生容易卡在哪裡？要修煉什麼？

#### 四、人生主題與發展方向
大六壬三傳的人生故事線 + 梅花變卦的發展方向 + 占星的宮位主題。

#### 五、給你的提醒
表格格式，每條標註來源：
| 提醒 | 來源 |
| --- | --- |"""

    else:
        question_line = f"\n問盤人的問題是：「{question}」\n" if question else ""
        context = f"""## 模式：問事解讀（起卦占卜）

這是問事當下時刻排出的盤，目的是分析事件的走向與建議。
{question_line}
各系統的問事解讀角度：
- 奇門遁甲 — 行動策略與時機，該不該動、怎麼動
- 大六壬 — 事件發展的故事線（開頭→過程→結局）
- 太乙神數 — 力量對比與大勢，主導權在誰手上
- 梅花易數 — 事情的體用關係：體=問盤人，用=問的事/對方
- 八字 — 問事時刻的氣場狀態，當下的能量配置
- 西洋占星 — 卜卦占星（Horary），行星配置反映事件狀態
- 印度占星 — Prashna（卜問），業力層面的事件指引"""

        steps = """## 解讀步驟（請嚴格按順序執行）

### 步驟一：逐盤摘要
對每個提供的系統，各用 2-3 句話提取關鍵發現。

### 步驟二：交叉比對
1. **共識**：多個系統指向同一方向的結論（標註來源）
2. **獨特洞察**：只有某個系統看到的重要資訊
3. **矛盾**：系統之間說法不同時，指出來並分析誰更可信

### 步驟三：統整解讀

#### 一、你是誰、你現在的狀態
綜合所有盤對「你」的描述，用一段話畫出一幅畫面。

#### 二、力量對比
太乙的數字（主算 vs 客算）+ 其他盤的佐證。
明確告訴問盤人：「主導權在你」或「勢均力敵」或「對方條件比你好」。

#### 三、發展過程與阻力
大六壬三傳的故事線為主軸，其他盤的補充。
標明阻力在「過程」還是「結局」。過程中的阻力要說「這會過去」。

#### 四、最終走向
各盤結局指標的共識。如果多盤一致，強調可信度。

#### 五、具體建議
表格格式，每條標註來源：
| 建議 | 來源 |
| --- | --- |"""

    mode_label = "本命" if mode == "natal" else "問事"
    return f"""你是一位同時精通奇門遁甲、大六壬、太乙神數、梅花易數、八字命理、西洋占星、印度占星的命理師。

本次是「{mode_label}」模式，提供了以下 {len(provided)} 個系統的盤：{checklist}。
你必須在解讀中引用每一個系統，不可跳過。

{context}

---

以下是排出的盤：

{data_blocks}

---

## 各系統看什麼（解讀框架）
{FRAMEWORK_SHARED}

---

{steps}

---

## 解讀立場
- 站在問盤人這邊，幫他看清局勢
- 有優勢時講「你有底氣、有選擇權」
- 建議以保護問盤人的利益為出發點

## 風格要求
- 繁體中文，白話文為主，術語用括號附註
- 每個概念翻成生活場景，讓不懂命理的人也能秒懂
- 語氣像有智慧的朋友聊天：溫暖但直接
- 不用軍事用語（戰力、兵力等）
- 占星部分簡述太陽/月亮/上升組合，不逐一列行星
- 只解讀有提供的盤，沒提供的不提

## 字數
步驟一（逐盤摘要）：不限，確保完整
步驟二（交叉比對）：不限，確保完整
步驟三（統整解讀）：800-1500 字，精煉不囉嗦"""


def interpret(qimen_data: dict, liuren_data: dict, taiyi_data: dict,
              meihua_data: dict = None, bazi_data: dict = None,
              western_data: dict = None, vedic_data: dict = None,
              mode: str = "horary", question: str = None) -> str:
    """用 LLM 做多式合參解讀。mode: natal=本命解讀, horary=問事解讀"""
    from openai import OpenAI

    load_dotenv()

    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        return "未設定 LLM_API_KEY，無法產生 AI 解讀"

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
    )

    # 組裝各盤 JSON
    sections = [
        ("奇門遁甲盤", qimen_data),
        ("大六壬盤", liuren_data),
        ("太乙神數盤", taiyi_data),
        ("梅花易數盤", meihua_data),
        ("八字命盤", bazi_data),
        ("西洋占星盤（回歸黃道）", western_data),
        ("印度占星盤（恆星黃道）", vedic_data),
    ]
    data_blocks = "\n\n".join(
        f"## {name}\n{json.dumps(data, ensure_ascii=False, cls=NpEncoder) if data else '（未提供）'}"
        for name, data in sections
    )

    # 動態列出有提供的盤名，讓 LLM 知道自己要涵蓋哪些
    provided = [name for name, data in sections if data]
    checklist = "、".join(provided)

    prompt = _build_prompt(mode, question, provided, checklist, data_blocks)

    model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=3000,
    )

    return response.choices[0].message.content
