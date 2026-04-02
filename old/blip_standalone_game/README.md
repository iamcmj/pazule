# BLIP Standalone 보물찾기 게임

파주 출판단지 보물찾기 게임의 단순화된 버전입니다.
BLIP VQA 모델만을 사용하여 사용자가 제출한 사진이 정답인지 판별하고, 오답 시 LLM이 생성한 힌트를 제공합니다.

---

## 🎯 게임 플로우

1. 게임이 시작되면 `answer.json`에서 랜덤하게 오늘의 정답을 선택합니다.
2. 사용자에게 초기 힌트를 제공합니다. (예: "마트료시카")
3. 사용자가 사진 경로를 입력합니다.
4. BLIP VQA로 사진이 정답인지 판별합니다.
   - **정답**: 쿠폰을 발급하고 게임을 종료합니다.
   - **오답**: 틀린 질문 리스트를 기반으로 LLM이 힌트를 생성하여 제공합니다.
5. 사용자는 힌트를 참고하여 다시 사진을 제출할 수 있습니다.

---

## 📂 파일 구조

```
blip_standalone_game/
├── project_plan.md           # 프로젝트 계획 문서
├── todo_list.md               # 진행 상황 체크리스트
├── game.py                    # 메인 게임 로직 ⭐
├── README.md                  # 본 파일
├── data/                      # 데이터 파일
│   ├── answer.json            # 정답 및 힌트 데이터
│   └── landmark_qa_labeled.json  # BLIP VQA 질문 데이터
├── test_images/               # 테스트용 이미지
│   ├── test2.jpg
│   ├── test3.jpg
│   └── test4.jpg
├── utils/                     # 유틸리티 모듈
│   ├── __init__.py
│   ├── answer_loader.py       # answer.json 랜덤 로드
│   ├── blip_checker.py        # BLIP VQA 체커
│   ├── hint_generator.py      # LLM 힌트 생성
│   └── coupon_manager.py      # 쿠폰 발급 로직
└── coupons/                   # 쿠폰 저장 폴더 (자동 생성)
    └── coupons.txt            # 발급된 쿠폰 목록
```

---

## 📦 설치 방법

### 1. 필수 라이브러리 설치

```bash
pip install torch transformers pillow openai python-dotenv
```

### 2. 환경 변수 설정

프로젝트 루트 디렉토리 (`blip_standalone_game/`)에 `.env` 파일을 생성하고 OpenAI API 키를 추가합니다:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 데이터 파일 확인

다음 데이터 파일이 프로젝트 내부에 있는지 확인합니다:

- `data/answer.json`
- `data/landmark_qa_labeled.json`

이 파일들은 이미 프로젝트에 포함되어 있습니다.

---

## 🚀 사용 방법

### 게임 실행

```bash
cd blip_standalone_game
python game.py
```

### 게임 플레이

1. 게임이 시작되면 오늘의 힌트가 출력됩니다.
2. 해당 장소의 사진을 촬영합니다.
3. 사진 경로를 입력합니다. (예: `C:\path\to\photo.jpg`)
4. BLIP이 사진을 검증합니다.
   - 정답이면 쿠폰이 발급되고 게임이 종료됩니다.
   - 오답이면 힌트가 제공되며 다시 시도할 수 있습니다.
5. 게임을 종료하려면 `quit`을 입력합니다.

---

## 💡 사용 예시

```bash
$ python game.py

============================================================
🎯 파주 출판단지 보물찾기 게임 (BLIP Standalone Version)
============================================================

🎯 오늘의 보물찾기 힌트: 마트료시카

📸 해당 장소의 사진을 찍어서 제출해주세요!
💡 사진 경로를 입력하거나 'quit'을 입력하여 종료할 수 있습니다.

------------------------------------------------------------
🔍 시도 #1
------------------------------------------------------------
사진 경로를 입력하세요 (또는 'quit' 입력): test1.jpg

🔄 BLIP VQA로 검증 중...

[BLIP Checker] Running VQA for '네모탑' (8 questions)...
[BLIP Checker] Result: 4/8 correct (50.00%)
[BLIP Checker] Is correct: False

============================================================
❌ 오답입니다!
============================================================

💭 힌트를 생성하는 중...

💡 힌트:
   층층이 쌓인 구조를 찾아보세요. 어두운 색감의 탑 모양 조형물이에요.

🔄 다시 도전해보세요!

------------------------------------------------------------
🔍 시도 #2
------------------------------------------------------------
사진 경로를 입력하세요 (또는 'quit' 입력): test2.jpg

🔄 BLIP VQA로 검증 중...

[BLIP Checker] Running VQA for '네모탑' (8 questions)...
[BLIP Checker] Result: 7/8 correct (87.50%)
[BLIP Checker] Is correct: True

============================================================
🎉 정답입니다! 축하합니다!
============================================================

🎁 쿠폰이 발급되었습니다!
   COUPON-네모탑-20250109-A7B3

✅ 정답: 네모탑
✅ 총 시도 횟수: 2회

============================================================
게임을 종료합니다. 감사합니다! 👋
============================================================
```

---

## 🔧 주요 모듈 설명

### 1. `answer_loader.py`

- `answer.json`에서 랜덤하게 오늘의 정답을 선택합니다.
- 반환값: `(answer, hint)` 튜플

### 2. `blip_checker.py`

- BLIP VQA 모델을 사용하여 사진이 정답인지 판별합니다.
- `landmark_qa_labeled.json`의 질문 리스트로 검증합니다.
- 정확도 75% 이상이면 정답으로 판정합니다.
- 반환값: `(is_correct, failed_questions)` 튜플

### 3. `hint_generator.py`

- OpenAI GPT-4o-mini를 사용하여 힌트를 생성합니다.
- 틀린 질문 리스트를 프롬프트에 포함하여 추상적 힌트를 생성합니다.
- 반환값: 힌트 문자열

### 4. `coupon_manager.py`

- 정답 시 쿠폰 코드를 생성합니다.
- 쿠폰은 `coupons/coupons.txt` 파일에 자동으로 저장됩니다.
- 형식: `COUPON-{랜드마크}-{날짜}-{랜덤코드}`

### 5. `game.py`

- 메인 게임 루프를 제어합니다.
- 위 모듈들을 조합하여 전체 게임 플로우를 구현합니다.

---

## ⚙️ 설정

### BLIP 모델

- 모델: `Salesforce/blip-vqa-base`
- 디바이스: CUDA (GPU) 또는 CPU (자동 선택)
- 성공 기준: 75% 이상의 정확도

### LLM 모델

- 모델: `gpt-4o-mini`
- Temperature: 0.7 (창의적인 힌트 생성)
- Max Tokens: 200

---

## ⚠️ 주의사항

1. **경로 문제**: 절대 경로를 사용하는 것을 권장합니다.
2. **모델 로딩**: BLIP 모델은 처음 로드 시 시간이 소요됩니다. (GPU 권장)
3. **API 비용**: OpenAI API 호출 시 비용이 발생합니다.
4. **이미지 형식**: JPG, PNG 등 일반적인 이미지 형식을 지원합니다. (HEIC는 `pillow-heif` 설치 필요)

---

## 🧪 테스트 방법

각 모듈은 개별적으로 테스트할 수 있습니다:

```bash
# answer_loader 테스트
python utils/answer_loader.py

# blip_checker 테스트 (테스트 이미지 경로 수정 필요)
python utils/blip_checker.py

# hint_generator 테스트 (.env 파일 필요)
python utils/hint_generator.py

# coupon_manager 테스트
python utils/coupon_manager.py
```

---

## 📈 향후 확장 가능성

1. **웹 인터페이스**: Flask/FastAPI로 웹 서버 구축
2. **CLIP 추가**: 감정 분석 미션 추가 (2단계 검증)
3. **리더보드**: 시도 횟수/시간 기록, 순위 시스템
4. **데이터베이스 연동**: 쿠폰을 DB에 저장, 사용자 프로필 관리
5. **시도 횟수 제한**: 5회 제한 후 자동 종료
6. **힌트 단계별 제공**: 1차 힌트 → 2차 힌트 (점점 구체적으로)

---

## 📝 프로젝트 정보

본 프로젝트는 BLIP VQA 모델을 활용한 단독 실행형(standalone) 보물찾기 게임입니다.

**주요 특징:**

- 상대 경로 사용으로 어디서든 실행 가능
- 자체 포함된 데이터 파일 (data/, test_images/)
- 모듈화된 구조로 유지보수 용이
