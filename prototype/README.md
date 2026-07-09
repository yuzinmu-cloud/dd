# AIGMOS Demo v0.3

## 版本

v0.3

## 狀態

可遊玩的 AI GM 文字原型

## 目的

這個原型用來驗證 AIGMOS 第一個單人文字冒險循環，並接入 OpenAI API，讓 AI GM 可以根據目前場景、玩家輸入與狀態記錄，用繁體中文回應玩家。

冒險內容基於 MVP 前提：《燭芯礦坑事件》。

## 安裝 OpenAI 套件

請先安裝 OpenAI Python SDK：

```bash
pip install openai
```

## 設定 OPENAI_API_KEY

執行遊戲前，需要先設定環境變數 `OPENAI_API_KEY`。

PowerShell 範例：

```powershell
$env:OPENAI_API_KEY="你的 API 金鑰"
```

macOS / Linux 範例：

```bash
export OPENAI_API_KEY="你的 API 金鑰"
```

請不要把 API key 寫進程式碼或提交到 GitHub。

如果沒有設定 API key，遊戲會顯示：

```text
找不到 OPENAI_API_KEY，請先設定 API 金鑰。
```

## 如何啟動

請在 repository 根目錄執行：

```bash
python prototype/main.py
```

## 原型目前會做什麼

- 啟動一段單人文字冒險。
- 載入固定的《燭芯礦坑事件》冒險前提。
- 顯示開場敘事。
- 接受玩家自由輸入的行動描述。
- 呼叫 OpenAI Responses API 產生 AI GM 回應。
- AI GM 會使用繁體中文回應。
- AI GM 會維持目前場景與礦坑事件脈絡。
- AI GM 不會替玩家決定行動。
- 遇到風險行動時，AI GM 會提示可能需要檢定。
- 記錄簡單的遊戲狀態。
- 支援五個場景：
  - 酒館
  - 村莊廣場
  - 礦坑入口
  - 礦坑深處
  - 礦坑最深處
- 在最後場景支援簡單結局狀態。
- 透過 `save_game.json` 進行簡單存檔與讀檔。

## 可用指令

英文與中文指令都可以使用：

- `help` / `幫助`：查看可用指令
- `status` / `狀態`：查看目前狀態
- `save` / `存檔`：儲存目前進度
- `load` / `讀檔`：讀取 `save_game.json`
- `quit` / `離開`：離開原型

除了以上指令，其他輸入都會被視為玩家在冒險中的行動，並送給 AI GM 回應。

## 可選模型設定

預設模型為 `gpt-4.1-mini`。

如需改用其他模型，可以設定：

```powershell
$env:AIGMOS_OPENAI_MODEL="你的模型名稱"
```

macOS / Linux：

```bash
export AIGMOS_OPENAI_MODEL="你的模型名稱"
```

## 目前不會做什麼

- 不包含完整規則系統。
- 不包含完整戰鬥系統。
- 不包含職業、HP、背包、裝備或法術系統。
- 不包含多人遊戲。
- 不包含網頁或手機介面。
- 不包含帳號、資料庫、付費、語音、圖像生成或市集功能。
- 不代表最終冒險文本、最終對話或最終遊戲機制。

## 存檔

玩家輸入 `save` 或 `存檔` 時，原型會在 `prototype/main.py` 旁邊寫入 `save_game.json`。

v0.3 沒有修改存檔格式。

## 未來方向

後續版本可以評估：

- 更清楚的新手引導。
- 更穩定的場景推進判斷。
- 更完整的 AI GM 記憶摘要。
- 更好的檢定提示格式。
- 自動化測試 AI GM prompt 結構。

以上只是未來方向，v0.3 沒有實作新系統。
