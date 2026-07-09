# AIGMOS Demo v0.4

## 版本

v0.4

## 狀態

可遊玩的本機 AI GM 文字原型

## 目的

這個原型用來驗證 AIGMOS 的本機單人文字冒險循環。玩家可以用自然語言輸入行動，系統會先用最小 AI Judge 判斷行動合理性與是否需要擲骰，再把目前場景、狀態、Judge 結果與骰子結果交給本機 AI GM 回應。

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

## 原型目前會做什麼

- 啟動一段單人文字冒險。
- 使用本機 Ollama 模型作為 AI GM。
- 接受玩家自由輸入的中文行動描述。
- 使用最小 AI Judge 判斷行動類型、合理性與是否需要擲骰。
- 需要檢定時自動擲 d20。
- 顯示骰子結果，例如：`檢定：d20 = 14，DC 13，成功。`
- AI GM 會根據 Judge 與 Dice 結果描述後果。
- 支援狀態保存與讀取。
- 記錄 playtest log 到 `prototype/playtest_log.txt`。
- 支援三位核心 NPC：
  - 酒館老闆娘瑪拉
  - 村長奧倫
  - 失蹤礦工的妹妹莉娜
- 支援至少六個線索。
- 支援三種結局方向：救援、真相、決戰。

## 可用指令

英文與中文指令都可以使用：

- `help` / `幫助`：查看可用指令
- `status` / `狀態`：查看目前狀態
- `save` / `存檔`：儲存目前進度
- `load` / `讀檔`：讀取 `save_game.json`
- `quit` / `離開`：離開原型

除了以上指令，其他輸入都會被視為玩家在冒險中的行動，並送給 AI GM 回應。

## 狀態與存檔

玩家輸入 `save` 或 `存檔` 時，原型會在 `prototype/main.py` 旁邊寫入 `save_game.json`。

v0.4 擴充了狀態欄位，包含：

- 玩家名稱
- HP
- 道具
- 目前位置
- 已知線索
- NPC 記憶
- 世界旗標
- 已完成目標
- 失敗目標

舊版 `save_game.json` 缺少新欄位時，遊戲會使用預設值讀取，不應崩潰。不過舊存檔可能只會讀取部分資料。

## Playtest Log

每次玩家輸入與 AI 回覆都會記錄到：

```text
prototype/playtest_log.txt
```

記錄內容包含：

- 回合數
- 場景
- 玩家行動
- Judge 結果
- Dice 結果
- AI 回覆

不會記錄 API key 或敏感資料。

## OpenAI fallback

目前預設不使用 OpenAI API。

如果之後需要測試 OpenAI provider，可以設定：

```powershell
$env:AIGMOS_AI_PROVIDER="openai"
$env:OPENAI_API_KEY="你的 API 金鑰"
```

不要把 API key 寫進程式碼或提交到 GitHub。

## 目前不會做什麼

- 不包含完整 DND 規則。
- 不包含完整戰鬥系統。
- 不包含職業、能力值、完整背包、裝備或法術系統。
- 不包含多人遊戲。
- 不包含網頁或手機介面。
- 不包含帳號、資料庫、付費、語音、圖像生成或市集功能。
- 不代表最終冒險文本、最終對話或最終遊戲機制。

## 未來方向

後續版本可以評估：

- 更穩定的場景推進判斷。
- 更完整的 NPC 記憶摘要。
- 更好的檢定提示格式。
- 更細緻的線索鎖定與結局條件。
- 自動化測試 AI GM prompt 結構。

以上只是未來方向，v0.4 沒有實作完整遊戲系統。
