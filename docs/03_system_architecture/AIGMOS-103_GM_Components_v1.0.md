# AIGMOS-103 GM Processor Components Specification v1.0

Status: Draft

## Purpose

定義 GM Processor 的所有元件。

本文件依據：

- AIGMOS-101_GM_Context_v1.0
- AIGMOS-102_GM_Turn_v1.0

## Component Overview

GM Processor 固定包含九個元件：

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

### Purpose

協調 GM Processor 每回合的固定流程。

### Responsibilities

- 接收 Player Input 與 GM Context。
- 依固定順序協調各元件。
- 收集各元件輸出。
- 組成 Turn Result。
- 處理 Warnings 與 Errors。

### Input

- Player Input
- GM Context
- Optional Dice Result

### Output

- Turn Result

### Cannot Do

- 自行解讀玩家行動。
- 自行裁定規則。
- 自行修改狀態。
- 自行產生敘事。

## 2. Interpreter

### Purpose

理解玩家真正想執行的行動。

### Responsibilities

- 分析 Player Input。
- 參考 GM Context 理解行動背景。
- 產生 Action Interpretation。

### Input

- Player Input
- GM Context

### Output

- Action Interpretation

### Cannot Do

- 判定成功或失敗。
- 修改任何 Context。
- 產生玩家可見敘事。

## 3. Judge

### Purpose

依照規則與目前狀態完成行動裁定。

### Responsibilities

- 判斷行動是否合法與是否可能。
- 判斷是否需要檢定。
- 指定檢定類型與難度。
- 產生 Ruling 與 Dice Request。

### Input

- Action Interpretation
- GM Context

### Output

- Ruling
- Dice Request

### Cannot Do

- 擲骰。
- 修改狀態。
- 產生敘事。

## 4. Dice Interface

### Purpose

提供 GM Processor 與骰子結果之間的固定資料交換邊界。

### Responsibilities

- 接收 Dice Request。
- 接收 Optional External Dice Result。
- 驗證骰子結果。
- 回傳 Validated Dice Result。

### Input

- Dice Request
- Optional External Dice Result

### Output

- Validated Dice Result

### Cannot Do

- 修改骰子結果。
- 裁定行動結果。
- 修改世界或角色狀態。

## 5. Resolver

### Purpose

根據解讀、裁定與骰子結果決定實際結果。

### Responsibilities

- 整合 Action Interpretation、Ruling 與 Dice Result。
- 參考 GM Context。
- 產生 Resolution。

### Input

- Action Interpretation
- Ruling
- Dice Result
- GM Context

### Output

- Resolution

### Cannot Do

- 直接修改 Context。
- 產生玩家可見敘事。
- 忽略 Ruling 或 Dice Result。

## 6. State Update Builder

### Purpose

將 Resolution 轉換成固定的狀態更新資料。

### Responsibilities

- 根據 Resolution 建立 State Update。
- 將變更依所屬狀態分類。
- 確保更新內容不超出 Resolution。

### Input

- Resolution
- GM Context

### Output

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

### Cannot Do

- 直接寫入外部系統。
- 新增 Resolution 未決定的結果。
- 產生敘事。

## 7. Narrator

### Purpose

將已完成的裁定與結果轉換成玩家可見敘事。

### Responsibilities

- 根據 Resolution 與 State Update 描述結果。
- 確保 Narration 符合既有裁定。
- 使用繁體中文產生 Narration。

### Input

- Action Interpretation
- Ruling
- Resolution
- State Update
- GM Context

### Output

- Narration

### Cannot Do

- 修改 State Update。
- 重新裁定規則。
- 新增重要世界事實。
- 替玩家決定思想、情緒或下一步。

## 8. Validator

### Purpose

確保各元件交換的資料合法且完整。

### Responsibilities

- 驗證各元件的 Input 與 Output。
- 阻止不合法資料進入下一步。
- 產生 Validation Result、Warnings 與 Errors。

### Input

- Component Input
- Component Output

### Output

- Validation Result
- Warnings
- Errors

### Cannot Do

- 自行修正規則結果。
- 自行新增世界內容。
- 略過驗證失敗。

## 9. AI Provider

### Purpose

提供可替換的 AI 能力邊界，隔離特定模型。

### Responsibilities

- 接收標準化 Model Request。
- 將模型回應轉換成 Raw Model Output。
- 回報 Provider Error。
- 維持模型替換能力。

### Input

- Model Request
- Model Configuration

### Output

- Raw Model Output
- Provider Error

### Cannot Do

- 保存遊戲狀態。
- 直接修改 GM Context。
- 綁定任何 Adventure。
- 綁定任何 Rule System。

## Component Flow

固定流程：

```text
Turn Orchestrator
↓
Interpreter
↓
Validator
↓
Judge
↓
Validator
↓
Dice Interface
↓
Resolver
↓
Validator
↓
State Update Builder
↓
Validator
↓
Narrator
↓
Validator
↓
Turn Result
```

## Component Independence

每個元件不得：

- 修改其他元件資料。
- 直接存取外部系統。
- 保存遊戲狀態。
- 綁定任何 Adventure。
- 綁定任何 Rule System。

元件之間只能透過各自定義的 Input 與 Output 交換資料。

## Acceptance Criteria

GM Processor 必須可以替換以下項目，而不用修改其他元件：

- AI
- Rule
- Adventure
- World

並確認：

- 固定包含九個元件。
- 每個元件都有 Purpose、Responsibilities、Input、Output 與 Cannot Do。
- Component Flow 符合 AIGMOS-102_GM_Turn_v1.0。
- 所有元件只透過固定資料交換。
- GM Processor 不依賴特定 Adventure、Rule System、World 或 AI。

## Restrictions

不得加入：

- Python
- JSON
- Prompt
- Implementation
