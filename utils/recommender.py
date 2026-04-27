import json
from typing import Any, Dict, List, Optional

SOJU_BOTTLE_ML = 360
SOJU_ABV = 0.165
STANDARD_COCKTAIL_VOLUME = {
    "숏드링크": 90,
    "롱드링크": 180,
    "온더락": 90
}

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def soju_bottles_to_alcohol_ml(bottles: float) -> float:
    return bottles * SOJU_BOTTLE_ML * SOJU_ABV

def cocktail_alcohol_ml(cocktail: Dict[str, Any]) -> float:
    vol = cocktail.get("vol", "숏드링크")
    volume_ml = STANDARD_COCKTAIL_VOLUME.get(vol, 120)
    abv = cocktail.get("abv", 0) / 100
    return volume_ml * abv

def init_user_state() -> Dict[str, Any]:
    return {
        "weights": {"group": {}, "base": {}, "category": {}, "flavor": {}, "descriptor": {}},
        "negative_weights": {"group": {}, "base": {}, "category": {}, "flavor": {}, "descriptor": {}},
        "capacity_alcohol_ml": None,
        "consumed_alcohol_ml": 0,
        "drink_count": 0,
        "last_cocktail_id": None,
        "last_group": None,
        "mode": "normal",
        "challenge_dislikes": False,
        "global_asked_ids": [],
        "idk_count": 0,
        "forced_pick": False
    }

def add_score(target: Dict[str, Dict[str, float]], section: str, key: str, value: float) -> None:
    target.setdefault(section, {})
    target[section][key] = target[section].get(key, 0) + value

def apply_answer(user_state: Dict[str, Any], answer: Dict[str, Any]) -> Dict[str, Any]:
    for block_name in ["weights", "negative_weights"]:
        block = answer.get(block_name, {})
        for section, values in block.items():
            if section.endswith("_range"):
                user_state[block_name][section] = values
                continue
            for key, value in values.items():
                add_score(user_state[block_name], section, key, value)

    action = answer.get("action")
    if action == "same_group": user_state["mode"] = "same_group"
    elif action == "same_group_with_variation": user_state["mode"] = "same_group_with_variation"
    elif action == "switch_group": user_state["mode"] = "switch_group"
    elif action == "reset_search": user_state["mode"] = "reset_search"
    elif action == "soften_dislikes": user_state["challenge_dislikes"] = True
    elif action == "keep_dislikes": user_state["challenge_dislikes"] = False
    elif action == "idk": user_state["idk_count"] = user_state.get("idk_count", 0) + 1
    
    return user_state

def match_list_score(cocktail_values: List[str], wanted: Dict[str, float], weight: float = 1.0) -> float:
    score = 0
    for value in cocktail_values:
        score += wanted.get(value, 0) * weight
    return score

def calc_capacity_ratio(user_state: Dict[str, Any]) -> Optional[float]:
    capacity = user_state.get("capacity_alcohol_ml")
    if not capacity or capacity <= 0: return None
    return user_state.get("consumed_alcohol_ml", 0) / capacity

def alcohol_capacity_adjustment(cocktail: Dict[str, Any], user_state: Dict[str, Any]) -> float:
    ratio = calc_capacity_ratio(user_state)
    if ratio is None: return 0
    abv = cocktail.get("abv", 0)
    score = 0
    if ratio < 0.2:
        if abv >= 24: score += 4
        elif abv <= 12: score -= 2
    elif ratio < 0.5:
        if 12 <= abv <= 24: score += 2
    elif ratio < 0.7:
        if abv <= 15: score += 5
        if abv >= 24: score -= 5
    elif ratio < 0.9:
        if abv <= 12: score += 7
        if cocktail.get("is_starter"): score += 3
        if abv >= 20: score -= 8
    else:
        if abv <= 8: score += 6
        if abv >= 15: score -= 15
    return score

def first_drink_adjustment(cocktail: Dict[str, Any], user_state: Dict[str, Any]) -> float:
    if user_state.get("drink_count", 0) > 0: return 0
    score = 0
    if cocktail.get("is_starter"): score += 6
    if cocktail.get("vol") == "롱드링크": score += 4
    if cocktail.get("abv", 0) <= 15: score += 3
    if cocktail.get("group") == "클리너": score += 5
    if cocktail.get("vol") == "숏드링크": score -= 2
    return score

def group_mode_adjustment(cocktail: Dict[str, Any], user_state: Dict[str, Any]) -> float:
    mode = user_state.get("mode", "normal")
    last_group = user_state.get("last_group")
    if not last_group or last_group == "standalone": return 0
    
    current_group = cocktail.get("group")
    score = 0
    
    if mode in ["same_group", "same_group_with_variation"]:
        if current_group == last_group: 
            score += 15
        else: 
            score -= 10
            
    elif mode in ["switch_group", "reset_search"]:
        if current_group == last_group: 
            score -= 15
        else: 
            score += 4
            
    return score

def score_cocktail(cocktail: Dict[str, Any], user_state: Dict[str, Any], round_num: int = 1) -> float:
    weights = user_state.get("weights", {})
    negatives = user_state.get("negative_weights", {})
    score = 0

    group = cocktail.get("group")
    base = cocktail.get("base")

    score += weights.get("group", {}).get(group, 0) * 3
    score += weights.get("base", {}).get(base, 0) * 2
    score += match_list_score(cocktail.get("category", []), weights.get("category", {}), 3)
    score += match_list_score(cocktail.get("flavor", []), weights.get("flavor", {}), 2)
    score += match_list_score(cocktail.get("descriptor", []), weights.get("descriptor", {}), 1.5)

    dislike_multiplier = 0.2 if user_state.get("challenge_dislikes") else 1.0
    score -= negatives.get("group", {}).get(group, 0) * 4 * dislike_multiplier
    score -= negatives.get("base", {}).get(base, 0) * 3 * dislike_multiplier
    score -= match_list_score(cocktail.get("category", []), negatives.get("category", {}), 4) * dislike_multiplier
    score -= match_list_score(cocktail.get("flavor", []), negatives.get("flavor", {}), 4) * dislike_multiplier
    score -= match_list_score(cocktail.get("descriptor", []), negatives.get("descriptor", {}), 2) * dislike_multiplier

    score += first_drink_adjustment(cocktail, user_state)
    score += alcohol_capacity_adjustment(cocktail, user_state)
    score += group_mode_adjustment(cocktail, user_state)

    return round(score, 2)

def rank_cocktails(cocktails: List[Dict[str, Any]], user_state: Dict[str, Any], exclude_ids: Optional[List[str]] = None, top_n: int = 5, round_num: int = 1) -> List[Dict[str, Any]]:
    exclude_ids = exclude_ids or []
    ranked = []
    for cocktail in cocktails:
        if cocktail.get("id") in exclude_ids: continue
        item = dict(cocktail)
        item["_score"] = score_cocktail(cocktail, user_state, round_num)
        ranked.append(item)
    ranked.sort(key=lambda x: x["_score"], reverse=True)
    return ranked[:top_n]

def confidence_score(ranked: List[Dict[str, Any]]) -> float:
    if len(ranked) < 2: return 1.0
    top1 = ranked[0]["_score"]
    top2 = ranked[1]["_score"]
    if top1 <= 0: return 0
    return min(1.0, max(0, (top1 - top2) / max(top1, 1)))

def should_use_bartender_pick(user_state: Dict[str, Any]) -> bool:
    return user_state.get("idk_count", 0) >= 2

def bartender_pick(cocktails: List[Dict[str, Any]], user_state: Dict[str, Any], exclude_ids: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    candidates = [c for c in cocktails if c.get("is_bartender_pick")]
    if not candidates: return None
    ranked = rank_cocktails(candidates, user_state, exclude_ids=exclude_ids, top_n=1)
    return ranked[0] if ranked else None

def record_served_cocktail(user_state: Dict[str, Any], cocktail: Dict[str, Any]) -> Dict[str, Any]:
    user_state["drink_count"] += 1
    user_state["last_cocktail_id"] = cocktail.get("id")
    user_state["last_group"] = cocktail.get("group")
    user_state["consumed_alcohol_ml"] += cocktail_alcohol_ml(cocktail)
    user_state["mode"] = "normal"
    user_state["idk_count"] = 0
    user_state["forced_pick"] = False
    return user_state

def select_next_question(questions: List[Dict[str, Any]], user_state: Dict[str, Any], round_asked_ids: List[str], ranked: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    qmap = {q["id"]: q for q in questions}
    global_asked = user_state.get("global_asked_ids", [])
    drink_count = user_state.get("drink_count", 0)
    ratio = calc_capacity_ratio(user_state)

    if drink_count == 0:
        if "avoid_flavor" not in global_asked: return qmap.get("avoid_flavor")
        if "intro_mood" not in round_asked_ids: return qmap.get("intro_mood")

    if drink_count > 0:
        if "after_last_drink" not in round_asked_ids: return qmap.get("after_last_drink")
        mode = user_state.get("mode")
        if mode == "same_group_with_variation" and "variation_direction" not in round_asked_ids:
            return qmap.get("variation_direction")
        if mode in ["switch_group", "reset_search"] and "switch_direction" not in round_asked_ids:
            return qmap.get("switch_direction")

    if drink_count >= 2 and ratio is not None and (0.4 <= ratio <= 0.6):
        if "challenge_dislike" not in global_asked:
            return qmap.get("challenge_dislike")

    if should_use_bartender_pick(user_state):
        if "bartender_pick" not in round_asked_ids:
            return qmap.get("bartender_pick")

    if ratio is not None and ratio >= 0.6:
        if "final_decider" not in round_asked_ids: return qmap.get("final_decider")

    all_asked = global_asked + round_asked_ids
    excluded_from_random = [
        "final_decider", "variation_direction", "switch_direction", 
        "mid_round_status", "after_last_drink", "avoid_flavor", 
        "intro_mood", "challenge_dislike", "bartender_pick"
    ]

    valid_candidates = [
        q for q in questions 
        if q["id"] not in all_asked 
        and q.get("type") != "action"
        and q["id"] not in excluded_from_random
    ]

    if not valid_candidates: return None
    valid_candidates.sort(key=lambda q: q.get("priority", 0), reverse=True)
    return valid_candidates[0]

def generate_explanation(cocktail: Dict[str, Any], user_state: Dict[str, Any], round_num: int) -> List[str]:
    reasons = []
    ratio = calc_capacity_ratio(user_state)
    abv = cocktail.get("abv", 0)

    # 🚨 강제 픽 (잘 모르겠어요 3번 누적)
    if user_state.get("forced_pick"):
        reasons.append("😎 계속 결정을 어려워하시는 것 같아, 호불호 없이 누구나 사랑하는 바텐더의 필살기를 강제로 준비했습니다. 일단 한 번 믿고 드셔보세요!")
        return reasons

    # 🚨 [추가된 로직] 칵테일 데이터에 is_bartender_pick이 true라면 무조건 시그니처 멘트 출력
    if cocktail.get("is_bartender_pick"):
        if user_state.get("idk_count", 0) >= 2:
            reasons.append("💡 손님의 고민을 덜어드리기 위해 준비한 **바텐더의 시그니처입니다.**")
        else:
            reasons.append("🌟 이 칵테일은 저희 바에서 가장 자신 있게 내어드리는 **바텐더의 시그니처입니다.**")

    # 첫 잔 보정
    if round_num == 1 and (cocktail.get("group") == "클리너" or cocktail.get("is_starter")):
        reasons.append("🥂 입맛을 돋우고 오늘 자리를 산뜻하게 시작하기 위해 첫 잔에 완벽한 칵테일로 준비했습니다.")

    # 주량 보정
    if ratio is not None:
        if ratio >= 0.7 and abv <= 15:
            reasons.append("📉 주량에 꽤 다다르셨기에, 부담 없이 편하게 즐길 수 있는 저도수 위주로 세팅했습니다.")
        elif ratio < 0.2 and abv >= 20:
            reasons.append("🔥 아직 알코올 여유가 있으시네요! 초반에 기분 좋게 취기를 올려줄 묵직한 도수로 골랐습니다.")

    # 취향 매칭
    matched_tags = []
    weights = user_state.get("weights", {})
    for key in ["base", "category", "flavor", "descriptor"]:
        cocktail_tags = cocktail.get(key, [])
        if isinstance(cocktail_tags, str): cocktail_tags = [cocktail_tags]
        for tag in cocktail_tags:
            if weights.get(key, {}).get(tag, 0) > 0:
                matched_tags.append(tag)

    if matched_tags:
        display_tags = list(set(matched_tags))[:3]
        tag_str = ", ".join(display_tags)
        reasons.append(f"✨ 테스트에서 선택하신 **[{tag_str}]** 취향이 이 칵테일에 완벽하게 녹아있습니다.")

    # 비선호 도발
    if user_state.get("challenge_dislikes"):
        reasons.append("🎯 처음에 피하고 싶다 하셨던 향이 살짝 감돌지만, 바텐더를 믿고 도전해 볼 만한 마스터피스입니다.")

    # 그룹 연계
    mode = user_state.get("mode")
    last_group = user_state.get("last_group")
    if mode in ["same_group", "same_group_with_variation"] and cocktail.get("group") == last_group:
        reasons.append("🔄 직전 잔이 마음에 드셨다기에, 비슷한 매력을 가진 결로 이어가도록 조주했습니다.")
    elif mode in ["switch_group", "reset_search"] and cocktail.get("group") != last_group:
        reasons.append("🎭 이전과는 완전히 다른 분위기로 새롭게 기분을 환기해 드릴 한 잔입니다.")

    # 이유가 아무것도 없을 때 기본 멘트
    if not reasons:
        reasons.append("🍸 손님의 복합적인 취향 밸런스를 고려해 섬세하게 매칭한 결과입니다.")

    return reasons