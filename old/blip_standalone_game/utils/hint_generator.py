"""
hint_generator.py
LLM을 사용하여 틀린 질문 기반 힌트를 생성하는 모듈
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# GPT 모델 설정
MODEL_NAME = "gpt-4o-mini"


def generate_hint_from_failures(answer, failed_questions):
    """
    BLIP VQA에서 틀린 질문들을 바탕으로 추상적 힌트를 생성합니다.

    Args:
        answer (str): 정답 랜드마크 이름 (예: "네모탑")
        failed_questions (list): 틀린 질문 리스트
            [{"question": str, "expected": str, "got": str}, ...]

    Returns:
        str: LLM이 생성한 힌트 메시지

    Raises:
        ValueError: OPENAI_API_KEY가 설정되지 않았을 때
    """

    # API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")

    # 틀린 질문 정보를 텍스트로 포맷팅
    failed_info = ""
    if failed_questions:
        failed_info = "\n사용자 사진에서 부족한 특징 (BLIP VQA 결과):\n"
        for i, item in enumerate(failed_questions, 1):
            question = item.get("question", "N/A")
            expected = item.get("expected", "N/A")
            got = item.get("got", "N/A")
            failed_info += f'  {i}. 질문: "{question}"\n'
            failed_info += f"     - 모델 답변: '{got}', 기대 답변: '{expected}'\n"
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
        return hint

    except Exception as e:
        print(f"[Hint Generator] Error generating hint with GPT: {e}")
        # 오류 발생 시 기본 힌트 반환
        return f"다시 한 번 주변을 둘러보세요. '{answer}'와 관련된 특별한 장소가 있을 거예요! 💡"


# 테스트 코드
if __name__ == '__main__':
    print("=== hint_generator.py 테스트 ===\n")

    # 테스트 1: 네모탑
    print("--- 테스트 1: 네모탑 ---")
    test_answer_1 = "네모탑"
    test_failed_1 = [
        {
            "question": "Is the structure shaped like stacked squares?",
            "expected": "yes",
            "got": "no"
        },
        {
            "question": "Is the structure dark-colored?",
            "expected": "yes",
            "got": "no"
        }
    ]

    try:
        hint_1 = generate_hint_from_failures(test_answer_1, test_failed_1)
        print(f"정답: {test_answer_1}")
        print(f"틀린 질문 수: {len(test_failed_1)}")
        print(f"\n생성된 힌트:\n{hint_1}\n")
    except Exception as e:
        print(f"❌ 에러 발생: {e}\n")

    print("=" * 50 + "\n")

    # 테스트 2: 피노키오
    print("--- 테스트 2: 피노키오 ---")
    test_answer_2 = "피노키오"
    test_failed_2 = [
        {
            "question": "Does the statue have a particularly long nose?",
            "expected": "yes",
            "got": "no"
        },
        {
            "question": "Is the object the statue is holding a book?",
            "expected": "no",
            "got": "yes"
        }
    ]

    try:
        hint_2 = generate_hint_from_failures(test_answer_2, test_failed_2)
        print(f"정답: {test_answer_2}")
        print(f"틀린 질문 수: {len(test_failed_2)}")
        print(f"\n생성된 힌트:\n{hint_2}\n")
    except Exception as e:
        print(f"❌ 에러 발생: {e}\n")

    print("=" * 50)
