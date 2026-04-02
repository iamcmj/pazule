"""
blip_checker.py
BLIP VQA를 사용하여 사진이 정답인지 판별하는 모듈
"""

import os
import json
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForQuestionAnswering


# --- 디바이스 설정 ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- 모델 이름 ---
MODEL_NAME = "Salesforce/blip-vqa-base"

# --- 미션 성공 기준 (75%) ---
SUCCESS_THRESHOLD = 0.75

# --- 전역 변수 (모델과 데이터 캐싱용) ---
_processor = None
_model = None
_landmark_qa_data = None


def _load_model():
    """BLIP VQA 모델과 프로세서를 로드합니다. (최초 1회만 실행)"""
    global _processor, _model

    if _processor is not None and _model is not None:
        return _processor, _model

    print(f"[BLIP Checker] Loading BLIP VQA model '{MODEL_NAME}' on device '{DEVICE}'...")
    try:
        _processor = BlipProcessor.from_pretrained(MODEL_NAME)
        _model = BlipForQuestionAnswering.from_pretrained(MODEL_NAME).to(DEVICE)
        print("[BLIP Checker] Model loaded successfully.")
        return _processor, _model
    except Exception as e:
        print(f"[BLIP Checker] Error loading model: {e}")
        return None, None


def _load_landmark_qa():
    """랜드마크별 Q&A 데이터를 JSON 파일에서 로드합니다. (최초 1회만 실행)"""
    global _landmark_qa_data

    if _landmark_qa_data is not None:
        return _landmark_qa_data

    # landmark_qa_labeled.json 경로 설정 (blip_standalone_game 루트 기준)
    # utils/ -> blip_standalone_game/ -> data/landmark_qa_labeled.json
    qa_json_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'data',
        'landmark_qa_labeled.json'
    )

    try:
        with open(qa_json_path, 'r', encoding='utf-8') as f:
            _landmark_qa_data = json.load(f)
            print(f"[BLIP Checker] Landmark Q&A data loaded from '{qa_json_path}'.")
            return _landmark_qa_data
    except FileNotFoundError:
        print(f"[BLIP Checker] Error: File not found at '{qa_json_path}'.")
        return {}
    except json.JSONDecodeError as e:
        print(f"[BLIP Checker] Error: Failed to decode JSON: {e}")
        return {}


def check_answer_with_blip(image_path, answer):
    """
    BLIP VQA를 사용하여 사용자 이미지가 정답인지 판별합니다.

    Args:
        image_path (str): 사용자가 업로드한 이미지 경로
        answer (str): 정답 랜드마크 이름 (예: "네모탑")

    Returns:
        tuple: (is_correct, failed_questions)
        - is_correct (bool): True=정답, False=오답
        - failed_questions (list): 틀린 질문들의 상세 정보
            [{"question": str, "expected": str, "got": str}, ...]

    Raises:
        FileNotFoundError: 이미지 파일을 찾을 수 없을 때
        ValueError: 모델 로드 실패 또는 데이터 없을 때
    """

    # 1. 모델 로드
    processor, model = _load_model()
    if processor is None or model is None:
        raise ValueError("BLIP 모델을 로드할 수 없습니다.")

    # 2. Q&A 데이터 로드
    landmark_qa_data = _load_landmark_qa()
    if not landmark_qa_data:
        raise ValueError("landmark_qa_labeled.json 데이터를 로드할 수 없습니다.")

    # 3. 해당 랜드마크의 질문 리스트 가져오기
    question_list = landmark_qa_data.get(answer)
    if not question_list:
        raise ValueError(f"'{answer}'에 대한 Q&A 데이터가 없습니다.")

    total_questions = len(question_list)
    if total_questions == 0:
        raise ValueError(f"'{answer}'의 Q&A 리스트가 비어 있습니다.")

    # 4. 이미지 로드
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    try:
        raw_image = Image.open(image_path).convert('RGB')
    except Exception as e:
        raise ValueError(f"이미지 로드 실패: {e}")

    # 5. VQA 실행 및 정확도 계산
    correct_count = 0
    failed_questions = []

    try:
        pixel_values = processor(images=raw_image, return_tensors="pt").pixel_values.to(DEVICE)
    except Exception as e:
        raise ValueError(f"이미지 전처리 실패: {e}")

    print(f"[BLIP Checker] Running VQA for '{answer}' ({total_questions} questions)...")

    for item in question_list:
        question = item[0]
        expected_answer = item[1]

        try:
            inputs = processor(text=question, return_tensors="pt").to(DEVICE)

            out = model.generate(
                pixel_values=pixel_values,
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=10
            )

            model_answer = processor.decode(out[0], skip_special_tokens=True).strip().lower()

            if model_answer == expected_answer:
                correct_count += 1
            else:
                # 틀린 질문 상세 정보 저장
                failed_questions.append({
                    "question": question,
                    "expected": expected_answer,
                    "got": model_answer
                })

        except Exception as e:
            print(f"[BLIP Checker] Error during VQA for question '{question}': {e}")
            failed_questions.append({
                "question": question,
                "expected": expected_answer,
                "got": "error"
            })

    # 6. 최종 성공 여부 판별
    accuracy = correct_count / total_questions
    is_correct = accuracy >= SUCCESS_THRESHOLD

    print(f"[BLIP Checker] Result: {correct_count}/{total_questions} correct ({accuracy:.2%})")
    print(f"[BLIP Checker] Is correct: {is_correct}")

    return (is_correct, failed_questions)


# 테스트 코드
if __name__ == '__main__':
    print("=== blip_checker.py 테스트 ===\n")

    # 테스트 이미지 경로 (blip_standalone_game 루트 기준)
    # utils/ -> blip_standalone_game/ -> test_images/test4.jpg
    test_image_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'test_images',
        'test4.jpg'
    )
    test_landmark = "네모탑"

    print(f"테스트 이미지: {test_image_path}")
    print(f"테스트 랜드마크: {test_landmark}\n")

    if not os.path.exists(test_image_path):
        print(f"❌ 테스트 이미지가 존재하지 않습니다: {test_image_path}")
    else:
        try:
            is_correct, failed = check_answer_with_blip(test_image_path, test_landmark)

            print("\n=== 테스트 결과 ===")
            print(f"정답 여부: {is_correct}")

            if not is_correct:
                print(f"\n틀린 질문 ({len(failed)}개):")
                for item in failed:
                    print(f"  - 질문: {item['question']}")
                    print(f"    예상: '{item['expected']}', 실제: '{item['got']}'")
            else:
                print("✅ 모든 질문을 통과했습니다!")

        except Exception as e:
            print(f"❌ 에러 발생: {e}")
