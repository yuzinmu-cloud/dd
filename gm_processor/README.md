# GM Processor 原型

## 用途

GM Processor 是 AIGMOS 的獨立單回合處理原型。

它接收玩家輸入、規則資料、角色資料、當前情境、世界狀態與近期事件，輸出一份結構化的 `TurnResult`，包含：

- 玩家行動理解
- 裁定結果
- 是否需要擲骰
- 解決結果
- 狀態更新
- 玩家可見敘事
- warnings / errors

本原型不依賴任何特定劇本，也不修改 `prototype/`。

## 安裝方式

建議使用 Python 3.10 以上。

```bash
pip install pydantic pytest
```

## Ollama 啟動方式

請先安裝 Ollama：

https://ollama.com

啟動預設模型：

```bash
ollama run qwen2.5:7b
```

本原型會呼叫：

```text
http://localhost:11434/api/generate
```

預設模型：

```text
qwen2.5:7b
```

可用環境變數覆蓋：

```powershell
$env:AIGMOS_LOCAL_MODEL="你的模型名稱"
```

## 執行 Demo

```bash
python gm_processor/demo.py
```

流程：

1. 讀取 `gm_processor/sample_data/`。
2. 顯示目前情境。
3. 接受一行繁體中文玩家輸入。
4. 呼叫 `process_turn`。
5. 顯示玩家可見敘事、裁定結果與狀態更新。
6. 執行一次後結束。

## 執行測試

```bash
python -m pytest gm_processor/tests
```

## 目前範圍

- 只處理單一玩家回合。
- 使用 Pydantic 驗證輸入與輸出。
- 使用 Ollama 本機模型，不使用 OpenAI API。
- 模型輸出不合法時，會嘗試解析 JSON；仍不合法時回傳安全錯誤結果。

## 目前不包含

- 完整 D&D 規則。
- 完整戰鬥系統。
- 長期記憶。
- 完整戰役。
- 多劇本切換。
- 自我學習。
- UI、App、資料庫、帳號或多人模式。
