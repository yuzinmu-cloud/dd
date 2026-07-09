from __future__ import annotations

from game_state import GameState


ADVENTURE_TITLE_DISPLAY = "燭芯礦坑事件"

ADVENTURE_PREMISE = """
玩家是一名獨行冒險者，抵達暴雨中的邊境村莊灰堤村。
三名礦工在廢棄的燭芯礦坑失蹤，礦坑深處出現奇異燭光。
村民想找回失蹤者，但酒館老闆娘、村長與失蹤礦工的妹妹都隱瞞了不同部分的真相。
玩家可以調查村莊、詢問 NPC、進入礦坑，最後走向救援、真相或決戰結局。
""".strip()

OPENING_NARRATION = """
燭芯礦坑事件

暴雨拍打著你的斗篷。

當你踏入邊境村莊灰堤村時，整座村子異常安靜。
只有酒館還亮著燈，遠方山脊下的廢棄礦坑卻不時閃過蒼白的燭光。

三名礦工失蹤了。
村民希望在天亮以前得到答案。
""".strip()

SCENE_NAMES = {
    "village_inn": "酒館",
    "village_square": "村莊廣場",
    "mine_entrance": "礦坑入口",
    "mine_interior": "礦坑深處",
    "final_chamber": "礦坑最深處",
}

SCENE_DESCRIPTIONS = {
    "village_inn": "你站在村裡唯一還亮著燈的酒館中。濕透的旅人低聲交談，酒館老闆娘瑪拉看著你的眼神比她願意承認的更警覺。",
    "village_square": "村莊廣場被雨水沖得發亮。幾名村民聚在告示牌旁，村長奧倫努力壓低眾人的恐慌。",
    "mine_entrance": "礦坑入口在山脊下張著黑暗的口。破裂的警告牌掛在木樁上，新鮮的腳印一路消失在坑道裡。",
    "mine_interior": "礦坑深處傳來滴水聲。腐朽的支架在黑暗中傾斜，燭色微光在更深處緩緩游移。",
    "final_chamber": "你抵達礦坑最深處。失蹤礦工的線索、怪異燭光，以及村子隱瞞的祕密都在這裡交會。",
}

NPCS = {
    "mara": {
        "name": "瑪拉",
        "role": "酒館老闆娘",
        "what_they_know": "上一批探勘隊回村後神情蒼白，隨後礦坑開始出現燭色微光。",
        "what_they_hide": "她曾把一盞舊礦燈交給失蹤礦工，希望他們確認下層坑道是否安全。",
        "attitude": "謹慎、內疚，但願意幫助真心想救人的玩家。",
    },
    "oren": {
        "name": "奧倫",
        "role": "村長",
        "what_they_know": "礦坑下層多年前因事故封閉，村子一直對外宣稱只是坍方。",
        "what_they_hide": "他害怕真相曝光會讓灰堤村失去最後的生計。",
        "attitude": "克制、務實，想低調解決問題。",
    },
    "lina": {
        "name": "莉娜",
        "role": "失蹤礦工的妹妹",
        "what_they_know": "她哥哥失蹤前提到聽見封閉坑道裡有人敲擊。",
        "what_they_hide": "她偷拿過哥哥的礦坑筆記，知道一條繞進下層的側道。",
        "attitude": "焦急、直接，會催促玩家立刻行動。",
    },
}

CLUES = {
    "inn_survey_crew": "酒館線索：上一批探勘隊返村後沉默不語，礦坑異光也從那晚開始。",
    "inn_old_lantern": "酒館線索：瑪拉曾把一盞舊礦燈交給失蹤礦工。",
    "village_closed_tunnel": "村莊線索：礦坑下層多年前因事故封閉，但村長不願公開細節。",
    "village_knocking": "村莊線索：莉娜說有人聽見封閉坑道深處傳來敲擊聲。",
    "mine_fresh_tracks": "礦坑線索：新鮮腳印進入礦坑，卻沒有離開的痕跡。",
    "mine_guiding_lights": "礦坑線索：燭色微光不像野獸或陷阱，更像在引導闖入者。",
}

FLAG_LABELS = {
    "questioned_innkeeper": "詢問過酒館老闆娘瑪拉",
    "met_village_leader": "見過村長奧倫",
    "heard_family_plea": "聽見莉娜的請求",
    "found_fresh_tracks": "發現通往礦坑的新鮮腳印",
    "noticed_warning_signs": "注意到礦坑警告牌",
    "handled_environmental_danger": "小心處理礦坑內的危險支架",
    "followed_strange_lights": "跟隨奇異燭光前進",
    "prioritized_rescue": "選擇優先救援",
    "prioritized_confrontation": "選擇正面對抗",
    "prioritized_truth": "選擇揭露真相",
}

HELP_TEXT = "可用指令：幫助/help、狀態/status、存檔/save、讀檔/load、離開/quit。除此之外，你可以直接輸入想做的行動。"


def describe_current_scene(state: GameState) -> str:
    return SCENE_DESCRIPTIONS[state.current_scene]


def status_text(state: GameState) -> str:
    scene_name = SCENE_NAMES.get(state.current_scene, state.current_scene)
    clues = "\n".join(f"- {clue}" for clue in state.known_clues) if state.known_clues else "尚未發現"
    inventory = "、".join(state.inventory) if state.inventory else "沒有道具"
    flags = "\n".join(f"- {FLAG_LABELS.get(flag, flag)}" for flag in sorted(state.world_flags or state.flags)) if (state.world_flags or state.flags) else "尚未觸發"
    completed = "\n".join(f"- {item}" for item in state.completed_objectives) if state.completed_objectives else "尚未完成"
    failed = "\n".join(f"- {item}" for item in state.failed_objectives) if state.failed_objectives else "尚未失敗"
    return (
        "====================\n"
        "目前狀態\n"
        "====================\n"
        f"冒險：{ADVENTURE_TITLE_DISPLAY}\n"
        f"玩家：{state.player_name}\n"
        f"HP：{state.hp}/{state.max_hp}\n"
        f"目前位置：{state.current_location or scene_name}\n"
        f"回合數：{state.turn_count}\n"
        f"道具：{inventory}\n"
        "線索：\n"
        f"{clues}\n"
        "事件：\n"
        f"{flags}\n"
        "已完成目標：\n"
        f"{completed}\n"
        "失敗目標：\n"
        f"{failed}\n"
        "===================="
    )


def handle_action(state: GameState, action: str, record: bool = True) -> str:
    cleaned = action.strip().lower()
    if record:
        state.record_action(action)

    if state.ended:
        return ending_text(state)

    if _move_by_location_keyword(state, cleaned):
        return describe_current_scene(state)

    if state.current_scene == "village_inn":
        return handle_village_inn(state, cleaned)
    if state.current_scene == "village_square":
        return handle_village_square(state, cleaned)
    if state.current_scene == "mine_entrance":
        return handle_mine_entrance(state, cleaned)
    if state.current_scene == "mine_interior":
        return handle_mine_interior(state, cleaned)
    if state.current_scene == "final_chamber":
        return handle_final_chamber(state, cleaned)

    return "遊戲主持人停頓了一下。目前的場景狀態無法辨識。"


def handle_village_inn(state: GameState, action: str) -> str:
    if has_any(action, "瑪拉", "innkeeper", "talk", "ask", "question", "rumor", "老闆", "酒館老闆", "老闆娘", "交談", "詢問", "打聽", "傳聞"):
        state.set_flag("questioned_innkeeper")
        state.add_clue(CLUES["inn_survey_crew"])
        state.add_clue(CLUES["inn_old_lantern"])
        state.remember_npc("瑪拉", "玩家詢問了探勘隊與舊礦燈。")
        return "瑪拉透露探勘隊與舊礦燈的線索。"

    if has_any(action, "square", "leave", "outside", "leader", "families", "continue", "廣場", "離開", "外面", "村長", "家屬", "繼續"):
        state.move_to_scene("village_square")
        return describe_current_scene(state)

    state.add_note("酒館裡氣氛緊繃，瑪拉似乎隱瞞了某些事情。")
    return "你注意到酒館裡的舊地圖、泥濘靴印與緊張村民。"


def handle_village_square(state: GameState, action: str) -> str:
    if has_any(action, "奧倫", "leader", "mayor", "elder", "quiet", "briefing", "村長", "長老", "安靜", "簡報", "說明"):
        state.set_flag("met_village_leader")
        state.add_clue(CLUES["village_closed_tunnel"])
        state.remember_npc("奧倫", "玩家詢問了封閉坑道與村子的隱瞞。")
        return "奧倫承認下層坑道曾因事故封閉，但不願把細節攤在村民面前。"

    if has_any(action, "莉娜", "relative", "family", "miner", "missing", "urgent", "家屬", "妹妹", "親人", "礦工", "失蹤", "急", "求助"):
        state.set_flag("heard_family_plea")
        state.add_clue(CLUES["village_knocking"])
        state.remember_npc("莉娜", "玩家聽見她描述封閉坑道裡的敲擊聲。")
        return "莉娜急切地說，她哥哥失蹤前提過封閉坑道裡的敲擊聲。"

    if has_any(action, "mine", "entrance", "ridge", "go", "continue", "礦坑", "入口", "山脊", "前往", "繼續"):
        state.move_to_scene("mine_entrance")
        return describe_current_scene(state)

    return "雨水沿著廣場石縫流成銀線。你可以詢問奧倫、安撫莉娜，或前往礦坑入口。"


def handle_mine_entrance(state: GameState, action: str) -> str:
    if has_any(action, "tracks", "boot", "footprint", "inspect", "search", "腳印", "靴印", "檢查", "調查", "搜尋"):
        state.set_flag("found_fresh_tracks")
        state.add_clue(CLUES["mine_fresh_tracks"])
        return "你確認新鮮腳印一路通往礦坑，卻沒有返回痕跡。"

    if has_any(action, "sign", "warning", "listen", "light", "lantern", "告示", "警告", "聆聽", "光", "燭光", "提燈"):
        state.set_flag("noticed_warning_signs")
        state.add_clue("礦坑線索：警告牌標示下層坑道不穩，日落後禁止進入。")
        return "裂開的警告牌提到支架不穩與封閉下層坑道。"

    if has_any(action, "enter", "inside", "mine", "go", "continue", "進入", "裡面", "礦坑", "前進", "繼續"):
        state.move_to_scene("mine_interior")
        return describe_current_scene(state)

    return "礦坑在雨中沉默地等待。你可以檢查腳印、查看警告牌、在入口聆聽，或直接進入。"


def handle_mine_interior(state: GameState, action: str) -> str:
    if has_any(action, "beam", "danger", "careful", "avoid", "brace", "支架", "危險", "小心", "避開", "撐住", "加固"):
        state.set_flag("handled_environmental_danger")
        state.add_clue("礦坑線索：支架後方有一枚掉落的礦工識別牌。")
        return "你小心通過不穩支架，找到一枚掉落的礦工識別牌。"

    if has_any(action, "light", "follow", "clue", "token", "deeper", "sound", "光", "燭光", "跟隨", "線索", "識別牌", "更深", "聲音"):
        state.set_flag("followed_strange_lights")
        state.add_clue(CLUES["mine_guiding_lights"])
        return "燭色微光像是在引路，將你帶向更深處的敲擊聲。"

    if has_any(action, "final", "chamber", "continue", "go", "forward", "最深處", "房間", "繼續", "前進", "往前"):
        state.move_to_scene("final_chamber")
        return describe_current_scene(state)

    return "坑道越來越狹窄。你可以處理支架、跟隨燭光、搜尋線索，或前往礦坑最深處。"


def handle_final_chamber(state: GameState, action: str) -> str:
    if has_any(action, "rescue", "help", "free", "save", "miners", "救援", "幫助", "放出", "拯救", "礦工"):
        state.set_flag("prioritized_rescue")
        state.ending = "rescue_focused"
        state.ended = True
        state.complete_objective("救出失蹤礦工")
        return ending_text(state)

    if has_any(action, "fight", "attack", "confront", "threat", "danger", "戰鬥", "攻擊", "對抗", "威脅", "危險", "決戰"):
        state.set_flag("prioritized_confrontation")
        state.ending = "confrontation_focused"
        state.ended = True
        state.complete_objective("阻止礦坑威脅")
        return ending_text(state)

    if has_any(action, "truth", "evidence", "reveal", "ask", "investigate", "explain", "真相", "證據", "揭露", "詢問", "調查", "解釋"):
        state.set_flag("prioritized_truth")
        state.ending = "truth_revealing"
        state.ended = True
        state.complete_objective("揭露燭芯礦坑真相")
        return ending_text(state)

    return "礦坑最深處逼你做出選擇：救援、決戰，或揭露真相。"


def ending_text(state: GameState) -> str:
    if state.ending == "rescue_focused":
        return "【救援結局】\n你把失蹤礦工的性命放在第一位。"

    if state.ending == "confrontation_focused":
        return "【決戰結局】\n你正面迎向礦坑裡的危險，暫時阻止了威脅。"

    return "【真相結局】\n你揭開了足夠多的隱情，讓灰堤村無法再用沉默掩蓋這場事件。"


def _move_by_location_keyword(state: GameState, action: str) -> bool:
    if has_any(action, "酒館", "inn") and state.current_scene != "village_inn":
        state.move_to_scene("village_inn")
        return True
    if has_any(action, "廣場", "square") and state.current_scene != "village_square":
        state.move_to_scene("village_square")
        return True
    if has_any(action, "礦坑入口", "入口", "entrance") and state.current_scene != "mine_entrance":
        state.move_to_scene("mine_entrance")
        return True
    if has_any(action, "礦坑深處", "坑道", "interior") and state.current_scene != "mine_interior":
        state.move_to_scene("mine_interior")
        return True
    if has_any(action, "最深處", "final chamber") and state.current_scene != "final_chamber":
        state.move_to_scene("final_chamber")
        return True
    return False


def has_any(text: str, *keywords: str) -> bool:
    return any(keyword in text for keyword in keywords)
