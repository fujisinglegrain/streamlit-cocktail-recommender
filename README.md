# 🍸 프라이빗 바텐더 (Private Bartender)

Python과 Streamlit을 활용한 **맞춤형 칵테일 추천 및 관리 대시보드 웹 애플리케이션**입니다.  
사용자의 취향(알코올 도수, 단맛/드라이함, 기주 등)을 기반으로 최적의 칵테일을 추천하며,  
관리자 모드를 통해 레시피를 실시간으로 관리할 수 있습니다.

---

## 👨‍🎓 제출자 정보

- **학번:** 2020204080  
- **이름:** 황승훈  

---

## 🌟 주요 기능

### 1. 사용자 맞춤형 추천 (퀴즈 기반)
- 스무고개 형태의 질문을 통해 취향 분석  
- 디포즈 가이드 / 오마카세 테스트 제공  
- 추천 결과와 함께 추천 이유 설명  

### 2. 로그인 및 세션 관리
- 회원가입 및 로그인 기능  
- 사용자별 상태 유지 (취기 진행도, 마신 기록)  

### 3. 관리자 대시보드 (CRUD)
- `admin` 계정 접속 시  
  - 칵테일 조회  
  - 삭제  
  - 신규 추가  

### 4. 캐싱(Caching) 기능
- `@st.cache_data`를 활용한 데이터 캐싱  
- 데이터 변경 시 캐시 초기화 후 즉시 반영  

---

## 🚀 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📊 프로젝트 데이터 구조 (정규 워딩)

### 🧩 Group
- 김렛
- 마티니
- 맨해튼
- 클리너
- 캄파리
- 커피
- 티키
- 크리미
- 맨즈칵테일
- standalone

---

### 🍸 Base
- 진
- 보드카
- 럼
- 위스키
- 브랜디
- 리큐르

---

### 🏷️ Category
- citrus
- sweet
- fruity
- herbal
- bitter
- spicy
- woody
- creamy
- refreshing
- strong
- dry
- floral
- savory
- tropical

---

### 🍓 Flavor
- lemon, lime, orange, grapefruit, yuzu  
- strawberry, berry, pineapple, apple, cherry  
- melon, passionfruit  
- mint, herbal, elderflower  
- vanilla, chocolate, caramel, coffee  
- cinnamon, pepper, ginger  
- oak, smoke  
- sugar, honey, almond  
- wine, fruit, coconut  
- anise, tomato, milk, cucumber  

---

### ✨ Descriptor
- 상큼함
- 청량함
- 산뜻함
- 가벼움
- 달콤함
- 부드러움
- 크리미함
- 고소함
- 묵직함
- 진함
- 풍부함
- 강렬함
- 스파이시함
- 쌉쌀함
- 우아함
- 향긋함
- 깔끔함
- 드라이함
- 은은함
- 트로피컬
- 과일감
- 복합적
- 균형감

---

## 💡 프로젝트 특징

- 단순 퀴즈 앱이 아닌 **추천 시스템 기반 구조**
- 사용자 상태(주량, 이전 선택)를 반영하는 동적 로직
- 캐싱 + 관리자 제어 기능 포함

---

## 📌 참고

- 본 프로젝트는 로컬 환경에서 실행을 기준으로 제작되었습니다.
- Streamlit 기반 웹 애플리케이션입니다.