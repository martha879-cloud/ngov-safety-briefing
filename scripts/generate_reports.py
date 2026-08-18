"""
docs/data/briefing.json, daily_report.json, history.json 을
실제 countries.json 데이터를 기반으로 매일 자동 생성하는 스크립트.

update_data.py가 docs/data/countries.json 을 먼저 갱신한 뒤에 실행되어야 합니다.

전날 상태와 비교하기 위해 data/processed/previous_countries.json 에 스냅샷을 저장하고,
history.json의 최근 N일치 흐름을 위해 data/processed/history_log.json 에 누적 로그를 남깁니다.

+ 장기 아카이빙(위기상황 흐름 분석용) 3종:
  - docs/data/archive/event_log.json         : 지금까지 감지된 모든 변경사항(외교부/국무부/CDC) 누적, 사유 포함
  - docs/data/archive/status_timeseries.json : 국가별 상태(색상) 일별 시계열 (차트용, 압축된 형태)
  - docs/data/archive/status_history_full.json : 전체 기간 국가수 색상별 분포 (history.json의 무제한 버전)
  - data/archive/countries/YYYY-MM-DD.json   : 그날의 countries.json 원본 그대로 보관 (감사/상세조회용, 사이트에서는 안 씀)
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COUNTRIES_PATH = os.path.join(BASE_DIR, "docs", "data", "countries.json")
PREV_PATH = os.path.join(BASE_DIR, "data", "processed", "previous_countries.json")
HISTORY_LOG_PATH = os.path.join(BASE_DIR, "data", "processed", "history_log.json")

STATE_DEPT_PATH = os.path.join(BASE_DIR, "docs", "data", "state_dept_issues.json")
CDC_PATH = os.path.join(BASE_DIR, "docs", "data", "cdc_issues.json")
PREV_SOURCE_LEVELS_PATH = os.path.join(
    BASE_DIR, "data", "processed", "previous_source_levels.json"
)

BRIEFING_PATH = os.path.join(BASE_DIR, "docs", "data", "briefing.json")
DAILY_REPORT_PATH = os.path.join(BASE_DIR, "docs", "data", "daily_report.json")
HISTORY_PATH = os.path.join(BASE_DIR, "docs", "data", "history.json")

ARCHIVE_DIR = os.path.join(BASE_DIR, "docs", "data", "archive")
EVENT_LOG_PATH = os.path.join(ARCHIVE_DIR, "event_log.json")
STATUS_TIMESERIES_PATH = os.path.join(ARCHIVE_DIR, "status_timeseries.json")
STATUS_HISTORY_FULL_PATH = os.path.join(ARCHIVE_DIR, "status_history_full.json")

DAILY_SNAPSHOT_DIR = os.path.join(BASE_DIR, "data", "archive", "countries")

STATUS_EMOJI = {"green": "🟢", "yellow": "🟡", "orange": "🟠", "red": "🔴"}

# 국가 카드 색상 상태를 숫자로 (아카이브 페이지에서 타임라인 차트를 그릴 때 사용)
STATUS_SEVERITY_NUM = {"green": 0, "yellow": 1, "orange": 2, "red": 3}

HISTORY_WINDOW = 7  # docs/data/history.json(짧은 요약)에 보여줄 최근 일수. 전체 로그 자체는 안 자름.


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
    """어제 스냅샷과 비교해서 실제로 상태가 바뀐 국가만 모음 (외교부 여행경보 단계 기준)"""
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
                "source": "🏛️ 외교부",
                "change": f"{STATUS_EMOJI.get(prev.get('status'), '⚪')} → {STATUS_EMOJI[c['status']]}",
                # scrape_travel_alert_reasons.py로 실제 조정 사유를 찾았으면 그걸 우선 쓰고,
                # 없으면 예전처럼 단계/발령일 텍스트(c["issue"])로 대체한다.
                "reason": c.get("adjustment_reason") or c["issue"],
            })

    return {"date": today_str, "changes": changes}


SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def pick_representative_issue(issues_for_country):
    """한 국가에 여러 항목이 있을 때, 가장 심각하고 가장 최근인 항목 하나를 대표로 고른다.
    (국가 카드에서 이 소스의 대표 항목을 하나만 보여주는 것과 동일한 기준)"""

    if not issues_for_country:
        return None

    def sort_key(issue):
        return (
            SEVERITY_RANK.get(issue.get("severity"), 0),
            issue.get("published_at") or "",
        )

    return sorted(issues_for_country, key=sort_key, reverse=True)[0]


def build_source_changes(source_label, issues, previous_snapshot, snapshot_key):
    """미국 국무부/CDC처럼 국가별 대표 항목이 있는 소스에 대해,
    어제 스냅샷과 비교해서 실제로 등급/내용이 바뀐 국가만 변경사항으로 뽑아낸다.

    반환값: (changes 리스트, 갱신된 snapshot 딕셔너리)
    """

    by_country = {}
    for issue in issues:
        by_country.setdefault(issue["country"], []).append(issue)

    changes = []

    # 얕은 복사가 아니라 국가별 내부 딕셔너리까지 새로 만들어서,
    # 이 함수 밖의 원본 previous_snapshot을 건드리지 않게 한다.
    new_snapshot = {name: dict(entry) for name, entry in previous_snapshot.items()}

    for country_name, country_issues in by_country.items():

        rep = pick_representative_issue(country_issues)

        if not rep:
            continue

        current_fingerprint = {
            "severity": rep.get("severity"),
            "title": rep.get("title"),
        }

        prev_country_entry = previous_snapshot.get(country_name)
        prev_fingerprint = (
            prev_country_entry.get(snapshot_key) if prev_country_entry else None
        )

        # 이 국가+소스 조합을 처음 보는 경우는 "변경"이 아니라 기준값 저장으로만 취급한다
        # (그래야 이 기능을 처음 도입한 날 20개국이 전부 "변경됨"으로 쏟아지는 걸 방지)
        if prev_fingerprint is not None and prev_fingerprint != current_fingerprint:
            changes.append({
                "country": country_name,
                "flag": "",  # app.js에서 countries 목록과 매칭해서 채워줌
                "source": source_label,
                "change": f"{prev_fingerprint.get('title', '이전 정보 없음')} → {rep.get('title')}",
                "reason": rep.get("summary") or rep.get("title"),
            })

        new_snapshot.setdefault(country_name, {})[snapshot_key] = current_fingerprint

    return changes, new_snapshot


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


def build_history(countries, today_label, today_str, history_log):
    """오늘자 상태 분포를 누적 로그에 반영한다.
    이전에는 여기서 history_log 자체를 HISTORY_WINDOW로 잘라서 저장했는데,
    그러면 저장소에 남는 로그 자체가 최근 7일치 뿐이라 장기 추이를 볼 수 없었다.
    그래서 이제 history_log는 무제한으로 누적 보관하고, 짧은 요약(history.json)만
    최근 HISTORY_WINDOW일치로 잘라서 만든다."""

    counts = {"green": 0, "yellow": 0, "orange": 0, "red": 0}
    for c in countries:
        counts[c["status"]] = counts.get(c["status"], 0) + 1

    # 같은 날 중복 실행 시 오늘 항목을 갱신 (중복 추가 방지)
    history_log = [e for e in history_log if e["label"] != today_label]
    history_log.append({"label": today_label, "date": today_str, **counts})

    recent = history_log[-HISTORY_WINDOW:]

    history = {
        "labels": [e["label"] for e in recent],
        "green": [e["green"] for e in recent],
        "yellow": [e["yellow"] for e in recent],
        "orange": [e["orange"] for e in recent],
        "red": [e["red"] for e in recent],
    }

    return history, history_log


def append_event_log(changes, today_str, event_log):
    """오늘 감지된 변경사항(외교부/국무부/국무부 안전공지/CDC, 사유 포함)을
    영구 이벤트 로그에 누적한다. 위기상황이 시간에 따라 어떻게 흘러왔는지
    나중에 국가별로 돌아볼 수 있게 하는 게 목적이라, 별도로 자르지 않고 계속 쌓는다.
    같은 날 여러 번 실행돼도 중복 추가되지 않게, 오늘 날짜 항목은 지우고 다시 넣는다."""

    event_log = [e for e in event_log if e.get("date") != today_str]

    for change in changes:
        event_log.append({"date": today_str, **change})

    return event_log


def append_status_timeseries(countries, today_str, timeseries):
    """국가별 상태(색상)를 일별 시계열로 누적한다.
    아카이브 페이지에서 국가를 골랐을 때 상태 추이 차트를 그리는 데 쓰는,
    country_history_full보다 훨씬 가벼운 압축 데이터."""

    for c in countries:
        series = timeseries.setdefault(c["name"], [])
        series[:] = [e for e in series if e.get("date") != today_str]

        series.append({
            "date": today_str,
            "status": c["status"],
            "severity_num": STATUS_SEVERITY_NUM.get(c["status"], 0),
        })

    return timeseries


def save_daily_snapshot(countries, today_str):
    """그날의 countries.json 원본을 그대로 하루 하나씩 영구 보관한다.
    (감사/상세 조회용 원본 아카이브. 용량이 크지 않으니 사이트 표시용과 별도로 계속 쌓는다.
    docs/ 밖에 두어서 사이트 배포 용량에는 영향을 주지 않는다.)"""

    snapshot_dir = Path(DAILY_SNAPSHOT_DIR)
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    path = snapshot_dir / f"{today_str}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(countries, f, ensure_ascii=False, indent=2)


def main():
    now = datetime.now(KST)
    today_str = now.strftime("%Y-%m-%d")
    today_label = f"{now.month}/{now.day}"

    countries = load_json(COUNTRIES_PATH, [])
    previous = load_json(PREV_PATH, [])
    previous_by_id = {c["id"]: c for c in previous}
    history_log = load_json(HISTORY_LOG_PATH, [])

    state_dept_issues = load_json(STATE_DEPT_PATH, {"issues": []}).get("issues", [])
    cdc_issues = load_json(CDC_PATH, {"issues": []}).get("issues", [])
    previous_source_levels = load_json(PREV_SOURCE_LEVELS_PATH, {})

    daily_report = build_daily_report(countries, previous_by_id, today_str)

    # "US State Dept" 소스에는 "여행경보 단계" 항목과 "US State Dept Alert"(개별 안전공지)가
    # 둘 다 섞여서 저장되어 있어서(update_state_dept_issues.py 참고), 소스별로 나눠서 비교한다.
    level_change_issues = [i for i in state_dept_issues if i.get("source") == "US State Dept"]
    alert_issues = [i for i in state_dept_issues if i.get("source") == "US State Dept Alert"]

    state_dept_changes, previous_source_levels = build_source_changes(
        "🇺🇸 미국 국무부", level_change_issues, previous_source_levels, "state_dept"
    )
    state_dept_alert_changes, previous_source_levels = build_source_changes(
        "🇺🇸 국무부 안전공지", alert_issues, previous_source_levels, "state_dept_alert"
    )
    cdc_changes, previous_source_levels = build_source_changes(
        "🇺🇸 CDC", cdc_issues, previous_source_levels, "cdc"
    )

    daily_report["changes"].extend(state_dept_changes)
    daily_report["changes"].extend(state_dept_alert_changes)
    daily_report["changes"].extend(cdc_changes)

    # 국무부/CDC 변경사항은 flag를 안 갖고 있으니 countries.json 기준으로 채워준다
    flag_by_country = {c["name"]: c["flag"] for c in countries}
    for change in daily_report["changes"]:
        if not change.get("flag"):
            change["flag"] = flag_by_country.get(change["country"], "🌍")

    briefing = build_briefing(countries, daily_report["changes"])
    history, history_log = build_history(countries, today_label, today_str, history_log)

    # --- 장기 아카이빙 ---
    event_log = load_json(EVENT_LOG_PATH, [])
    status_timeseries = load_json(STATUS_TIMESERIES_PATH, {})

    event_log = append_event_log(daily_report["changes"], today_str, event_log)
    status_timeseries = append_status_timeseries(countries, today_str, status_timeseries)
    save_daily_snapshot(countries, today_str)

    save_json(DAILY_REPORT_PATH, daily_report)
    save_json(BRIEFING_PATH, briefing)
    save_json(HISTORY_PATH, history)
    save_json(HISTORY_LOG_PATH, history_log)
    save_json(PREV_PATH, countries)
    save_json(PREV_SOURCE_LEVELS_PATH, previous_source_levels)

    save_json(EVENT_LOG_PATH, event_log)
    save_json(STATUS_TIMESERIES_PATH, status_timeseries)
    save_json(STATUS_HISTORY_FULL_PATH, history_log)

    print("오늘 변경사항:", len(daily_report["changes"]), "건")
    mofa_count = (
        len(daily_report["changes"])
        - len(state_dept_changes)
        - len(state_dept_alert_changes)
        - len(cdc_changes)
    )
    print(
        "  (외교부:", mofa_count,
        "/ 국무부 단계:", len(state_dept_changes),
        "/ 국무부 안전공지:", len(state_dept_alert_changes),
        "/ CDC:", len(cdc_changes), ")",
    )
    print("히스토리 누적 일수(전체):", len(history_log))
    print("이벤트 로그 누적 건수(전체):", len(event_log))


if __name__ == "__main__":
    main()
