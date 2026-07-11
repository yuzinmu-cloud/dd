# GM Processor

GM Processor 現在支援多回合 Session，同時保留無狀態的單回合核心。

## 架構邊界

- `process_turn()`：無狀態的單回合處理器，只接收新版 TurnInput。
- `session_runner.py`：唯一保存 Session 內 GMContext 的元件，負責持續呼叫 `process_turn()`。
- `state_update_applier.py`：將合法 State Update 套用到 Context 副本；不直接修改原始 Context。
- `session_log.py`：選用的公開 playtest log，不記錄 hidden facts。

每次單回合呼叫的正式輸入包含：

```text
player_input
context
dice_result (optional)
```

GM Context 由 Rule、Character、World、Adventure、History、Session 六個區段組成，是 GM Processor 唯一正式資訊來源。

## 多回合 Session

Session Runner 每回合會：

1. 使用目前 GMContext 建立 TurnInput。
2. 呼叫無狀態 `process_turn()`。
3. 原子套用合法 State Update。
4. 更新 History Context。
5. 增加 `turn_number` 並更新近期對話。
6. 將新的 GMContext 傳入下一回合。

以下資料有長度上限，只保留最新內容：

- `recent_events`：20
- `recent_conversation`：12 則訊息
- `player_decisions`：30
- `unresolved_consequences`：20

輸入 `離開`、`quit` 或 `exit` 可結束 Session。每次 Demo 啟動都重新讀取 Context JSON，不會污染另一個 Session，也不會改寫 sample 檔案。

## State Update

State Update 只會套用明確列出的變更。任何非法更新會使該次 State Update 整批回滾，保留原 Context。

支援：

- Character：HP、conditions、inventory、equipment、attributes、skills
- NPC：attitude、current_state、known_facts、goals
- World：location、known facts、active states、time、weather
- Adventure：known clues、active objectives、active events、current situation
- Session：current phase、initiative

限制：

- 不可修改角色 ID、角色名稱、規則、world name、adventure ID、premise 或 hidden facts。
- HP 必須介於 0 與 max HP 之間。
- 不可移除不存在的物品。
- 世界事實只能明確新增；失效必須使用 `invalidated_world_facts`。
- 本階段禁止動態新增 NPC。
- 本階段維持單一 Adventure，不會自動切換。

## Pending Dice

若 Turn Result 需要骰子但沒有結果，Session 不增加回合數，也不重複記錄玩家決定。Demo 會要求：

```text
roll 14
```

有效結果會使用相同玩家行動與相同 Context 再次呼叫 `process_turn()`；完成 Resolution 後才套用 State Update。格式錯誤時會提示重輸，不會中斷 Session。

## Context Samples

- `gm_processor/sample_data/gm_context.json`：霧河諸境
- `gm_processor/sample_data/gm_context_alt.json`：赫利俄斯航域
- `gm_processor/sample_data/turn_input.json`：新版單回合 TurnInput 範例

舊 `rule_system.json`、`character.json`、`situation.json`、`world_state.json` 已淘汰，只保留作 legacy 參考，不再是 Demo 輸入。

## 執行 Demo

預設 Context：

```powershell
python gm_processor/demo.py
```

替代 Context：

```powershell
python gm_processor/demo.py --context gm_context_alt.json
```

選用安全 playtest log：

```powershell
python gm_processor/demo.py --log
```

Logs 寫入 `gm_processor/logs/`，該目錄已被忽略。Logging 失敗只會產生 warning，不會中斷遊戲。

## 執行測試

```powershell
python -m pytest gm_processor/tests
```

## Ollama

AI Provider 預設使用 `local_ai.py` 連接 Ollama。服務或模型不可用時，單回合與 Session 都會回傳合法結果並記錄 error，不會崩潰。

## 目前不包含

- 自動存檔或資料庫
- 完整 D&D 規則
- Adventure 自動切換
- 角色建立
- 長期跨 Session 記憶
- UI 或 App
