"""
answer_loader.py
answer.json에서 랜덤하게 오늘의 정답을 선택하는 모듈
"""

import json
import random
import os


def get_random_answer():
    """
    answer.json에서 랜덤하게 하나의 미션을 선택합니다.

    Returns:
        tuple: (answer, hint)
        예: ("네모탑", "마트료시카")

    Raises:
        FileNotFoundError: answer.json 파일을 찾을 수 없을 때
        ValueError: answer.json 형식이 올바르지 않을 때
    """
    # answer.json 파일 경로 (blip_standalone_game 루트 기준)
    # utils/ -> blip_standalone_game/ -> data/answer.json
    answer_json_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'data',
        'answer.json'
    )

    # 파일 존재 여부 확인
    if not os.path.exists(answer_json_path):
        raise FileNotFoundError(f"answer.json 파일을 찾을 수 없습니다: {answer_json_path}")

    # JSON 파일 로드
    try:
        with open(answer_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"answer.json 파일 형식이 올바르지 않습니다: {e}")

    # missions 배열 확인
    if 'missions' not in data or not isinstance(data['missions'], list):
        raise ValueError("answer.json에 'missions' 배열이 없거나 형식이 올바르지 않습니다")

    if len(data['missions']) == 0:
        raise ValueError("missions 배열이 비어 있습니다")

    # 랜덤 선택
    mission = random.choice(data['missions'])

    # answer와 hint 추출
    answer = mission.get('answer')
    hint = mission.get('hint')

    if not answer or not hint:
        raise ValueError("선택된 미션에 'answer' 또는 'hint'가 없습니다")

    return (answer, hint)


# 테스트 코드
if __name__ == '__main__':
    print("=== answer_loader.py 테스트 ===\n")

    try:
        for i in range(3):
            answer, hint = get_random_answer()
            print(f"테스트 {i+1}:")
            print(f"  정답: {answer}")
            print(f"  힌트: {hint}\n")
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
