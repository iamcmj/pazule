# server.py
import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

# ✅ 프로젝트 루트 경로를 sys.path에 추가
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# ✅ 모듈 임포트
from answer_manager import get_today_state
from mission_manager import run_mission1, run_mission2
from metadata.validator import validate_metadata

app = Flask(__name__)
CORS(app)  # 프론트엔드와 통신을 위해 CORS 활성화

ADMIN_API_TOKEN = os.getenv("ADMIN_API_TOKEN")


def load_today_state():
    """오늘의 내부 미션 상태를 로드합니다."""
    return get_today_state()


def get_hint_by_mission_type(state, mission_type):
    """미션 타입에 맞는 공개용 힌트를 반환합니다."""
    if mission_type == "photo":
        return state["hint2"]
    return state["hint1"]


def get_answer_by_mission_type(state, mission_type):
    """미션 타입에 맞는 내부 정답을 반환합니다."""
    if mission_type == "photo":
        return state["answer2"]
    return state["answer1"]


def require_admin_access():
    """관리자 전용 요청인지 확인합니다."""
    if not ADMIN_API_TOKEN:
        return jsonify({"error": "관리자 토큰이 설정되지 않았습니다."}), 403

    request_token = request.headers.get("X-Admin-Token")
    if request_token != ADMIN_API_TOKEN:
        return jsonify({"error": "관리자 권한이 필요합니다."}), 403

    return None


@app.route("/get-today-hint", methods=["GET"])
def get_today_hint():
    """공개용 힌트 API - mission_type에 맞는 힌트만 반환"""
    mission_type = request.args.get("mission_type", "location")
    state = load_today_state()
    return jsonify({"hint": get_hint_by_mission_type(state, mission_type)})


@app.route("/api/admin/today-state", methods=["GET"])
def get_admin_today_state():
    """관리자 전용 - 오늘의 내부 상태를 확인합니다."""
    auth_error = require_admin_access()
    if auth_error:
        return auth_error

    return jsonify(load_today_state())


@app.route("/api/preview", methods=["POST"])
def api_preview():
    """HEIC 파일을 JPG로 변환하여 미리보기 제공"""
    if "image" not in request.files:
        return jsonify({"error": "이미지 파일이 필요합니다."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "이미지 파일이 선택되지 않았습니다."}), 400

    # ✅ 임시 파일로 저장
    import tempfile
    from PIL import Image
    from pillow_heif import register_heif_opener
    import io

    # HEIC 포맷 지원 등록
    register_heif_opener()

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(file.filename)[1]
    ) as tmp_file:
        file.save(tmp_file.name)
        temp_path = tmp_file.name

    try:
        # HEIC 파일을 JPG로 변환
        img = Image.open(temp_path)
        img_rgb = img.convert("RGB")

        # 메모리 버퍼에 JPG 저장
        output = io.BytesIO()
        img_rgb.save(output, format="JPEG", quality=90)
        output.seek(0)

        from flask import send_file

        return send_file(
            output,
            mimetype="image/jpeg",
            as_attachment=False,
            download_name="preview.jpg",
        )
    except Exception as e:
        print(f"미리보기 변환 오류: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        # ✅ 임시 파일 삭제
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.route("/api/mission", methods=["POST"])
def api_mission():
    """미션 실행 API - mission_type에 따라 적절한 미션 실행"""
    # ✅ 이미지 파일 확인
    if "image" not in request.files:
        return jsonify({"error": "이미지 파일이 필요합니다."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "이미지 파일이 선택되지 않았습니다."}), 400

    # ✅ mission_type 확인 (기본값: "location" -> mission1)
    mission_type = request.form.get("mission_type", "location")

    # ✅ 파일 확장자 확인 및 HEIC 지원
    file_ext = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = [".jpg", ".jpeg", ".png", ".heic", ".heif"]

    if file_ext not in allowed_extensions:
        return (
            jsonify(
                {
                    "error": f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_extensions)}"
                }
            ),
            400,
        )

    # ✅ 임시 파일로 저장 (HEIC 파일도 원본 확장자 유지)
    import tempfile

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        file.save(tmp_file.name)
        temp_path = tmp_file.name

    try:
        state = load_today_state()

        # ✅ 메타데이터 유효성 검사
        if not validate_metadata(temp_path):
            return (
                jsonify(
                    {"error": "오늘 촬영한 사진이 아니거나 출판단지 내부가 아닙니다."}
                ),
                400,
            )

        # ✅ mission_type에 따라 적절한 미션 실행
        if mission_type == "photo":
            # Mission2 (사진 촬영) - CLIP 감정 분석
            result = run_mission2(temp_path, get_answer_by_mission_type(state, "photo"))
        else:
            # Mission1 (장소 찾기) - BLIP 장소 인식
            result = run_mission1(
                temp_path,
                get_answer_by_mission_type(state, "location"),
            )

        return jsonify(result)
    except Exception as e:
        print(f"미션 실행 오류: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        # ✅ 임시 파일 삭제
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
