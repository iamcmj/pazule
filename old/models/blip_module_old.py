# /models/blip_module.py

import os
import json
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForQuestionAnswering


# --- 디바이스 설정 ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"BLIP Module: Using device '{DEVICE}'")

# --- 모델 이름 ---
MODEL_NAME = "Salesforce/blip-vqa-base"

# --- 랜드마크별 Q&A JSON 파일 경로 ---
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(MODULE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LANDMARK_QA_FILE = os.path.join(DATA_DIR, "landmark_qa.json")

# --- 미션 성공 기준 (75%) ---
SUCCESS_THRESHOLD = 0.75


# =====================================
# 모델 및 데이터 전역 로드 (성능 최적화)
# =====================================

def load_model():
    """BLIP VQA 모델과 프로세서를 로드합니다."""
    print(f"Loading BLIP VQA model '{MODEL_NAME}'...")
    try:
        processor = BlipProcessor.from_pretrained(MODEL_NAME)
        model = BlipForQuestionAnswering.from_pretrained(MODEL_NAME).to(DEVICE)
        print("BLIP VQA model loaded successfully.")
        return processor, model
    except Exception as e:
        print(f"Error loading BLIP model: {e}")
        return None, None

def load_landmark_qa():
    """랜드마크별 Q&A 데이터를 JSON 파일에서 로드합니다."""
    try:
        with open(LANDMARK_QA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Landmark Q&A data loaded from '{LANDMARK_QA_FILE}'.")
            return data
    except FileNotFoundError:
        print(f"Error: Landmark Q&A file not found at '{LANDMARK_QA_FILE}'.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from '{LANDMARK_QA_FILE}'.")
        return {}

# --- 모델과 데이터 로드 ---
processor, model = load_model()
landmark_qa_data = load_landmark_qa()


# =====================================
# 메인 함수
# =====================================

def check_with_blip(user_image_path, landmark_name):
    """
    BLIP VQA를 사용해 사용자 이미지가 해당 랜드마크가 맞는지 검증합니다.
    JSON에 정의된 질문 리스트를 수행하고 'yes' 답변의 비율을 계산합니다.

    Args:
        user_image_path (str): 사용자가 업로드한 이미지 파일 경로
        landmark_name (str): 오늘의 정답 랜드마크 이름 (예: "피노키오")

    Returns:
        tuple: (is_success, hint_payload)
               is_success (bool): 미션 성공 여부 (True/False)
               hint_payload (list): 'no'로 답변된 질문 목록 (LLM 힌트 생성용)
    """
    
    # --- 0. 모델 로드 확인 ---
    if not processor or not model:
        print("Error: BLIP model is not loaded. Aborting mission.")
        return False, []
        
    # --- 1. 랜드마크에 해당하는 질문 리스트 가져오기 ---
    question_list = landmark_qa_data.get(landmark_name)

    if not question_list:
        print(f"Warning: No Q&A data found for landmark '{landmark_name}'.")
        return False, []

    total_questions = len(question_list)
    if total_questions == 0:
        print(f"Warning: Empty Q&A list for landmark '{landmark_name}'.")
        return False, []

    # --- 2. 이미지 로드 ---
    try:
        raw_image = Image.open(user_image_path).convert('RGB')
    except FileNotFoundError:
        print(f"Error: User image not found at '{user_image_path}'.")
        return False, []
    except Exception as e:
        print(f"Error loading image '{user_image_path}': {e}")
        return False, []

    # --- 3. VQA 실행 및 'yes' 카운트 ---
    yes_count = 0
    no_questions_list = [] # 'no' 답변된 질문 저장용

    try:
        pixel_values = processor(images=raw_image, return_tensors="pt").pixel_values.to(DEVICE)
    except Exception as e:
        print(f"Error processing image with BLIP: {e}")
        return False, []

    print(f"Running VQA for landmark '{landmark_name}' ({total_questions} questions)...")

    for question in question_list:
        try:
            inputs = processor(text=question, return_tensors="pt").to(DEVICE)
            
            out = model.generate(
                pixel_values=pixel_values, 
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=10 
            )
            
            model_answer = processor.decode(out[0], skip_special_tokens=True).strip().lower()
            
            # [수정] 모델의 답변이 'yes'인지 확인
            if model_answer == "yes":
                yes_count += 1
            else:
                # 'yes'가 아니면 (즉, 'no' 또는 다른 답변) 힌트 목록에 질문 추가
                no_questions_list.append(question)
                
        except Exception as e:
            print(f"Error during VQA processing for question '{question}': {e}")
            # 오류 발생 시에도 'no'로 간주하고 목록에 추가
            no_questions_list.append(question)

    # --- 4. 최종 성공 여부 판별 ---
    match_ratio = yes_count / total_questions
    is_success = match_ratio >= SUCCESS_THRESHOLD

    print(f"VQA Result: {yes_count}/{total_questions} 'yes' answers ({match_ratio:.2%}). Success: {is_success}")

    if is_success:
        return True, no_questions_list
    else:
        # [수정] 실패 시 'no'로 답변된 질문 리스트를 반환
        return False, no_questions_list
    

if __name__ == "__main__":
    
    # --- 1. 테스트 설정 ---
    
    # [주의!] main.py에서 './metadata/test_image/test1.HEIC'를 사용했습니다.
    # .HEIC 포맷은 'pip install pillow-heif'가 설치되어 있어야 PIL이 열 수 있습니다.
    # 
    # 만약 pillow-heif를 설치하지 않았다면,
    # 이 파일 이름을 테스트하려는 .jpg 또는 .png 파일 이름으로 변경하세요.
    test_image_name = "test3.jpg"
    
    # 'data/landmark_qa.json'에 정의된 테스트하려는 랜드마크 이름
    test_landmark = "피노키오" 

    # --- 2. 테스트 경로 설정 ---
    # (경로는 이미 파일 상단에 정의된 PROJECT_ROOT를 기준으로 잡습니다)
    test_image_path = os.path.join(PROJECT_ROOT, "metadata", "test_image", test_image_name)

    print("="*30)
    print("  BLIP Module Standalone Test  ")
    print("="*30)

    # --- 3. 실행 전 기본 확인 ---
    if not processor or not model:
        print("❌ 테스트 실패: BLIP 모델을 로드하지 못했습니다.")
    elif not landmark_qa_data:
        print(f"❌ 테스트 실패: {LANDMARK_QA_FILE} 파일을 로드하지 못했습니다.")
    elif not landmark_qa_data.get(test_landmark):
        print(f"❌ 테스트 실패: '{LANDMARK_QA_FILE}'에 '{test_landmark}' 키가 없습니다.")
    elif not os.path.exists(test_image_path):
         print(f"❌ 테스트 실패: 테스트 이미지 파일을 찾을 수 없습니다.")
         print(f"   (경로: {test_image_path})")
    else:
        # --- 4. 메인 함수 실행 ---
        print(f"▶️ Test Image: {test_image_path}")
        print(f"▶️ Test Landmark: {test_landmark}")
        print("Running check_with_blip...")
        
        try:
            is_success, hint_payload = check_with_blip(test_image_path, test_landmark)
            
            print("\n--- 💡 Test Result ---")
            print(f"Success: {is_success}")
            print(hint_payload)
            if not is_success:
                print("Hint Payload ('no' or error questions):")
                for q in hint_payload:
                    print(f"  - {q}")
            print("-----------------------")
            
        except Exception as e:
            print(f"\n--- ❌ Test Failed with Runtime Exception ---")
            print(f"Error: {e}")
            if "cannot read HEIC file" in str(e):
                print("\n[알림] .HEIC 파일을 열 수 없습니다.")
                print("터미널에서 'pip install pillow-heif'를 실행하고 다시 시도해 주세요.")
            print("---------------------------------------------")
