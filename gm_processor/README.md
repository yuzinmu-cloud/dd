# GM Processor

GM Processor 是 AIGMOS 的獨立單回合處理器。GM Context 是唯一正式輸入格式；`process_turn()` 不再接受分散的規則、角色、情境、世界狀態或歷史欄位。

## 正式輸入

每次呼叫使用新版 `TurnInput`：

```text
player_input
context
dice_result (optional)
```

`context` 是完整的 GM Context，由六個區段組成：

- Rule Context：唯一規則裁定依據。
- Character Context：玩家角色能力、裝備、狀態與限制。
- World Context：客觀世界事實、地點與活躍狀態。
- Adventure Context：當前事件、NPC、線索、目標及 GM 隱藏資訊。
- History Context：近期事件、玩家決定與未解後果。
- Session Context：本次 Session、回合編號與近期對話。

## 修改 Context

預設範例位於 `gm_processor/sample_data/gm_context.json`。修改時必須保留所有 GMContext 必要欄位，且符合下列限制：

- `context_version` 不可為空。
- `current_hp` 不可大於 `max_hp`。
- `turn_number` 不可小於 0。
- `hidden_gm_facts` 不可同時列為 `known_clues`。
- NPC 的 `hidden_facts` 不可同時列為 `known_facts`。

完整 TurnInput 範例位於 `gm_processor/sample_data/turn_input.json`。

## 不同世界範例

`gm_processor/sample_data/gm_context_alt.json` 使用完全不同的科幻世界、角色、規則與當前事件。切換 Context 不需要修改 GM Processor 程式。

## 執行 Demo

預設 Context：

```powershell
python gm_processor/demo.py
```

替代 Context：

```powershell
python gm_processor/demo.py --context gm_context_alt.json
```

Demo 讀取一份 GM Context、接受一行繁體中文玩家輸入、呼叫 `process_turn()`、顯示固定 Turn Result，然後結束。

## 執行測試

```powershell
python -m pytest gm_processor/tests
```

## 舊 Sample Data

以下分散式檔案已淘汰並保留作為 legacy 參考，不再是正式 Demo 輸入來源：

- `rule_system.json`
- `character.json`
- `situation.json`
- `world_state.json`

## Ollama

AI Provider 預設透過現有 `local_ai.py` 使用 Ollama。模型或服務無法使用時，GM Processor 會回傳合法 Turn Result，並將問題放入 `errors`，不會讓回合崩潰。

## 目前範圍

- 僅支援單回合。
- 不自動擲骰；外部系統可透過 `dice_result` 提供結果。
- 不寫入 Context、世界或存檔。
- 不包含完整規則、多回合、長期記憶、資料庫、UI 或 App。
