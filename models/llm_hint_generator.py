# models/llm_hint_generator.py

import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# .env 파일 로드는 가능할 때만 수행
if load_dotenv is not None:
    load_dotenv()

# GPT 모델 설정
MODEL_NAME = "gpt-4o-mini"


def _get_default_hint(answer):
    return (
        f"다시 한 번 주변을 둘러보세요. '{answer}'와 관련된 특별한 장소가 있을 거예요! 💡"
    )


def _get_openai_client():
    """필요할 때만 OpenAI 클라이언트를 생성합니다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, None

    try:
        from openai import OpenAI
    except ImportError:
        print("⚠️ openai 패키지가 설치되지 않았습니다. 기본 힌트를 사용합니다.")
        return None, api_key

    try:
        return OpenAI(api_key=api_key), api_key
    except Exception as e:
        print(f"⚠️ OpenAI 클라이언트 초기화 실패: {e}")
        return None, api_key


def generate_blip_hint(answer, blip_failed_questions=None):
    """
    BLIP VQA에서 틀린 질문들을 바탕으로 추상적 힌트를 생성합니다.

    Args:
        answer (str): 정답 랜드마크 이름 (예: "네모탑")
        blip_failed_questions (list): 틀린 질문 리스트
            [{"question": str, "expected_answer": str, "model_answer": str}, ...]

    Returns:
        str: LLM이 생성한 힌트 메시지

    Raises:
        ValueError: OPENAI_API_KEY가 설정되지 않았을 때
    """

    # API 키 확인
    client, api_key = _get_openai_client()
    if not api_key:
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. 기본 힌트를 사용합니다.")
        return _get_default_hint(answer)
    if not client:
        return _get_default_hint(answer)

    if blip_failed_questions is None:
        blip_failed_questions = []

    # 틀린 질문 정보를 텍스트로 포맷팅
    failed_info = ""
    if blip_failed_questions:
        failed_info = "\n사용자 사진에서 부족한 특징 (BLIP VQA 결과):\n"
        for i, item in enumerate(blip_failed_questions, 1):
            question = item.get("question", "N/A")
            expected_answer = item.get("expected_answer", "N/A")
            model_answer = item.get("model_answer", "N/A")
            failed_info += f'  {i}. 질문: "{question}"\n'
            failed_info += f"     - 모델 답변: '{model_answer}', 기대 답변: '{expected_answer}'\n"
    else:
        failed_info = "\n사용자 사진에서 부족한 특징: (정보 없음)\n"

    # 시스템 프롬프트
    system_prompt = """당신은 파주 출판단지 보물찾기 게임의 힌트 제공자입니다.
사용자가 촬영한 사진이 정답 랜드마크가 아닐 때, 추상적이고 창의적인 힌트를 제공하는 역할을 합니다.

### 힌트 작성 가이드라인:
1. 정답 랜드마크 이름을 직접 언급하지 마세요.
2. 2-3문장의 짧고 감성적인 힌트를 작성하세요.
3. 은유적이고 시적인 표현을 사용하세요.
4. BLIP VQA 결과를 바탕으로 사진에 없는 특징을 간접적으로 암시하거나, 잘못 인식된 특징을 정답과 대조하세요.
5. 사용자가 다시 도전하고 싶은 마음이 들도록 격려하세요.
6. 항상 한국어로 작성하세요.
7. 너무 들뜨거나 장난스러운 톤은 피해주세요.

### 힌트 작성 예시:

**예시 1: 정답의 특징이 사진에 없을 때 (기대 답변 'yes', 모델 답변 'no')**
- **정답:** 피노키오
- **입력 정보:**
    - 질문: "Does the statue have a particularly long nose?"
    - 모델 답변: 'no', 기대 답변: 'yes'
- **좋은 힌트:** "진실의 무게를 코 끝으로 증명하는 친구를 찾아보세요. 때로는 작은 거짓말이 가장 큰 특징이 되기도 한답니다."
- **나쁜 힌트:** "코가 긴 인형을 찾아보세요." (너무 직접적임)

**예시 2: 정답이 아닌 다른 대상을 찍었을 때 (기대 답변 'no', 모델 답변 'yes')**
- **정답:** 네모탑
- **입력 정보:**
    - 질문: "Are there any books in the photo?"
    - 모델 답변: 'yes', 기대 답변: 'no' (사용자가 책이 많은 '지혜의 숲'을 찍었다고 가정)
- **좋은 힌트:** "이야기가 잠든 고요한 숲도 아름답지만, 우리가 찾는 보물은 하늘을 향해 지혜를 층층이 쌓아 올린 곳에 숨겨져 있어요."
- **나쁜 힌트:** "책이 아니라 탑을 찍어야 해요." (너무 직접적임)

### 주의사항:
- 잘못된 특징(모델이 'yes'라고 했지만 'no'가 기대됨)은 오답임을 명확히 하세요.
- 부족한 특징(모델이 'no'라고 했지만 'yes'가 기대됨)은 간접적으로 암시하세요.
"""

    # 사용자 프롬프트
    user_prompt = f"""정답 랜드마크: {answer}
{failed_info}

위 정보를 바탕으로 사용자가 정답에 더 가까이 다가갈 수 있도록 추상적이고 창의적인 힌트를 생성해주세요."""

    print(f"✅ LLM 힌트 생성 시도 (API 키 설정됨, 길이: {len(api_key)}자)")

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,  # 창의적인 힌트를 위해 높은 temperature 설정
            max_tokens=200
        )

        hint = response.choices[0].message.content.strip()
        print("✅ LLM 힌트 생성 성공")
        return hint

    except Exception as e:
        print(f"❌ Error generating hint with GPT: {e}")
        # 오류 발생 시 기본 힌트 반환
        return _get_default_hint(answer)




def generate_clip_hint(answer, clip_info):

    # API 키 확인
    client, api_key = _get_openai_client()
    if not api_key:
        print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. 기본 힌트를 사용합니다.")
        return _get_default_hint(answer)
    if not client:
        return _get_default_hint(answer)

    # clip_info
    failed_info = ""
    if clip_info:
        failed_info = "\n사용자 사진에서 부족한 감성 (CLIP 결과):\n"
        question = clip_info[0].get("question", "N/A")
        model_answer = clip_info[0].get("model_answer", "N/A")
        expected_answer = clip_info[0].get("expected_answer", "N/A")
    
        failed_info += f'  질문: "{question}"\n'
        failed_info += f"  - 모델 답변: '{model_answer}'\n"
        failed_info += f"  - 기대 답변: '{expected_answer}'\n"
    else:
        failed_info = "\n사용자 사진에서 부족한 감성: (정보 없음)\n"
    '''
        틀렸을시 : 
            # 감정 정보 반환 (힌트 생성용)
            f"질문: 이 장소에서 {kw} 분위기가 느껴지나요?",
            f"model answer: 아니요, 이 장소는 {moods} 분위기가 더 강하게 느껴져요.",
            f"expected answer: 네, 이 장소는 {kw} 분위기가 느껴져요."
    '''

    # 시스템 프롬프트
    system_prompt = """당신은 파주 출판단지 감성 찾기 게임의 힌트 제공자입니다.
사용자가 촬영한 사진이 정답 감성이 아닐 때, 추상적이고 창의적인 힌트를 제공하는 역할을 합니다.

### 힌트 작성 가이드라인: 
1. 2-3문장의 짧고 감성적인 힌트를 작성하세요.
2. 장소의 분위기를 시각적, 청각적, 촉각적 요소로 구체화하여 상상할 수 있도록 작성하세요.
3. CLIP 결과에서 모델이 예측한 분위기 키워드를 시각적 요소(색감, 빛, 공간감, 분위기)를 중심으로 작성하세요.
4. CLIP 결과에서 모델이 예측한 분위기 키워드가 많을수록 사용자에게 정답 힌트를 더 자세히 주세요.
5. CLIP 결과에서 모델이 예측한 분위기 키워드를 각각 한줄씩 단 하나도 빠뜨리지 말고 모두 언급하세요. 
6. 사용자가 다시 도전하고 싶은 마음이 들도록 격려하세요.
7. 항상 한국어로 작성하세요.
8. 너무 들뜨거나 장난스러운 톤은 피해주세요.

### 힌트 작성 예시:

**예시 1: 모델의 답변에서 나타나는 분위기가 적을 때 (분위기 개수 3개 이하)**
- **정답:** 자연적인
- **입력 정보:**
    - 질문: "이 장소에서 자연적인 분위기가 느껴지나요?"
    - 모델 답변: "아니요, 이 장소는 활기찬, 신비로운 분위기 순서대로 더 강하게 느껴져요."
    - 기대 답변: "네, 이 장소는 자연적인 분위기가 느껴져요' (이 예시에서는 모델 답변에서 나타나는 분위기가 활기찬, 신비로운 2개임)"
- **좋은 힌트:** "이 사진에서는 이런 점들이 돋보였어요.
                매우 활발한 기운의 활기찬 느낌을 받았습니다.
                묘한 빛의 신비로운 분위기 또한 느껴졌습니다. 
                우리가 찾는 자연은 그보다 조금 더 따스한 숨결을 품고 있답니다. 고요한 바람과 햇살의 감촉에 집중해 보세요"
- **나쁜 힌트:** "사진 분석 결과 활기찬, 신비로운 2개만 담고 있습니다." (너무 직접적임)

**예시 2: 모델의 답변에서 나타나는 분위기가 많을 때 (분위기 개수 4개 이상)**
- **정답:** 옛스러운
- **입력 정보:**
    - 질문: "이 장소에서 옛스러운 분위기가 느껴지나요?"
    - 모델 답변: "아니요, 이 장소는 웅장한, 활기찬, 신비로운, 화사한, 자연적인 분위기 순서대로 더 강하게 느껴져요."
    - 기대 답변: "네, 이 장소는 옛스러운 분위기가 느껴져요' (이 예시에서는 모델 답변에서 나타나는 분위기가 웅장한, 활기찬, 신비로운, 화사한, 자연적인 5개임)"
- **좋은 힌트:** "방금 담아주신 사진은 이렇게 보였어요. 참 인상적인 순간이네요.
                하늘을 향해 뻗은 거대한 공간감에서 웅장한 느낌을 받았습니다.
                생명력이 넘치는 초록빛에서 활기찬 기운이 느껴졌고요.
                빛과 그림자가 묘하게 얽혀 신비로운 분위기를 자아냈습니다.
                다채로운 색감이 어우러져 전반적으로 화사한 인상을 주었네요.
                인공적이지 않은, 풍경 그대로의 자연적인 모습도 함께 담겼습니다.
                우리가 찾는 옛스러움은 이처럼 화려한 빛깔과는 조금 다른 결을 가지고 있어요."
- **나쁜 힌트:** "사진 분석 결과 웅장한, 활기찬, 신비로운, 화사한, 자연적인 5개만 담고 있습니다." 
"""

    # 사용자 프롬프트
    user_prompt = f"""정답 분위기: {answer}
{failed_info}

위 정보를 바탕으로 사용자가 정답에 더 가까이 다가갈 수 있도록 힌트를 생성해주세요.
"""

    print(f"✅ LLM 힌트 생성 시도 (API 키 설정됨, 길이: {len(api_key)}자)")

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,  # 창의적인 힌트를 위해 높은 temperature 설정
            max_tokens=200
        )

        hint = response.choices[0].message.content.strip()
        print("✅ LLM 힌트 생성 성공")
        return hint

    except Exception as e:
        print(f"❌ Error generating hint with GPT: {e}")
        # 오류 발생 시 기본 힌트 반환
        return _get_default_hint(answer)





if __name__ == "__main__":
    # 테스트 예시
    print("=== LLM Hint Generator 테스트 ===\n")

    # 예시 1: 피노키오
    print("--- 예시 1: 피노키오 ---")
    test_answer_1 = "피노키오"
    test_blip_questions_1 = [
        {
            "question": "Does the statue have a particularly long nose?",
            "model_answer": "no",
            "expected_answer": "yes"
        },
        {
            "question": "Is the statue wearing green-colored clothes?",
            "model_answer": "no",
            "expected_answer": "yes"
        },
        {
            "question": "Is the object the statue is holding a book?",
            "model_answer": "yes",
            "expected_answer": "no"
        }
    ]
    
    print(f"정답: {test_answer_1}")
    print(f"BLIP 실패 질문 수: {len(test_blip_questions_1)}")
    
    hint_1 = generate_blip_hint(test_answer_1, test_blip_questions_1)
    print("\n생성된 힌트:")
    print(hint_1)
    print("\n" + "="*50 + "\n")
    
    # 예시 2: 지혜의숲 조각상
    print("--- 예시 2: 지혜의숲 조각상 ---")
    test_answer_2 = "지혜의숲 조각상"
    test_blip_questions_2 = [
        {"question": "Is the sculpture made of glass?", "model_answer": "yes", "expected_answer": "no"},
        {"question": "Does the sculpture have a tail?", "model_answer": "yes", "expected_answer": "no"},
        {"question": "Is the sculpture standing up?", "model_answer": "yes", "expected_answer": "no"},
        {"question": "Is the sculpture holding an object to its eyes?", "model_answer": "no", "expected_answer": "yes"},
        {"question": "Is the sculpture in a sitting position?", "model_answer": "no", "expected_answer": "yes"}
    ]

    print(f"정답: {test_answer_2}")
    print(f"BLIP 실패 질문 수: {len(test_blip_questions_2)}")

    hint_2 = generate_blip_hint(test_answer_2, test_blip_questions_2)
    print("\n생성된 힌트:")
    print(hint_2)
    print("\n" + "="*50 + "\n")
