"""
game.py
BLIP Standalone 보물찾기 게임 메인 로직
"""

import os
import sys

# utils 모듈 import
from utils import (
    get_random_answer,
    check_answer_with_blip,
    generate_hint_from_failures,
    issue_coupon
)


def print_header():
    """게임 시작 헤더 출력"""
    print("=" * 60)
    print("🎯 파주 출판단지 보물찾기 게임 (BLIP Standalone Version)")
    print("=" * 60)
    print()


def print_footer():
    """게임 종료 푸터 출력"""
    print()
    print("=" * 60)
    print("게임을 종료합니다. 감사합니다! 👋")
    print("=" * 60)


def main():
    """
    메인 게임 루프

    1. 오늘의 정답/힌트 출력
    2. 사용자 입력 대기 (이미지 경로 or 'quit')
    3. BLIP으로 검증
    4. 정답 → 쿠폰 지급 및 종료
       오답 → LLM 힌트 생성 및 재시도
    """

    # 게임 시작
    print_header()

    # 1. 오늘의 정답 선택
    try:
        answer, initial_hint = get_random_answer()
        print(f"🎯 오늘의 보물찾기 힌트: {initial_hint}")
        print()
        print("📸 해당 장소의 사진을 찍어서 제출해주세요!")
        print("💡 사진 경로를 입력하거나 'quit'을 입력하여 종료할 수 있습니다.")
        print()
    except Exception as e:
        print(f"❌ 정답 로드 실패: {e}")
        print("answer.json 파일을 확인해주세요.")
        return

    # 2. 게임 루프
    attempt = 0

    while True:
        attempt += 1
        print("-" * 60)
        print(f"🔍 시도 #{attempt}")
        print("-" * 60)

        # 사용자 입력
        image_path = input("사진 경로를 입력하세요 (또는 'quit' 입력): ").strip()

        # 종료 명령
        if image_path.lower() == 'quit':
            print("\n게임을 중단합니다.")
            break

        # 빈 입력 체크
        if not image_path:
            print("⚠️  사진 경로를 입력해주세요.\n")
            continue

        # 파일 존재 여부 확인
        if not os.path.exists(image_path):
            print(f"⚠️  파일을 찾을 수 없습니다: {image_path}")
            print("경로를 다시 확인해주세요.\n")
            continue

        print()
        print("🔄 BLIP VQA로 검증 중...")
        print()

        # BLIP 검증
        try:
            is_correct, failed_questions = check_answer_with_blip(image_path, answer)
        except Exception as e:
            print(f"❌ 검증 중 오류 발생: {e}")
            print("다시 시도해주세요.\n")
            continue

        # 정답 처리
        if is_correct:
            print("=" * 60)
            print("🎉 정답입니다! 축하합니다!")
            print("=" * 60)
            print()

            # 쿠폰 발급
            coupon = issue_coupon(answer)
            print(f"🎁 쿠폰이 발급되었습니다!")
            print(f"   {coupon}")
            print()
            print(f"✅ 정답: {answer}")
            print(f"✅ 총 시도 횟수: {attempt}회")
            print()

            break

        # 오답 처리
        else:
            print("=" * 60)
            print("❌ 오답입니다!")
            print("=" * 60)
            print()

            # LLM 힌트 생성
            print("💭 힌트를 생성하는 중...")
            print()

            try:
                hint = generate_hint_from_failures(answer, failed_questions)
                print("💡 힌트:")
                print(f"   {hint}")
                print()
            except Exception as e:
                print(f"⚠️  힌트 생성 실패: {e}")
                print(f"   기본 힌트: 다시 한 번 주변을 둘러보세요!\n")

            print("🔄 다시 도전해보세요!\n")

    # 게임 종료
    print_footer()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n게임이 중단되었습니다. (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류 발생: {e}")
        sys.exit(1)
