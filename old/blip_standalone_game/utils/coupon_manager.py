"""
coupon_manager.py
정답 시 쿠폰을 발급하는 모듈
"""

import datetime
import random
import string
import os


def issue_coupon(answer):
    """
    정답 시 쿠폰 코드를 생성합니다.

    Args:
        answer (str): 정답 랜드마크 이름 (예: "네모탑")

    Returns:
        str: 쿠폰 코드 (예: "COUPON-네모탑-20250109-A7B3")
    """

    # 타임스탬프 생성 (YYYYMMDD 형식)
    timestamp = datetime.datetime.now().strftime("%Y%m%d")

    # 랜덤 코드 생성 (4자리 대문자 + 숫자)
    random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

    # 쿠폰 코드 생성
    coupon = f"COUPON-{answer}-{timestamp}-{random_code}"

    # (선택) 쿠폰을 파일에 저장
    _save_coupon_to_file(coupon, answer)

    return coupon


def _save_coupon_to_file(coupon, answer):
    """
    쿠폰 코드를 파일에 저장합니다. (선택적 기능)

    Args:
        coupon (str): 쿠폰 코드
        answer (str): 정답 랜드마크 이름
    """

    # coupons 폴더 경로 (blip_standalone_game 루트 기준)
    # utils/ -> blip_standalone_game/ -> coupons/
    coupons_dir = os.path.join(
        os.path.dirname(__file__),
        '..',
        'coupons'
    )

    # 폴더가 없으면 생성
    if not os.path.exists(coupons_dir):
        os.makedirs(coupons_dir)

    # 쿠폰 파일 경로 (coupons.txt)
    coupons_file = os.path.join(coupons_dir, 'coupons.txt')

    # 현재 시간
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 파일에 추가 (append mode)
    try:
        with open(coupons_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {coupon} (정답: {answer})\n")
        print(f"[Coupon Manager] Coupon saved to '{coupons_file}'")
    except Exception as e:
        print(f"[Coupon Manager] Error saving coupon to file: {e}")


# 테스트 코드
if __name__ == '__main__':
    print("=== coupon_manager.py 테스트 ===\n")

    # 테스트 1: 네모탑 쿠폰 발급
    print("--- 테스트 1: 네모탑 쿠폰 발급 ---")
    coupon_1 = issue_coupon("네모탑")
    print(f"발급된 쿠폰: {coupon_1}\n")

    # 테스트 2: 피노키오 쿠폰 발급
    print("--- 테스트 2: 피노키오 쿠폰 발급 ---")
    coupon_2 = issue_coupon("피노키오")
    print(f"발급된 쿠폰: {coupon_2}\n")

    # 테스트 3: 여러 개 발급
    print("--- 테스트 3: 여러 개 연속 발급 ---")
    for i in range(3):
        coupon = issue_coupon("테스트")
        print(f"{i+1}. {coupon}")

    print("\n쿠폰이 'coupons/coupons.txt' 파일에 저장되었습니다.")
