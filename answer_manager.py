import os, json, random
from datetime import date

# ======================================
# ✅ 루트 기준 절대 경로 계산
# ======================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ANSWER_FILE = os.path.join(DATA_DIR, "answer.json")
STATE_FILE = os.path.join(DATA_DIR, "current_answer.json")


def load_missions1():
    """missions1 리스트 로드"""
    with open(ANSWER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("missions1", [])


def load_missions2():
    """missions2 리스트 로드"""
    with open(ANSWER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("missions2", [])


def _normalize_state(state):
    """하위 호환성을 포함해 상태 파일을 표준 형태로 정규화합니다."""
    if not state:
        return None

    normalized = {
        "date": state.get("date"),
        "answer1": state.get("answer1") or state.get("answer"),
        "answer2": state.get("answer2"),
        "hint1": state.get("hint1") or state.get("hint"),
        "hint2": state.get("hint2"),
    }

    if all(
        normalized.get(key)
        for key in ("date", "answer1", "answer2", "hint1", "hint2")
    ):
        return normalized

    return None


def get_today_state(admin_choice1=None, admin_choice2=None):
    """
    오늘의 내부 미션 상태를 반환합니다.

    Returns:
        dict: {
            "date": str,
            "answer1": str,
            "answer2": str,
            "hint1": str,
            "hint2": str,
        }
    """
    answer1, answer2, hint1, hint2 = get_today_answers(admin_choice1, admin_choice2)
    return {
        "date": str(date.today()),
        "answer1": answer1,
        "answer2": answer2,
        "hint1": hint1,
        "hint2": hint2,
    }


def get_today_answer(admin_choice=None, mission_type=None):
    """
    오늘의 정답과 힌트를 가져옵니다.

    Args:
        admin_choice (str, optional): 관리자가 지정한 정답
        mission_type (str, optional): 미션 타입 ("photo" -> missions2, "location" -> missions1)
                                     None이면 missions1 사용 (기본값)

    Returns:
        tuple: (answer, hint)
    """
    today = str(date.today())

    # 이미 오늘 정답이 있으면 그대로 사용
    if not admin_choice:
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = _normalize_state(json.load(f))
                if state and state.get("date") == today:
                    # mission_type에 따라 다른 힌트 반환
                    if mission_type == "photo":
                        return state["answer2"], state["hint2"]
                    return state["answer1"], state["hint1"]
        except FileNotFoundError:
            print("⚠️ current_answer.json이 아직 없습니다. 새로 생성합니다.")

    # mission_type에 따라 다른 리스트에서 선택
    if mission_type == "photo":
        candidates = load_missions2()
    else:
        candidates = load_missions1()

    if admin_choice:
        match = next((m for m in candidates if m["answer"] == admin_choice), None)
        if match:
            answer, hint = match["answer"], match["hint"]
        else:
            raise ValueError(f"관리자 지정 '{admin_choice}'은 후보에 없습니다.")
    else:
        choice = random.choice(candidates)
        answer, hint = choice["answer"], choice["hint"]

    return answer, hint


def get_today_answers(admin_choice1=None, admin_choice2=None):
    """
    오늘의 정답과 두 가지 힌트(missions1, missions2)를 모두 가져옵니다.
    missions1과 missions2에서 각각 독립적으로 answer와 hint를 선택합니다.

    Args:
        admin_choice1 (str, optional): 관리자가 지정한 missions1 정답
        admin_choice2 (str, optional): 관리자가 지정한 missions2 정답

    Returns:
        tuple: (mission1_answer, mission2_answer, hint1, hint2)
    """
    today = str(date.today())

    # ✅ data 폴더 없으면 자동 생성
    os.makedirs(DATA_DIR, exist_ok=True)

    # 파일이 존재하고 비어있지 않은 경우에만 읽기 시도
    if not admin_choice1 and not admin_choice2:
        if os.path.exists(STATE_FILE) and os.path.getsize(STATE_FILE) > 0:
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:  # 내용이 있는 경우에만 파싱 시도
                        state = _normalize_state(json.loads(content))
                        if state and state.get("date") == today:
                            # 오늘 날짜면 기존 값 반환
                            answer1 = state["answer1"]
                            answer2 = state["answer2"]
                            hint1 = state["hint1"]
                            hint2 = state["hint2"]
                            if answer1 and answer2 and hint1 and hint2:
                                return answer1, answer2, hint1, hint2
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # JSON 파싱 오류나 잘못된 형식일 경우 새로 생성
                print(f"⚠️ 상태 파일 형식 오류: {e}. 새로 생성합니다.")
            except Exception as e:
                # 기타 오류
                print(f"⚠️ 상태 파일 읽기 오류: {e}. 새로 생성합니다.")

    # 새로운 정답 생성
    # missions1에서 answer1과 hint1 선택
    missions1_candidates = load_missions1()
    if admin_choice1:
        missions1_match = next(
            (m for m in missions1_candidates if m["answer"] == admin_choice1), None
        )
        if missions1_match:
            answer1 = missions1_match["answer"]
            hint1 = missions1_match["hint"]
        else:
            raise ValueError(
                f"관리자 지정 missions1 '{admin_choice1}'은 후보에 없습니다."
            )
    else:
        missions1_choice = random.choice(missions1_candidates)
        answer1 = missions1_choice["answer"]
        hint1 = missions1_choice["hint"]

    # missions2에서 answer2와 hint2 선택 (독립적으로)
    missions2_candidates = load_missions2()
    if admin_choice2:
        missions2_match = next(
            (m for m in missions2_candidates if m["answer"] == admin_choice2), None
        )
        if missions2_match:
            answer2 = missions2_match["answer"]
            hint2 = missions2_match["hint"]
        else:
            raise ValueError(
                f"관리자 지정 missions2 '{admin_choice2}'은 후보에 없습니다."
            )
    else:
        missions2_choice = random.choice(missions2_candidates)
        answer2 = missions2_choice["answer"]
        hint2 = missions2_choice["hint"]

    # 상태 저장
    state = {
        "date": today,
        "answer1": answer1,  # missions1 정답
        "answer2": answer2,  # missions2 정답
        "hint1": hint1,  # missions1 힌트
        "hint2": hint2,  # missions2 힌트
    }

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    return answer1, answer2, hint1, hint2


if __name__ == "__main__":
    answer, hint = get_today_answer(admin_choice="피노키오")
    print(f"오늘의 정답: {answer} / 힌트: {hint}")
