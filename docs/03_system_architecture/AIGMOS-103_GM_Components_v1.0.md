# AIGMOS-103 GM Processor Components Specification v1.0

Status: Draft

## Purpose

定義 GM Processor 內部元件、各自責任、輸入輸出與權限邊界。

本文件必須依照：

- AIGMOS-101 GM Context Specification v1.0
- AIGMOS-102 GM Turn Specification v1.0

## Component Overview

GM Processor 包含以下元件：

1. Turn Orchestrator
2. Interpreter
3. Judge
4. Dice Interface
5. Resolver
6. State Update Builder
7. Narrator
8. Validator
9. AI Provider

## 1. Turn Orchestrator

責任：

- 接收 Player Input 與 GM Context。
- 依固定順序呼叫所有元件。
- 收集每個元件輸出。
- 組成最終 Turn Result。
- 處理錯誤與安全降級。

輸入：

- Player Input
- GM Context
- Optional Dice Result

輸出：

- Turn Result

不得：

- 自行解讀玩家行動。
- 自行裁定規則。
- 自行修改狀態。
- 自行產生敘事。

## 2. Interpreter

責任：

- 理解玩家輸入。
- 產生 Action Interpretation。

輸入：

- Player Input
- GM Context

輸出：

- Action Interpretation

不得：

- 判定成功或失敗。
- 修改任何 Context。
- 產生玩家可見敘事。

## 3. Judge

責任：

- 依 Rule Context 與目前狀態進行規則裁定。
- 判斷行動是否可能。
- 判斷是否需要檢定。
- 指定檢定類型與難度。

輸入：

- Action Interpretation
- GM Context

輸出：

- Ruling
- Dice Request

不得：

- 擲骰。
- 修改狀態。
- 產生敘事。

## 4. Dice Interface

責任：

- 向外部骰子系統提出擲骰需求。
- 接收骰子結果。
- 驗證骰子結果格式。

輸入：

- Dice Request
- Optional External Dice Result

輸出：

- Validated Dice Result

不得：

- 修改骰子結果。
- 裁定敘事結果。
- 修改世界狀態。

## 5. Resolver

責任：

- 根據 Action Interpretation、Ruling 與 Dice Result，決定實際發生的結果。

輸入：

- Action Interpretation
- Ruling
- Dice Result
- GM Context

輸出：

- Resolution

不得：

- 直接修改 Context。
- 產生玩家可見敘事。
- 忽略 Ruling 或 Dice Result。

## 6. State Update Builder

責任：

- 將 Resolution 轉換成結構化 State Update。

輸入：

- Resolution
- GM Context

輸出：

- State Update

State Update 可包含：

- Player Changes
- NPC Changes
- World Changes
- Inventory Changes
- Clue Changes
- Location Changes
- Event Changes
- Session Changes

不得：

- 直接寫入外部系統。
- 新增 Resolution 未決定的結果。
- 產生敘事。

## 7. Narrator

責任：

- 將已完成的裁定與結果轉換成玩家可見敘事。

輸入：

- Action Interpretation
- Ruling
- Resolution
- State Update
- GM Context

輸出：

- Narration

不得：

- 修改 State Update。
- 重新裁定規則。
- 新增重要世界事實。
- 替玩家決定思想、情緒或下一步。

## 8. Validator

責任：

- 驗證各元件輸入與輸出格式。
- 阻止不合法資料進入下一步。
- 產生 Warnings 與 Errors。

輸入：

- 各元件輸入與輸出資料

輸出：

- Validation Result
- Warnings
- Errors

不得：

- 自行修正規則結果。
- 自行新增世界內容。

## 9. AI Provider

責任：

- 提供本機或外部語言模型存取介面。
- 隔離特定模型實作。

輸入：

- Structured Prompt
- Output Schema
- Model Configuration

輸出：

- Raw Model Output
- Provider Error

不得：

- 保存遊戲狀態。
- 直接修改 GM Context。
- 綁定特定劇本或規則。

## Required Component Order

固定順序：

```text
Turn Orchestrator
→ Interpreter
→ Validator
→ Judge
→ Validator
→ Dice Interface
→ Resolver
→ Validator
→ State Update Builder
→ Validator
→ Narrator
→ Validator
→ Turn Result
```

## Component Independence

每個元件必須：

- 有明確輸入。
- 有明確輸出。
- 可以單獨測試。
- 不直接存取其他元件內部資料。
- 不依賴特定劇本名稱。
- 不依賴特定規則系統名稱。
- 不依賴特定 AI 模型。

## AI Usage Policy

本文件不強制指定哪些元件一定使用 AI。

每個元件可以使用：

- Deterministic Rules
- Local LLM
- External LLM
- Hybrid Method

但對外輸入輸出契約不得改變。

## Non-Goals

本文件不定義：

- Python 類別。
- JSON Schema。
- Prompt 內容。
- 特定模型。
- 完整 D&D 規則。
- Adventure System。
- World System。
- UI。
- App。
- 資料庫。

## Acceptance Criteria

文件完成後必須：

- 清楚定義 9 個元件。
- 每個元件都有責任、輸入、輸出與禁止事項。
- 元件順序符合 AIGMOS-102。
- 所有元件只透過固定資料交換。
- GM Processor 不依賴特定劇本、規則或模型。
- 文件不包含實作程式碼。
- 不修改任何既有程式。
