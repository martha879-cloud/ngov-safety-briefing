"""
docs/data/briefing.json, daily_report.json, history.json 을
실제 countries.json 데이터를 기반으로 매일 자동 생성하는 스크립트.

update_data.py가 docs/data/countries.json 을 먼저 갱신한 뒤에 실행되어야 합니다.

전날 상태와 비교하기 위해 data/processed/previous_countries.json 에 스냅샷을 저장하고,
history.json의 지난 7일치 흐름을 위해 data/processed/history_log.json 에 누적 로그를 남깁니다.
"""

import json
import os
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COUNTRIES_PATH = os.path.join(BASE_DIR, "docs", "data", "countries.json")
PREV_PATH = os.path.join(BASE_DIR, "data", "processed", "previous_countries.json")
HISTORY_LOG_PATH = os.path.join(BASE_DIR, "data", "processed", "history_log.json")

BRIEFING_PATH = os.path.join(BASE_DIR, "docs", "data", "briefing.json")
DAILY_REPORT_PATH = os.path.join(BASE_DIR, "docs", "data", "daily_report.json")
HISTORY_PATH = os.path.join(BASE_DIR, "docs", "data", "history.json")

STATUS_EMOJI = {"green": "🟢", "yellow": "🟡", "orange": "🟠", "red": "🔴"}

HISTORY_WINDOW = 7  # 그래프에 보여줄 최근 일수


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_daily_report(countries, previous_by_id, today_str):
    """어제 스냅샷과 비교해서 실제로 상태가 바뀐 국가만 모음"""
    changes = []

    for c in countries:
        prev = previous_by_id.get(c["id"])

        # 첫 실행이라 비교할 어제 데이터가 없으면 "변경"으로 취급하지 않음
        if prev is None:
            continue

        if prev.get("status") != c["status"]:
            changes.append({
                "country": c["name"],
                "flag": c["flag"],
                "change": f"{STATUS_EMOJI.get(prev.get('status'), '⚪')} → {STATUS_EMOJI[c['status']]}",
                "reason": c["issue"],
            })

    return {"date": today_str, "changes": changes}


def josa_eun_neun(word):
    """마지막 글자 받침 유무에 따라 '은' 또는 '는' 조사를 고름"""
    if not word:
        return "는"
    last = word[-1]
    code = ord(last) - 0xAC00
    if 0 <= code <= 11171 and code % 28 != 0:
        return "은"
    return "는"


def build_briefing(countries, changes):
    """현재 countries 데이터로 브리핑 문장을 실제로 조립"""
    summary = []

    if changes:
        names = ", ".join(c["country"] for c in changes)
        summary.append(f"금일 위험도 변경 국가는 {names} 총 {len(changes)}개국입니다.")
    else:
        summary.append("금일 위험도 변경 국가는 없습니다.")

    elevated = [c for c in countries if c["status"] in ("orange", "red")]
    for c in elevated:
        summary.append(f"{c['flag']} {c['name']}: {c['issue']}")

    monitoring = [c for c in countries if c["status"] == "yellow"]
    if monitoring:
        names = ", ".join(c["name"] for c in monitoring)
        josa = josa_eun_neun(monitoring[-1]["name"])
        summary.append(f"{names}{josa} 모니터링 중입니다.")

    if not elevated and not monitoring:
        summary.append("모든 파견국이 특이사항 없이 활동 가능합니다.")
    elif not elevated:
        summary.append("나머지 파견국은 특이사항 없이 활동 가능합니다.")

    return {"summary": summary}


def build_history(countries, today_label, history_log):
    """오늘자 상태 분포를 누적 로그에 반영하고, 최근 7일치만 프론트에 넘김"""
    counts = {"green": 0, "yellow": 0, "orange": 0, "red": 0}
    for c in countries:
        counts[c["status"]] = counts.get(c["status"], 0) + 1

    # 같은 날 중복 실행 시 오늘 항목을 갱신 (중복 추가 방지)
    history_log = [e for e in history_log if e["label"] != today_label]
    history_log.append({"label": today_label, **counts})
    history_log = history_log[-HISTORY_WINDOW:]

    history = {
        "labels": [e["label"] for e in history_log],
        "green": [e["green"] for e in history_log],
        "yellow": [e["yellow"] for e in history_log],
        "orange": [e["orange"] for e in history_log],
        "red": [e["red"] for e in history_log],
    }

    return history, history_log


def main():
    now = datetime.now(KST)
    today_str = now.strftime("%Y-%m-%d")
    today_label = f"{now.month}/{now.day}"

    countries = load_json(COUNTRIES_PATH, [])
    previous = load_json(PREV_PATH, [])
    previous_by_id = {c["id"]: c for c in previous}
    history_log = load_json(HISTORY_LOG_PATH, [])

    daily_report = build_daily_report(countries, previous_by_id, today_str)
    briefing = build_briefing(countries, daily_report["changes"])
    history, history_log = build_history(countries, today_label, history_log)

    save_json(DAILY_REPORT_PATH, daily_report)
    save_json(BRIEFING_PATH, briefing)
    save_json(HISTORY_PATH, history)
    save_json(HISTORY_LOG_PATH, history_log)
    save_json(PREV_PATH, countries)

    print("오늘 변경사항:", len(daily_report["changes"]), "건")
    print("히스토리 누적 일수:", len(history_log))


if __name__ == "__main__":
    main()
