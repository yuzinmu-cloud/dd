from __future__ import annotations

from game_state import GameState


ADVENTURE_TITLE_DISPLAY = "燭芯礦坑事件"

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
    "village_inn": "你站在村裡唯一還亮著燈的酒館中。濕透的旅人低聲交談，酒館老闆看著你的眼神比她願意承認的更警覺。",
    "village_square": "村莊廣場被雨水沖得發亮。幾名村民聚在告示牌旁，村長努力壓低眾人的恐慌。",
    "mine_entrance": "礦坑入口在山脊下張著黑暗的口。破裂的警告牌掛在木樁上，新鮮的腳印一路消失在坑道裡。",
    "mine_interior": "礦坑深處傳來滴水聲。腐朽的支架在黑暗中傾斜，燭色微光在更深處緩緩游移。",
    "final_chamber": "你抵達礦坑最深處。失蹤礦工的線索、怪異燭光，以及村子隱瞞的祕密都在這裡交會。",
}

FLAG_LABELS = {
    "questioned_innkeeper": "詢問過酒館老闆",
    "met_village_leader": "見過村長",
    "heard_family_plea": "聽見失蹤礦工家屬的請求",
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
    notes = "\n".join(f"- {note}" for note in state.notes) if state.notes else "尚未記錄"
    flags = "\n".join(f"- {FLAG_LABELS.get(flag, flag)}" for flag in sorted(state.flags)) if state.flags else "尚未觸發"
    scene_name = SCENE_NAMES.get(state.current_scene, state.current_scene)
    return (
        "====================\n"
        "目前狀態\n"
        "====================\n"
        f"冒險：{ADVENTURE_TITLE_DISPLAY}\n"
        f"目前位置：{scene_name}\n"
        f"回合數：{state.turn_count}\n"
        "線索：\n"
        f"{notes}\n"
        "事件：\n"
        f"{flags}\n"
        "===================="
    )


def handle_action(state: GameState, action: str) -> str:
    cleaned = action.strip().lower()
    state.record_action(action)

    if state.ended:
        return ending_text(state)

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
    if has_any(action, "innkeeper", "talk", "ask", "question", "rumor", "老闆", "酒館老闆", "交談", "詢問", "打聽", "傳聞"):
        state.set_flag("questioned_innkeeper")
        state.add_note("酒館老闆暗示，礦坑異光是在上一批探勘隊回來之後才開始出現的。")
        return (
            "酒館老闆擦著早已乾淨的杯子，聲音壓得很低。她承認，那些燭色微光是在上一批探勘隊蒼白返村後才出現的。"
            "她朝窗外的廣場看了一眼，暗示村長正在那裡安撫失蹤者的家屬。"
        )

    if has_any(action, "square", "leave", "outside", "leader", "families", "continue", "廣場", "離開", "外面", "村長", "家屬", "繼續"):
        state.advance_scene()
        return describe_current_scene(state)

    state.add_note("酒館裡氣氛緊繃，酒館老闆似乎隱瞞了某些事情。")
    return (
        "你環顧酒館：泥濘的靴印、沉默的礦工、牆上一張用炭筆標出礦坑道路的舊地圖。"
        "遊戲主持人給出明確的下一步：你可以詢問酒館老闆，或前往村莊廣場。"
    )


def handle_village_square(state: GameState, action: str) -> str:
    if has_any(action, "leader", "mayor", "elder", "quiet", "briefing", "村長", "長老", "安靜", "簡報", "說明"):
        state.set_flag("met_village_leader")
        state.add_note("村長希望事情在恐慌擴散前低調解決。")
        return (
            "村長把你帶到雨聲較小的屋簷下。他承認村子需要找回失蹤礦工，卻也害怕消息傳開後再也沒有人敢靠近這裡。"
            "他同意讓你前往礦坑入口調查。"
        )

    if has_any(action, "relative", "family", "miner", "missing", "urgent", "家屬", "親人", "礦工", "失蹤", "急", "求助"):
        state.set_flag("heard_family_plea")
        state.add_note("失蹤礦工的親人相信，有人曾聽見封閉坑道裡傳出敲擊聲。")
        return (
            "一名失蹤礦工的親人抓住你的袖口，懇求你不要等到天亮。"
            "他說，有人在舊封閉坑道下方聽見過微弱的敲擊聲。"
        )

    if has_any(action, "mine", "entrance", "ridge", "go", "continue", "礦坑", "入口", "山脊", "前往", "繼續"):
        state.advance_scene()
        return describe_current_scene(state)

    return (
        "雨水沿著廣場石縫流成銀線。你可以和村長談談，聽失蹤礦工家屬說明，"
        "或直接往礦坑入口前進。"
    )


def handle_mine_entrance(state: GameState, action: str) -> str:
    if has_any(action, "tracks", "boot", "footprint", "inspect", "search", "腳印", "靴印", "檢查", "調查", "搜尋"):
        state.set_flag("found_fresh_tracks")
        state.add_note("新鮮腳印通往廢棄礦坑，但沒有任何離開的痕跡。")
        return (
            "你在泥地裡蹲下。新鮮腳印一路通往礦坑深處，雨水卻沒有沖出任何返回的痕跡。"
            "不論發生了什麼，失蹤者很可能進去了，卻沒有出來。"
        )

    if has_any(action, "sign", "warning", "listen", "light", "lantern", "告示", "警告", "聆聽", "光", "燭光", "提燈"):
        state.set_flag("noticed_warning_signs")
        state.add_note("舊警告牌提到支架不穩與封閉下層坑道。")
        return (
            "你的提燈照亮一塊裂開的警告牌：支架不穩、下層封閉、日落後禁止進入。"
            "就在這時，一點燭色微光從坑道深處回應似地閃了一下。"
        )

    if has_any(action, "enter", "inside", "mine", "go", "continue", "進入", "裡面", "礦坑", "前進", "繼續"):
        state.advance_scene()
        return describe_current_scene(state)

    return "礦坑在雨中沉默地等待。你可以檢查腳印、查看警告牌、在入口聆聽，或直接進入。"


def handle_mine_interior(state: GameState, action: str) -> str:
    if has_any(action, "beam", "danger", "careful", "avoid", "brace", "支架", "危險", "小心", "避開", "撐住", "加固"):
        state.set_flag("handled_environmental_danger")
        state.add_note("你小心處理了礦坑內不穩的支架。")
        return (
            "你放慢腳步，用一段斷木撐住下沉的橫樑後才通過。橫樑後方，你發現一枚掉落的礦工識別牌。"
            "這座礦坑很危險，但危險並非毫無脈絡。有人曾倉皇經過這裡。"
        )

    if has_any(action, "light", "follow", "clue", "token", "deeper", "sound", "光", "燭光", "跟隨", "線索", "識別牌", "更深", "聲音"):
        state.set_flag("followed_strange_lights")
        state.add_note("奇異燭光將你引向礦坑最深處。")
        return (
            "燭色微光在前方漂移，始終保持著一步之遙。它們沒有攻擊你，反而像是在引路。"
            "低沉的敲擊聲從礦坑最深處傳來。"
        )

    if has_any(action, "final", "chamber", "continue", "go", "forward", "最深處", "房間", "繼續", "前進", "往前"):
        state.advance_scene()
        return describe_current_scene(state)

    return (
        "坑道越來越狹窄。你可以處理不穩的支架、跟隨奇異燭光、搜尋線索，"
        "或繼續前往礦坑最深處。"
    )


def handle_final_chamber(state: GameState, action: str) -> str:
    if has_any(action, "rescue", "help", "free", "save", "miners", "救援", "幫助", "放出", "拯救", "礦工"):
        state.set_flag("prioritized_rescue")
        state.ending = "rescue_focused"
        state.ended = True
        return ending_text(state)

    if has_any(action, "fight", "attack", "confront", "threat", "danger", "戰鬥", "攻擊", "對抗", "威脅", "危險", "決戰"):
        state.set_flag("prioritized_confrontation")
        state.ending = "confrontation_focused"
        state.ended = True
        return ending_text(state)

    if has_any(action, "truth", "evidence", "reveal", "ask", "investigate", "explain", "真相", "證據", "揭露", "詢問", "調查", "解釋"):
        state.set_flag("prioritized_truth")
        state.ending = "truth_revealing"
        state.ended = True
        return ending_text(state)

    return (
        "礦坑最深處逼你做出選擇。你可以優先救出失蹤礦工，正面對抗眼前的危險，"
        "或揭露燭芯礦坑事件背後的真相。"
    )


def ending_text(state: GameState) -> str:
    if state.ending == "rescue_focused":
        return (
            "【救援結局】\n"
            "你把失蹤礦工的性命放在第一位。村子或許仍會爭論責任歸屬，但至少有人活著回到了雨中。"
        )

    if state.ending == "confrontation_focused":
        return (
            "【決戰結局】\n"
            "你正面迎向礦坑裡的危險，暫時阻止了威脅。只是燭芯礦坑仍有一些真相，被埋在黑暗裡。"
        )

    return (
        "【真相結局】\n"
        "你揭開了足夠多的隱情，讓灰堤村無法再用沉默掩蓋這場事件。雨還在下，但村子已經不同了。"
    )


def has_any(text: str, *keywords: str) -> bool:
    return any(keyword in text for keyword in keywords)
