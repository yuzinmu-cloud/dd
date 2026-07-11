# AIGMOS-101 GM Context Specification v1.0

Status: Draft

## Purpose

GM Context 是 GM Processor 每一回合唯一合法的輸入資料。

GM Processor 不得直接讀取任何其他系統。

所有世界資訊、角色資訊、規則資訊、劇本資訊都必須先整理成 GM Context。

## Architecture

GM Context 由六個 Context 組成：

1. Rule Context
2. Character Context
3. World Context
4. Adventure Context
5. History Context
6. Session Context

## Rule Context

Purpose：

提供規則裁定依據。

內容：

- Rule System Name
- Rule Version
- Available Checks
- Difficulty Rules
- Special Rules
- House Rules

## Character Context

Purpose：

提供玩家角色目前狀態。

內容：

- Character ID
- Name
- Race
- Class
- Level
- Attributes
- Skills
- Inventory
- Equipment
- Conditions
- HP

## World Context

Purpose：

提供客觀世界資訊。

內容：

- World Name
- Current Region
- Current Location
- Time
- Weather
- Known World Facts
- Active World States

## Adventure Context

Purpose：

提供目前 Adventure。

內容：

- Adventure ID
- Adventure Title
- Current Situation
- NPC List
- Known Clues
- Active Objectives
- Hidden GM Facts

## History Context

Purpose：

提供目前遊戲歷史。

內容：

- Recent Events
- Player Decisions
- Unresolved Consequences
- World Changes
- NPC Memories

## Session Context

Purpose：

提供本次 Session。

內容：

- Session ID
- Turn Number
- Recent Conversation
- Initiative (optional)

## GM Input

GM Processor 每回合只能收到：

- GM Context
- Player Input

## GM Output

GM Processor 必須輸出：

- Interpretation
- Ruling
- Dice Request
- Resolution
- State Update
- Narration
- Warnings
- Errors

## Ownership

Rule Context
→ Rule System

Character Context
→ Character System

World Context
→ World System

Adventure Context
→ Adventure System

History Context
→ Save System

Session Context
→ Game Client

GM Processor 不擁有任何 Context。

## Acceptance Criteria

GM Processor：

- 不直接讀取 Rule System
- 不直接讀取 Adventure
- 不直接讀取 World
- 不直接讀取 Character
- 僅接收 GM Context
- 可透過不同 GM Context 主持不同世界

## Restrictions

本文件僅定義 GM Context。

不得加入：

- JSON Schema
- Python
- Prompt
- Implementation
