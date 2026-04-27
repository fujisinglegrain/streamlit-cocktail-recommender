import streamlit as st
import os
import sys
import json # JSON 수정을 위해 추가

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.recommender import (
    load_json, init_user_state, apply_answer, rank_cocktails, 
    bartender_pick, record_served_cocktail, select_next_question, 
    soju_bottles_to_alcohol_ml, generate_explanation, confidence_score
)

st.set_page_config(page_title="프라이빗 바텐더", page_icon="🍸", layout="centered")

# [1] 제출자 정보
st.sidebar.title("👨‍🎓 제출자 정보")
st.sidebar.info("학번: 2020204080\n\n이름: 황승훈")
st.caption("학번: 2020204080 | 이름: 황승훈")

# [2] 캐싱 기능 적용
@st.cache_data
def load_all_data():
    try:
        cocktails = load_json("data/cocktails.json")
        questions = load_json("data/questions.json")
        return cocktails, questions
    except FileNotFoundError as e:
        st.error(f"🚨 데이터 파일을 찾을 수 없습니다: {e}")
        return [], []

cocktails_db, questions_db = load_all_data()

KOR_MAP = {
    "lemon": "레몬🍋", "lime": "라임🍋‍🟩", "orange": "오렌지🍊", "grapefruit": "자몽🍊", "yuzu": "유자🍋",
    "strawberry": "딸기🍓", "berry": "베리류🫐", "peach": "복숭아🍑", "pineapple": "파인애플🍍", "apple": "사과🍎",
    "cherry": "체리🍒", "apricot": "살구🍑", "melon": "멜론🍈", "passionfruit": "패션프루츠🥭",
    "mint": "민트🌿", "basil": "바질🌱", "rosemary": "로즈마리🌿", "herbal": "허브/약초🌿", "elderflower": "엘더플라워🌼",
    "vanilla": "바닐라🍦", "chocolate": "초콜릿🍫", "caramel": "카라멜🍯", "coffee": "커피☕", "cinnamon": "시나몬/계피🍂",
    "pepper": "스파이스/후추🌶️", "ginger": "생강🫚", "oak": "오크/나무향🌲", "smoke": "스모키/연기향💨", "sugar": "달달한 설탕🍬",
    "honey": "꿀🍯", "almond": "견과류/아몬드🥜", "wine": "와인🍷", "coconut": "코코넛🥥", "anise": "아니스/감초🪵",
    "tomato": "토마토🍅", "fruit": "풍부한 과즙🍹",
    "citrus": "시트러스", "sweet": "달콤함", "fruity": "과일향", "bitter": "쌉쌀함", "spicy": "스파이시",
    "woody": "우디", "creamy": "크리미", "refreshing": "청량함", "strong": "강렬함", "dry": "드라이",
    "floral": "향긋함", "savory": "감칠맛", "tropical": "트로피컬"
}

# 🚨 사용자 세션 초기화
if 'user_db' not in st.session_state:
    st.session_state.user_db = {"admin": {"pw": "1234", "name": "관리자"}}
if 'current_user' not in st.session_state:
    st.session_state.current_user = {"id": "", "name": ""}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'step' not in st.session_state: st.session_state.step = "login"
if 'user_state' not in st.session_state: st.session_state.user_state = init_user_state()
if 'history' not in st.session_state: st.session_state.history = []
if 'round_asked_ids' not in st.session_state: st.session_state.round_asked_ids = []
if 'result_drink' not in st.session_state: st.session_state.result_drink = None

# --- 사이드바 로직 ---
if st.session_state.step != "login":
    st.sidebar.divider()
    st.sidebar.subheader("👤 현재 사용자")
    st.sidebar.write(f"**이름:** {st.session_state.current_user['name']}")
    st.sidebar.write(f"**아이디:** {st.session_state.current_user['id']}")
    
    # 🚨 관리자 전용 메뉴 (아이디가 admin일 때만 보임)
    if st.session_state.current_user['id'] == "admin":
        if st.sidebar.button("🛠️ 데이터베이스 관리 (Admin)"):
            st.session_state.step = "admin_page"
            st.rerun()

if st.session_state.step not in ["login", "setup", "admin_page"]:
    st.sidebar.divider()
    st.sidebar.subheader("📜 오늘 마신 기록")
    if not st.session_state.history:
        st.sidebar.write("아직 마신 술이 없습니다.")
    else:
        for i, drink in enumerate(st.session_state.history):
            st.sidebar.write(f"{i+1}. {drink['name']}")

    capacity = st.session_state.user_state.get("capacity_alcohol_ml", 0)
    consumed = st.session_state.user_state.get("consumed_alcohol_ml", 0)
    drunk_ratio = min((consumed / capacity) if capacity > 0 else 0, 1.0)
    
    st.sidebar.write(f"**현재 취기:** {int(drunk_ratio * 100)}%")
    st.sidebar.progress(drunk_ratio)
    if drunk_ratio > 0.85: st.sidebar.error("주량에 다다랐습니다! 오늘의 대미를 장식할 막잔을 준비하세요. 🛑")

if st.session_state.step != "login":
    if st.sidebar.button("바에서 나가기 (로그아웃)"):
        st.session_state.logged_in = False
        st.session_state.step = "login"
        st.session_state.current_user = {"id": "", "name": ""}
        st.session_state.history = []
        st.session_state.user_state = init_user_state()
        st.rerun()

# --- 메인 화면 로직 ---
if st.session_state.step == "login":
    st.title("🍸 프라이빗 바(Bar) 입장")
    login_tab, signup_tab = st.tabs(["로그인", "회원가입"])
    
    with login_tab:
        login_id = st.text_input("아이디", key="login_id")
        login_pw = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("입장하기"):
            if login_id in st.session_state.user_db and st.session_state.user_db[login_id]["pw"] == login_pw:
                st.session_state.logged_in = True
                st.session_state.current_user = {
                    "id": login_id,
                    "name": st.session_state.user_db[login_id]["name"]
                }
                st.session_state.step = "setup"
                st.rerun()
            else:
                st.error("❌ 아이디 또는 비밀번호가 일치하지 않거나 존재하지 않습니다.")
                
    with signup_tab:
        new_id = st.text_input("새 아이디", key="new_id")
        new_name = st.text_input("이름", key="new_name") 
        new_pw = st.text_input("새 비밀번호", type="password", key="new_pw")
        confirm_pw = st.text_input("비밀번호 확인", type="password", key="confirm_pw")
        
        if st.button("가입하기"):
            if not new_id or not new_name or not new_pw:
                st.warning("아이디, 이름, 비밀번호를 모두 입력해주세요.")
            elif new_id in st.session_state.user_db:
                st.error("이미 존재하는 아이디입니다.")
            elif new_pw != confirm_pw:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                st.session_state.user_db[new_id] = {"pw": new_pw, "name": new_name}
                st.success("회원가입 성공! 로그인 탭에서 로그인해주세요.")

# 🚨 관리자 전용 대시보드 로직
elif st.session_state.step == "admin_page":
    st.title("🛠️ 데이터베이스 관리 (Admin)")
    
    tab1, tab2 = st.tabs(["📋 칵테일 조회 및 삭제", "✨ 신규 칵테일 추가"])
    
    # --- 탭 1: 조회 및 삭제 ---
    with tab1:
        st.subheader("현재 등록된 칵테일 목록")
        st.write(f"총 **{len(cocktails_db)}**개의 레시피가 저장되어 있습니다.")
        
        # 데이터프레임으로 예쁘게 띄우기 (리스트 보기 기능)
        st.dataframe(cocktails_db, use_container_width=True)
        
        st.divider()
        st.subheader("🗑️ 칵테일 데이터 삭제")
        # 이름 목록을 셀렉트 박스로 띄워서 안전하게 삭제
        del_target = st.selectbox("삭제할 칵테일 선택", [c["name"] for c in cocktails_db])
        if st.button("선택한 칵테일 삭제하기 🚨"):
            file_path = "data/cocktails.json"
            with open(file_path, "r", encoding="utf-8") as f:
                current_data = json.load(f)
            
            # 선택한 이름과 일치하지 않는 것들만 남김 (삭제 효과)
            updated_data = [c for c in current_data if c["name"] != del_target]
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(updated_data, f, ensure_ascii=False, indent=2)
            
            load_all_data.clear() # 캐시 클리어
            st.rerun() # 즉각 반영

    # --- 탭 2: 신규 추가 (모든 태그 직접 입력) ---
    with tab2:
        st.subheader("새 칵테일 레시피 추가")
        with st.form("add_recipe_form"):
            new_name = st.text_input("칵테일 이름*")
            col1, col2, col3 = st.columns(3)
            with col1:
                new_base = st.selectbox("기주(Base)", ["진", "보드카", "럼", "데킬라", "위스키", "브랜디", "리큐르", "기타"])
            with col2:
                # 🚨 그룹명 직접 입력
                new_group = st.text_input("그룹(Group)", value="standalone")
            with col3:
                new_vol = st.selectbox("용량(Vol)", ["숏드링크", "롱드링크", "온더락"])
            
            new_abv = st.number_input("도수 (ABV %)", min_value=0, max_value=100, value=15)
            
            st.write("---")
            st.caption("여러 개 입력 시 쉼표(,)로 구분해 주세요.")
            new_category = st.text_input("카테고리 (Category)", placeholder="예: sweet, creamy")
            new_flavor = st.text_input("맛/향 노트 (Flavor)", placeholder="예: vanilla, almond")
            new_descriptor = st.text_input("설명 태그 (Descriptor)", placeholder="예: 달콤함, 부드러움")
            new_recipe = st.text_area("레시피 목록 (Recipe)", placeholder="예: 보드카 1oz, 깔루아 1oz")
            new_is_signature = st.checkbox("바텐더 픽으로 지정 (is_bartender_pick)")
            
            submit_btn = st.form_submit_button("데이터베이스에 추가 및 캐시 갱신 🚀")
            
            if submit_btn:
                if not new_name:
                    st.error("칵테일 이름을 필수로 입력해주세요.")
                else:
                    # 🚨 1. 입력받은 한국어 그룹명을 영어 파일명으로 매핑
                    GROUP_FILENAME_MAP = {
                        "김렛": "gimlet", "마티니": "martini", "맨해튼": "manhattan",
                        "클리너": "cleaner", "캄파리": "campari", "커피": "coffee",
                        "티키": "tiki", "크리미": "creamy", "맨즈칵테일": "mans",
                        "standalone": "standalone"
                    }
                    eng_group = GROUP_FILENAME_MAP.get(new_group, "standalone")
                    auto_image_path = f"data/images/group_{eng_group}.jpg"
                    
                    # 🚨 2. JSON 객체 생성 시 image_path 자동 할당
                    new_cocktail = {
                        "id": f"custom_{len(cocktails_db) + 1}",
                        "name": new_name,
                        "base": new_base,
                        "group": new_group,
                        "vol": new_vol,
                        "abv": new_abv,
                        "alcohol_score": min(new_abv // 4, 10),
                        "sweet_to_dry_sour_score": 5,
                        "category": [x.strip() for x in new_category.split(",") if x.strip()],
                        "flavor": [x.strip() for x in new_flavor.split(",") if x.strip()],
                        "descriptor": [x.strip() for x in new_descriptor.split(",") if x.strip()],
                        "recipe": [x.strip() for x in new_recipe.split(",") if x.strip()],
                        "is_bartender_pick": new_is_signature,
                        "image_path": auto_image_path  # 👈 여기에 알아서 들어갑니다!
                    }
                    
                    file_path = "data/cocktails.json"
                    with open(file_path, "r", encoding="utf-8") as f:
                        current_data = json.load(f)
                    
                    current_data.append(new_cocktail)
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(current_data, f, ensure_ascii=False, indent=2)
                    
                    load_all_data.clear() # 캐시 클리어
                    st.rerun() # 즉각 반영

    st.divider()
    if st.button("⬅️ 메인 화면으로 돌아가기"):
        st.session_state.step = "setup"
        st.rerun()

elif st.session_state.step == "setup":
    st.title(f"🙋‍♂️ {st.session_state.current_user['name']}님, 환영합니다.")
    st.subheader("먼저 오늘 어느 정도 드실 예정인지 주량을 파악하겠습니다.")
    bottles = st.slider("평소 소주 주량 (병 기준)", 0.5, 4.0, 1.5, 0.5)
    if st.button("바 테이블에 앉기"):
        st.session_state.user_state["capacity_alcohol_ml"] = soju_bottles_to_alcohol_ml(bottles)
        st.session_state.step = "choose_mode"
        st.rerun()

elif st.session_state.step == "choose_mode":
    round_num = st.session_state.user_state.get("drink_count", 0) + 1
    st.title(f"🥂 {round_num}번째 주문")
    st.write("어떤 방식으로 술을 골라드릴까요?")

    col1, col2 = st.columns(2)
    with col1:
        st.info("내가 원하는 맛이 명확할 때")
        if st.button("🎛️ 디포즈 가이드로 맞추기"):
            st.session_state.step = "route_a"
            st.rerun()
    with col2:
        st.success("바텐더에게 내 기분을 맡길 때")
        if st.button("🔮 감성 취향 테스트 (오마카세)"):
            st.session_state.step = "route_b_testing"
            st.session_state.round_asked_ids = []
            st.session_state.user_state["idk_count"] = 0
            st.session_state.user_state["forced_pick"] = False
            st.rerun()

elif st.session_state.step == "route_a":
    st.subheader("🎛️ 디포즈 가이드 세팅")
    alc_score = st.slider("알코올 타격감 (0: 논알콜 ~ 10: 독주)", 0, 10, 5)
    sweet_dry_score = st.slider("맛의 밸런스 (0: Sweet ~ 10: Dry/Sour)", 0, 10, 5)
    
    col1, col2 = st.columns(2)
    with col1:
        base_pref = st.selectbox("선호하는 기주(Base)", ["상관없음", "진", "보드카", "럼", "데킬라", "위스키", "브랜디", "리큐르"])
    with col2:
        unique_groups = sorted(list(set(c.get("group", "standalone") for c in cocktails_db)))
        group_list = ["상관없음"] + unique_groups
        
        GROUP_DISPLAY_MAP = {"캄파리": "비터스윗", "standalone": "독보적"}
        def format_group_name(g):
            if g == "상관없음": return "상관없음"
            return GROUP_DISPLAY_MAP.get(g, g)

        group_pref = st.selectbox("선호하는 스타일(Group)", group_list, format_func=format_group_name)

    if st.button("추천 받기 🍸"):
        best_drink = None
        min_penalty = float('inf')
        for drink in cocktails_db:
            if any(d.get("id") == drink.get("id") for d in st.session_state.history):
                continue
            
            penalty = 0
            penalty += abs(drink.get('alcohol_score', 5) - alc_score) * 2
            penalty += abs(drink.get('sweet_to_dry_sour_score', 5) - sweet_dry_score) * 2
            
            if base_pref != "상관없음" and drink.get('base') != base_pref: penalty += 10
            if group_pref != "상관없음" and drink.get('group') != group_pref: penalty += 10
                
            if penalty < min_penalty:
                min_penalty = penalty
                best_drink = drink
        
        st.session_state.result_drink = best_drink or cocktails_db[0]
        st.session_state.step = "result"
        st.rerun()

elif st.session_state.step == "route_b_testing":
    current_round = st.session_state.user_state.get("drink_count", 0) + 1
    exclude_list = [d.get("id") for d in st.session_state.history if d.get("id")]
    
    if st.session_state.user_state.get("idk_count", 0) >= 3:
        sig_drink = bartender_pick(cocktails_db, st.session_state.user_state, exclude_ids=exclude_list)
        st.session_state.result_drink = sig_drink or cocktails_db[0]
        st.session_state.user_state["forced_pick"] = True
        st.session_state.step = "result"
        st.rerun()

    ranked = rank_cocktails(cocktails_db, st.session_state.user_state, exclude_ids=exclude_list, round_num=current_round)
    next_q = select_next_question(questions_db, st.session_state.user_state, st.session_state.round_asked_ids, ranked)

    mode = st.session_state.user_state.get("mode", "normal")
    asked_count = len(st.session_state.round_asked_ids)
    
    if mode == "same_group": min_required_q = 2
    elif mode in ["same_group_with_variation", "switch_group"]: min_required_q = 3
    else: min_required_q = 4
        
    max_q = 7
    is_confident = False
    
    if asked_count >= min_required_q:
        conf = confidence_score(ranked)
        if conf >= 0.20:
            is_confident = True

    if not next_q or is_confident or asked_count >= max_q:
        st.session_state.result_drink = ranked[0] if ranked else cocktails_db[0]
        st.session_state.step = "result"
        st.rerun()

    st.subheader(f"바텐더의 질문 ({asked_count + 1}번째)")
    
    if next_q["id"] == "final_decider": st.caption(f"🍷 취기가 기분 좋게 올랐네요. 분위기를 무르익게 할 시간입니다.")
    elif next_q["id"] == "avoid_flavor": st.caption(f"📝 손님의 취향 베이스라인을 그리는 중입니다.")
    else: 
        conf_percent = int(confidence_score(ranked) * 100)
        st.caption(f"🔍 손님의 취향을 좁히는 중입니다... (1위 적합도: {ranked[0]['_score']}점 / 확신도: {conf_percent}%)")

    st.write(f"**{next_q['question']}**")
    
    options = [ans["text"] for ans in next_q["answers"]]
    choice = st.radio("선택해주세요:", options, index=None)

    if st.button("선택 완료"):
        if choice:
            selected_ans = next(ans for ans in next_q["answers"] if ans["text"] == choice)
            
            if next_q.get("type") == "action":
                action_type = selected_ans.get("action")
                if action_type == "recommend_signature":
                    sig_drink = bartender_pick(cocktails_db, st.session_state.user_state, exclude_ids=exclude_list)
                    st.session_state.result_drink = sig_drink or ranked[0]
                    st.session_state.step = "result"
                    st.rerun()
                elif action_type == "continue":
                    pass 

            if next_q["id"] in ["avoid_flavor", "challenge_dislike"]:
                st.session_state.user_state["global_asked_ids"].append(next_q["id"])
            else:
                st.session_state.round_asked_ids.append(next_q["id"])
            
            st.session_state.user_state = apply_answer(st.session_state.user_state, selected_ans)
            st.rerun()
        else:
            st.warning("선택지를 골라주세요!")

elif st.session_state.step == "result":
    drink = st.session_state.result_drink
    st.balloons()
    
    pick_label = "🌟 바텐더 픽 " if drink.get('is_bartender_pick') else ""
    st.success(f"## {pick_label}추천: {drink['name']}")

    current_round = st.session_state.user_state.get("drink_count", 0) + 1
    explanations = generate_explanation(drink, st.session_state.user_state, current_round)
    
    with st.expander("🤔 바텐더는 왜 이 술을 추천했을까요?", expanded=True):
        for reason in explanations:
            for eng, kor in KOR_MAP.items():
                if f"[{eng}]" in reason:
                    reason = reason.replace(f"[{eng}]", f"[{kor}]")
            st.info(reason)
    
    col1, col2 = st.columns([1, 1.5])
    with col1:
        if 'image_path' in drink and os.path.exists(drink['image_path']):
            st.image(drink['image_path'], use_container_width=True)
        else:
            st.info("📷 현재 이 주류의 사진은 준비 중입니다.")
            
    with col2:
        st.write(f"**🍸 베이스:** {drink.get('base', '알 수 없음')} | **그룹:** {drink.get('group', '알 수 없음')}")
        st.write(f"**📏 도수:** {drink.get('abv', 0)}% | **용량:** {drink.get('vol', '알 수 없음')}")
        st.write(f"**📝 레시피:** {', '.join(drink.get('recipe', []))}")
        
        all_tags = drink.get('category', []) + drink.get('flavor', []) + drink.get('descriptor', [])
        if all_tags: st.write(f"**✨ 특징:** {', '.join(all_tags)}")
            
        st.write("---")
        st.write(f"**알코올 타격감 ({drink.get('alcohol_score', 0)}/10)**")
        st.progress(drink.get('alcohol_score', 0) / 10.0)
        st.write(f"**단맛 ↔ 드라이함 ({drink.get('sweet_to_dry_sour_score', 0)}/10)**")
        st.progress(drink.get('sweet_to_dry_sour_score', 0) / 10.0)

    st.divider()
    st.write("이 술이 마음에 드시나요?")
    
    if st.button("🥃 이 잔을 마시겠습니다 (주량 기록)"):
        st.session_state.user_state = record_served_cocktail(st.session_state.user_state, drink)
        st.session_state.history.append(drink)
        st.session_state.step = "choose_mode"
        st.rerun()
        
    if st.button("🔄 다른 술로 다시 추천받기"):
        st.session_state.step = "choose_mode"
        st.rerun()