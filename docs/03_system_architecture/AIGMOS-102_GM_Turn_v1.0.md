# AIGMOS-102 GM Turn Specification v1.0

Status: Draft

## Purpose

定義 GM Processor 每一回合的固定工作流程。

所有 GM Processor 必須遵守本流程。

## Overview

每一回合固定流程：

```text
Player Input
↓
Interpret
↓
Judge
↓
Roll
↓
Resolve
↓
Update
↓
Narrate
↓
Turn Result
```

## Step 1：Interpret

目的：

理解玩家真正想做的事情。

輸入：

- Player Input
- GM Context

輸出：

Action Interpretation

不得：

- 裁定成功或失敗
- 修改世界
- 修改角色
- 產生敘事

## Step 2：Judge

目的：

依照 Rule Context 判定：

- 行動是否合法
- 是否可能
- 是否需要檢定
- 使用哪種檢定
- 難度

輸出：

Ruling

不得：

- 擲骰
- 修改世界

## Step 3：Roll

目的：

取得骰子結果。

若不需擲骰：

直接略過。

GM 不可自行修改骰子結果。

## Step 4：Resolve

目的：

根據：

- Action Interpretation
- Ruling
- Dice Result

推導實際發生的結果。

輸出：

Resolution

不得：

直接修改 Context。

## Step 5：Update

目的：

建立：

State Update

包含：

- Player Changes
- NPC Changes
- World Changes
- Inventory Changes
- Clue Changes
- Event Changes

不得：

直接寫入世界。

只提出更新內容。

## Step 6：Narrate

目的：

向玩家描述結果。

要求：

- 不控制玩家思想。
- 不控制玩家下一步。
- 符合 Resolution。
- 符合 State Update。
- 使用繁體中文。

## Turn Result

每回合固定輸出：

- Interpretation
- Ruling
- Dice Request
- Resolution
- State Update
- Narration
- Warnings
- Errors

## Design Rules

GM 每回合：

不得：

- 跳步驟
- 合併步驟
- 修改流程順序

任何新功能必須加入既有流程。

不得新增第二條流程。

## Acceptance Criteria

完成後：

任何人閱讀本文件。

都能理解：

GM Processor 每一回合到底做了哪些事情。

不得包含：

- Prompt
- Python
- JSON Schema
- 實作細節
