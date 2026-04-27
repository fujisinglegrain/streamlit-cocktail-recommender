# 🍸 프라이빗 바텐더 (Private Bartender)

Python과 Streamlit을 활용한 **맞춤형 칵테일 추천 및 관리 대시보드 웹 애플리케이션**입니다. 
사용자의 취향(알코올 도수, 단맛/드라이함, 기주 등)을 정밀하게 분석하여 최적의 칵테일을 추천하며, 관리자 모드를 통해 실시간 레시피 관리 및 캐싱(Caching) 제어 기능을 제공합니다.

## 👨‍🎓 제출자 정보
- **학번:** 2020204080 
- **이름:** 황승훈 

## 🌟 주요 기능
1. **사용자 맞춤형 추천 (디포즈 가이드 & 오마카세 테스트):** 스무고개 형태의 동적 퀴즈를 통해 취향을 분석하고, XAI(설명 가능한 AI) 기법을 모티브로 추천 사유를 함께 제공합니다.
2. **로그인 및 세션 관리:** 회원가입/로그인 기능을 통해 사용자별 상태(취기 진행도, 마신 기록)를 유지합니다.
3. **관리자 대시보드 (CRUD):** `admin` 계정 접속 시 칵테일 데이터 조회, 삭제, 신규 추가가 가능합니다.
4. **명시적 캐싱(Caching) 제어:** 대용량 JSON 데이터를 `@st.cache_data`로 관리하며, 관리자가 데이터를 변경할 때 명시적으로 캐시를 초기화하여 실시간으로 반영합니다.

## 🚀 실행 방법
```bash
# 1. 필요 패키지 설치
pip install -r requirements.txt

# 2. 애플리케이션 실행
streamlit run app.py

프로젝트 내에서 사용한 정규 워딩

group = [
  김렛,
  마티니,
  맨해튼,
  클리너,
  캄파리,
  커피,
  티키,
  크리미,
  맨즈칵테일,
  standalone,
]

base = [
  진,
  보드카,
  럼,
  위스키,
  브랜디,
  리큐르,
]

category = [
  citrus,
  sweet,
  fruity,
  herbal,
  bitter,
  spicy,
  woody,
  creamy,
  refreshing,
  strong,
  dry,
  floral,
  savory,
  tropical
]

flavor = [
  lemon,
  lime,
  orange,
  grapefruit,
  yuzu,
  strawberry,
  berry,
  pineapple,
  apple,
  cherry,
  melon,
  passionfruit,
  mint,
  herbal,
  elderflower,
  vanilla,
  chocolate,
  caramel,
  coffee,
  cinnamon,
  pepper,
  ginger,
  oak,
  smoke,
  sugar,
  honey,
  almond,
  wine,
  fruit,
  coconut,
  anise,
  tomato,
  milk,
  cucumber
]

descriptor = [
  상큼함,
  청량함,
  산뜻함,
  가벼움,
  달콤함,
  부드러움,
  크리미함,
  고소함,
  묵직함,
  진함,
  풍부함,
  강렬함,
  스파이시함,
  쌉쌀함,
  우아함,
  향긋함,
  깔끔함,
  드라이함,
  은은함,
  트로피컬,
  과일감,
  복합적,
  균형감
]