# BLIP 기반 랜드마크 이미지 인식 및 검증 시스템

파주 지역 랜드마크를 BLIP 모델로 인식하고 검증하는 AI 시스템입니다.

## 주요 기능

### 3가지 검증 방식 제공

1. **이미지-텍스트 유사도 검증** (`image_text`)

   - BlipForImageTextRetrieval 모델 사용
   - 이미지와 Ground Truth 캡션 간 직접 비교
2. **텍스트-텍스트 유사도 검증** (`text_text`)

   - 캡션 생성 + SBERT 임베딩
   - 생성된 캡션과 Ground Truth 캡션 비교
3. **VQA 유사도 검증** (`vqa`)

   - 질문-답변 기반
   - YES 답변 비율로 판정

## 지원 환경

✅ **Google Colab**
✅ **로컬 환경** (Windows, Linux, macOS)

## 설치

```bash
pip install torch transformers pillow sentence-transformers scikit-learn tqdm
```

### GPU 지원 (권장)

```bash
# CUDA 사용 가능한 경우
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 빠른 시작

### 1. Google Colab

```python
from blip import run_mission_verification, print_system_info

# 시스템 정보 확인
print_system_info()

# 검증 실행 (파일 업로드 UI 표시됨)
run_mission_verification('vqa', '피노키오')
```

### 2. 로컬 환경

```python
from blip import run_mission_verification, print_system_info

# 시스템 정보 확인
print_system_info()

# 검증 실행 (이미지 경로 지정)
run_mission_verification(
    verification_method='vqa',
    landmark_name='피노키오',
    image_path='test_pinocchio.jpg'
)
```

## 지원 랜드마크

- **피노키오** (피노키오 조각상)
- **네모탑** (네모탑 조각)
- **지혜의숲 조각상** (지혜의 숲 내부 조각상)

## 상세 사용법

### 이미지-텍스트 유사도 검증

```python
run_mission_verification(
    verification_method='image_text',
    landmark_name='지혜의숲 조각상',
    image_path='test.jpg'  # 로컬 환경
)
```

**특징:**

- Ground Truth 캡션 자동 생성
- 이미지와 텍스트 직접 매칭
- 점수: 0~100점

### 텍스트-텍스트 유사도 검증

```python
run_mission_verification(
    verification_method='text_text',
    landmark_name='네모탑',
    image_path='test.jpg'
)
```

**특징:**

- 사용자 이미지 → 캡션 생성
- 생성된 캡션과 Ground Truth 비교
- SBERT 임베딩 사용

### VQA 검증 (추천)

```python
run_mission_verification(
    verification_method='vqa',
    landmark_name='피노키오',
    image_path='test.jpg'
)
```

**특징:**

- Ground Truth 캡션 불필요
- 질문-답변 기반 검증
- YES 비율로 판정

## 커스터마이징

### 데이터 디렉토리 변경

```python
run_mission_verification(
    verification_method='vqa',
    landmark_name='피노키오',
    image_path='test.jpg',
    data_dir='./my_custom_data'  # 커스텀 경로
)
```

### 미션 데이터 커스터마이징

```python
custom_mission = {
    "id": 99,
    "daily_keyword": "문화",
    "landmark_name": "피노키오",
    "hint_text_1": "이야기 속 주인공을 찾아보세요",
    "hint_text_2": "긴 코가 특징입니다",
    "hint_text_3": "ㅍㄴㅋㅇ",
    "score_threshold_low": 0.4,
    "score_threshold_high": 0.75,
    "required_yes_ratio": 0.7
}

run_mission_verification(
    verification_method='vqa',
    landmark_name='피노키오',
    mission_data=custom_mission,
    image_path='test.jpg'
)
```

## Ground Truth 캡션 생성

```python
from blip import generate_ground_truth_captions_from_folder

# 폴더의 모든 이미지에서 캡션 생성
captions = generate_ground_truth_captions_from_folder(
    landmark_name='피노키오',
    data_dir='./data'
)

print(f"생성된 캡션: {captions}")
```

## 단일 이미지 캡션 생성

```python
from PIL import Image
from blip import generate_single_image_caption

# 이미지 로드
image = Image.open('test.jpg')

# 캡션 생성
captions = generate_single_image_caption(image)
# JSON 형식으로 출력됨 (missions.json에 복사 가능)
```

## 유틸리티 함수

```python
from blip import get_available_landmarks, print_system_info

# 사용 가능한 랜드마크 목록
landmarks = get_available_landmarks()
print(landmarks)  # ['피노키오', '네모탑', '지혜의숲 조각상']

# 시스템 정보 출력
print_system_info()
```

## 디렉토리 구조

```
github/blip/
├── blip.py              # 메인 코드
├── README.md            # 이 파일
├── CHANGES.md           # 수정 내역
├── BLIP.ipynb          # Jupyter 노트북
├── BLIP_CODE.ipynb     # BLIP 코드 정리
└── data/               # 데이터 폴더 (생성 필요)
    ├── 피노키오/
    ├── 네모탑/
    └── 지혜의숲 조각상/
```

## 모델 정보

| 모델                                      | 용도               | 크기 |
| ----------------------------------------- | ------------------ | ---- |
| `Salesforce/blip-image-captioning-base` | 캡션 생성          | Base |
| `Salesforce/blip-itm-base-coco`         | 이미지-텍스트 매칭 | Base |
| `ybelkada/blip-vqa-base`                | VQA                | Base |
| `all-MiniLM-L6-v2`                      | 텍스트 임베딩      | Mini |

## 성능

- **GPU 권장**: CUDA 지원 시 10배 이상 빠름
- **메모리**: 약 2-4GB (모델당)
- **Lazy Loading**: 필요한 모델만 로드

## 문제 해결

### "No module named 'google.colab'" 오류

정상입니다! 로컬 환경에서는 자동으로 우회됩니다.

### GPU를 사용하지 않음

```python
import torch
print(torch.cuda.is_available())  # True여야 함
```

### 이미지를 찾을 수 없음

```python
# 데이터 디렉토리 확인
from blip import DATA_DIR
print(f"현재 데이터 경로: {DATA_DIR}")

# 커스텀 경로 사용
run_mission_verification(..., data_dir='./your/custom/path')
```

### 모델 다운로드 느림

처음 실행 시 모델을 다운로드합니다 (약 1-2GB).
이후에는 캐시된 모델을 사용합니다.

## API Reference

### run_mission_verification()

```python
run_mission_verification(
    verification_method: str = "image_text",  # "image_text" | "text_text" | "vqa"
    landmark_name: str = None,                # 랜드마크 이름
    mission_data: dict = None,                # 미션 설정
    image_path: str = None,                   # 이미지 경로 (로컬)
    data_dir: str = None                      # 데이터 디렉토리
) -> None
```

### generate_ground_truth_captions_from_folder()

```python
generate_ground_truth_captions_from_folder(
    landmark_name: str,                       # 랜드마크 이름
    data_dir: str = None,                     # 데이터 디렉토리
    prompt_text: str = None                   # 선택적 프롬프트
) -> List[str]                                # 캡션 리스트
```

### verify_image_text_similarity()

```python
verify_image_text_similarity(
    user_image: PIL.Image,                    # 사용자 이미지
    gt_captions: List[str],                   # Ground Truth 캡션
    threshold_low: float = 0.5,               # 낮은 임계값
    threshold_high: float = 0.8               # 높은 임계값
) -> Tuple[float, str]                        # (점수, 피드백)
```

### verify_vqa_similarity()

```python
verify_vqa_similarity(
    user_image: PIL.Image,                    # 사용자 이미지
    landmark_name: str,                       # 랜드마크 이름
    required_yes_ratio: float = 0.75          # YES 비율 임계값
) -> Tuple[float, str]                        # (YES 비율, 피드백)
```
