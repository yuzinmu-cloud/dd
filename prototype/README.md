# AIGMOS Demo v0.6

## 版本

v0.6

## 狀態

可遊玩的本機離線 AI GM 文字原型

## 目的

這個原型用來驗證 AIGMOS 的本機單人文字冒險循環。玩家可以用繁體中文自然語言輸入行動，系統會用最小 AI Judge 判斷行動合理性與是否需要擲骰，再把目前場景、狀態、Judge 結果與骰子結果交給本機 AI GM 回應。

v0.6 的重點是讓 AI GM 回覆拆成兩段：玩家可見敘事，以及內部 structured update JSON。JSON 通過驗證後才會更新 GameState；如果 AI 輸出壞掉、缺少 JSON 或格式不合法，系統會改用保守的 `state_update.py` fallback，避免遊戲崩潰或狀態完全漏記。

目前版本預設使用 Ollama 本機模型，不需要 OpenAI API key，也不需要網路連線。

冒險內容基於 MVP 前提：《燭芯礦坑事件》。

## 安裝 Ollama

請先安裝 Ollama：

https://ollama.com

安裝後，先下載並啟動預設模型：

```bash
ollama run qwen2.5:7b
```

原型會呼叫本機 API：

```text
http://localhost:11434/api/generate
```

如果 Ollama 沒有啟動，遊戲會顯示：

```text
無法連接本機 AI。請確認 Ollama 已啟動，並已安裝模型。
```

如果模型不存在，遊戲會提示：

```text
找不到指定模型。請先執行：ollama run qwen2.5:7b
```

## 可選模型設定

預設模型是：

```text
qwen2.5:7b
```

可以用環境變數覆蓋：

PowerShell：

```powershell
$env:AIGMOS_LOCAL_MODEL="你的模型名稱"
```

macOS / Linux：

```bash
export AIGMOS_LOCAL_MODEL="你的模型名稱"
```

## 如何啟動遊戲

請在 repository 根目錄執行：

```bash
python prototype/main.py
```

## 可用指令

英文與中文指令都可以使用：

- `help` / `幫助`：查看可用指令
- `status` / `狀態`：查看目前狀態
- `save` / `存檔`：儲存目前進度
- `load` / `讀檔`：讀取 `save_game.json`
- `quit` / `離開`：離開原型

除了以上指令，其他輸入都會被視為玩家在冒險中的行動，並送給 AI GM 回應。

## 原型目前會做什麼

- 啟動一段單人文字冒險。
- 使用本機 Ollama 模型作為 AI GM。
- 接受玩家自由輸入的中文行動描述。
- 使用最小 AI Judge 判斷行動類型、合理性與是否需要擲骰。
- 需要檢定時自動擲 d20。
- 顯示骰子結果，例如：`檢定：d20 = 14，DC 13，成功。`
- AI GM 會根據 Judge 與 Dice 結果描述後果。
- AI GM 會輸出玩家可見敘事與內部 structured update JSON。
- JSON 通過驗證後會更新 GameState。
- JSON 壞掉時會啟用 fallback state update。
- 支援狀態保存與讀取。
- 記錄 playtest log 到 `prototype/playtest_log.txt`。
- 支援三位核心 NPC：酒館老闆娘瑪拉、村長奧倫、失蹤礦工的妹妹莉娜。
- 支援線索、NPC 記憶、世界旗標、HP、目標與結局追蹤。
- 支援救援、真相、決戰與失敗結局。

## v0.6 架構概觀

目前玩家表面上只看到 AI GM，但內部流程分成幾個小層：

1. 玩家輸入自由文字。
2. `judge.py` 判斷行動類型、是否可能、是否需要檢定。
3. `dice.py` 在需要時擲 d20。
4. `ai_gm.py` 建立 prompt，要求 AI GM 回傳敘事與 structured update JSON。
5. `local_ai.py` 呼叫 Ollama 本機模型。
6. `ai_response.py` 解析並驗證 AI 回覆。
7. `state_update.py` 在 JSON 合法時套用 structured update；不合法時使用 fallback。
8. `game_state.py` 保存目前世界狀態。
9. `playtest.py` 寫入測試紀錄。

## AI 回覆格式

AI GM 被要求輸出兩段：

```text
===NARRATION===
玩家可見敘事，最後詢問「你要怎麼做？」

===STATE_UPDATE_JSON===
{"clues_added": [], "flags_added": [], ...}
```

玩家只會看到 `NARRATION`。`STATE_UPDATE_JSON` 是內部資料，用來讓 GameState 記住 AI 敘事中發生的事。

如果本機模型把段落標記寫壞，但回覆尾端仍有合法 JSON 物件，`ai_response.py` 會先嘗試恢復並驗證該 JSON。只有無法恢復或驗證失敗時，才會啟用 fallback。

## Structured Update 可更新內容

目前 structured update 可以處理：

- `clues_added`
- `flags_added`
- `npc_memories_added`
- `inventory_added`
- `inventory_removed`
- `hp_delta`
- `objectives_completed`
- `objectives_failed`
- `ending`
- `notes_added`

`ending` 目前只允許：

- `rescue_focused`
- `truth_revealing`
- `confrontation_focused`
- `failure`
- `null`

## Fallback 行為

如果 AI 沒有輸出合法 JSON，遊戲不會崩潰。系統會改用保守規則從玩家行動與 AI 敘事中找出可追蹤資訊。

fallback 目前能處理一些明確關鍵字，例如：

- 瑪拉、老闆娘、酒館老闆
- 奧倫、村長
- 莉娜、妹妹、失蹤礦工家屬
- 腳印、靴印
- 燭光、奇異光、微光
- 舊礦燈、礦燈
- 救援、揭露真相、決戰等結局方向

fallback 是保底機制，不是完整理解系統。它只會做保守更新。

## 狀態與存檔

玩家輸入 `save` 或 `存檔` 時，原型會在 `prototype/main.py` 旁邊寫入 `save_game.json`。

狀態目前包含：

- 玩家名稱
- HP
- 道具
- 目前位置
- 已知線索
- NPC 記憶
- 世界旗標
- 已完成目標
- 失敗目標
- 結局

舊版 `save_game.json` 缺少新欄位時，遊戲會使用預設值讀取，不應崩潰。不過舊存檔可能只會讀取部分資料。

## Playtest Log

每次玩家輸入與 AI 回覆都會記錄到：

```text
prototype/playtest_log.txt
```

v0.6 記錄內容包含：

- 回合數
- 場景與目前位置
- 玩家行動
- Judge 結果
- Dice 結果
- AI raw response
- parsed narration
- parsed structured update
- parsed errors
- fallback 是否啟用
- state update 結果
- 最終 GameState 摘要
- 更新後已知線索
- 更新後世界旗標
- 玩家可見 AI 回覆

不會記錄 API key 或敏感環境變數。

## OpenAI provider

目前預設不使用 OpenAI API。

程式內仍保留 OpenAI provider 測試入口，但 v0.6 的預設路徑是 Ollama 本機模型。不要把 API key 寫進程式碼或提交到 GitHub。

## 目前不會做什麼

- 不包含完整 DND 規則。
- 不包含完整戰鬥系統。
- 不包含角色建立。
- 不包含職業、能力值、完整背包、裝備或法術系統。
- 不包含多人遊戲。
- 不包含網頁或手機介面。
- 不包含帳號、資料庫、付費、語音、圖像生成或市集功能。
- 不代表最終冒險文本、最終對話或最終遊戲機制。

## 已知限制

- 本機模型可能偶爾不遵守 JSON 格式；此時會嘗試恢復尾端 JSON，若仍不合法則啟用 fallback。
- fallback 無法理解所有 AI 敘事，只能保守處理明確線索與事件。
- 目前 Dice 與 Judge 都是最小規則，不是完整 TRPG 規則系統。
- 冒險內容仍是原型資料，還不是完整模組。
- 真實 20–30 分鐘遊玩體驗仍需要更多人工 playtest 驗證。

## 後續方向

後續版本可以評估：

- 更穩定的 structured update schema。
- 更嚴格的 AI JSON 修復流程。
- 更好的 NPC 記憶摘要。
- 更清楚的場景與結局條件。
- 更完整的線索狀態追蹤。
- 更多真人 playtest 紀錄分析。

以上只是未來方向，v0.6 沒有實作完整遊戲系統。
