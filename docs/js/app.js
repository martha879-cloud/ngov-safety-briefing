// =========================================
// KOICA-NGO 안전관리 대시보드
// =========================================

document.addEventListener("DOMContentLoaded", () => {
    loadDashboard();
});


// =========================================
// Dashboard Data Load
// =========================================

async function loadDashboard() {

    // -----------------------------------------
    // 국가 데이터는 대시보드의 핵심이라 반드시 필요함.
    // 이것만 실패하면 전체 에러 화면을 보여준다.
    // -----------------------------------------
    let countries;

    try {

        const countriesRes = await fetch("data/countries.json");

        if (!countriesRes.ok) {
            throw new Error(`HTTP ${countriesRes.status}`);
        }

        countries = await countriesRes.json();

    } catch (err) {

        console.error("countries.json 로드 실패:", err);

        const changesBox = document.getElementById("todayChanges");

        if (changesBox) {

            changesBox.innerHTML = `
                <div class="text-danger">
                    데이터를 불러오지 못했습니다.
                </div>
            `;

        }

        return;

    }


    // -----------------------------------------
    // 나머지 데이터는 선택적(optional).
    // 하나가 실패해도 나머지는 정상적으로 표시되어야 한다.
    // -----------------------------------------
    const report = await safeFetchJson(
        "data/daily_report.json",
        { date: "", changes: [] }
    );

    const update = await safeFetchJson(
        "data/last_update.json",
        { updated: "" }
    );

    const safetyIssuesData = await safeFetchJson(
        "data/safety_issues.json",
        { issues: [] }
    );

    const newsIssuesData = await safeFetchJson(
        "data/news_issues.json",
        { issues: [] }
    );

    const disasterIssuesData = await safeFetchJson(
        "data/disaster_issues.json",
        { issues: [] }
    );

    const stateDeptIssuesData = await safeFetchJson(
        "data/state_dept_issues.json",
        { issues: [] }
    );

    const whoIssuesData = await safeFetchJson(
        "data/who_issues.json",
        { issues: [] }
    );

    const cdcIssuesData = await safeFetchJson(
        "data/cdc_issues.json",
        { issues: [] }
    );


    // 마지막 업데이트
    const lastUpdate = document.getElementById("lastUpdate");

    if (lastUpdate) {
        lastUpdate.textContent = update.updated || "정보 없음";
    }


    // ==========================================
    // 외교부 안전공지 + 뉴스 이슈 + USGS 지진 + 미국 국무부 + WHO + CDC 통합
    // ==========================================

    const safetyIssues = Array.isArray(safetyIssuesData.issues)
        ? safetyIssuesData.issues
        : [];

    const newsIssues = Array.isArray(newsIssuesData.issues)
        ? newsIssuesData.issues
        : [];

    const disasterIssues = Array.isArray(disasterIssuesData.issues)
        ? disasterIssuesData.issues
        : [];

    const stateDeptIssues = Array.isArray(stateDeptIssuesData.issues)
        ? stateDeptIssuesData.issues
        : [];

    const whoIssues = Array.isArray(whoIssuesData.issues)
        ? whoIssuesData.issues
        : [];

    const cdcIssues = Array.isArray(cdcIssuesData.issues)
        ? cdcIssuesData.issues
        : [];

    const allIssues = [...safetyIssues, ...newsIssues, ...disasterIssues, ...stateDeptIssues, ...whoIssues, ...cdcIssues];

    // 국가별로 이슈를 묶어서 국가 카드 안에 같이 보여줄 수 있게 준비.
    // 심각도 우선, 그 다음 최신순으로 정렬 후 국가당 최대 3개만 사용.
    const SEVERITY_RANK = { critical: 4, high: 3, medium: 2, low: 1 };

    allIssues.sort((a, b) => {

        const rankA = SEVERITY_RANK[a.severity] || 0;
        const rankB = SEVERITY_RANK[b.severity] || 0;

        if (rankA !== rankB) {
            return rankB - rankA;
        }

        const dateA = new Date(a.published_at || "1900-01-01");
        const dateB = new Date(b.published_at || "1900-01-01");

        return dateB - dateA;

    });

    const issuesByCountry = {};

    allIssues.forEach(issue => {

        if (!issuesByCountry[issue.country]) {
            issuesByCountry[issue.country] = [];
        }

        if (issuesByCountry[issue.country].length < 3) {
            issuesByCountry[issue.country].push(issue);
        }

    });


    // -----------------------------------------
    // 각 렌더링 단계도 서로 독립적으로 실패하도록 분리.
    // -----------------------------------------

    try {
        renderSummary(countries);
    } catch (err) {
        console.error("KPI 렌더링 실패:", err);
    }

    try {
        renderTodayChanges(report);
    } catch (err) {
        console.error("변경사항 렌더링 실패:", err);
    }

    try {
        renderCountries(countries, issuesByCountry);
    } catch (err) {
        console.error("국가 카드 렌더링 실패:", err);
    }

    try {
        setupKpiFilters();
    } catch (err) {
        console.error("KPI 필터 설정 실패:", err);
    }

    console.log("Dashboard loaded");

}


// =========================================
// KPI 클릭 시 해당 상태 국가만 필터링
// =========================================

function setupKpiFilters() {

    const kpiCards = document.querySelectorAll(".kpi-card");
    const filterNotice = document.getElementById("filterNotice");
    const filterNoticeText = document.getElementById("filterNoticeText");
    const clearFilterBtn = document.getElementById("clearFilterBtn");

    if (!kpiCards.length) {
        return;
    }

    const statusLabels = {
        green: "🟢 활동 가능",
        yellow: "🟡 모니터링",
        orange: "🟠 조치 검토",
        red: "🔴 긴급 대응",
    };

    function applyFilter(status) {

        const countryCols = document.querySelectorAll(
            "#asiaList > div, #africaList > div, #latinList > div, #middleList > div"
        );

        countryCols.forEach(col => {
            const matches = !status || col.getAttribute("data-status") === status;
            col.style.display = matches ? "" : "none";
        });

        kpiCards.forEach(card => {
            card.classList.toggle("kpi-active", card.getAttribute("data-status") === status);
        });

        if (status && filterNotice && filterNoticeText) {
            filterNoticeText.textContent = `${statusLabels[status]} 국가만 표시 중`;
            filterNotice.style.display = "block";
        } else if (filterNotice) {
            filterNotice.style.display = "none";
        }

    }

    let activeStatus = null;

    kpiCards.forEach(card => {

        card.addEventListener("click", () => {

            const status = card.getAttribute("data-status");

            activeStatus = (activeStatus === status) ? null : status;

            applyFilter(activeStatus);

            if (activeStatus) {

                const countrySection = document.getElementById("asiaList");

                if (countrySection) {
                    countrySection.scrollIntoView({ behavior: "smooth", block: "start" });
                }

            }

        });

        // 키보드 접근성 (엔터/스페이스로도 클릭 가능하게)
        card.addEventListener("keydown", (e) => {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                card.click();
            }
        });

    });

    if (clearFilterBtn) {
        clearFilterBtn.addEventListener("click", () => {
            activeStatus = null;
            applyFilter(null);
        });
    }

}


// 개별 데이터 파일을 안전하게 불러오는 헬퍼.
// 실패해도 예외를 던지지 않고 fallback 값을 반환한다.
async function safeFetchJson(url, fallback) {

    try {

        const res = await fetch(url);

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }

        return await res.json();

    } catch (err) {

        console.warn(`${url} 로드 실패, 기본값 사용:`, err);

        return fallback;

    }

}


// =========================================
// KPI Summary
// =========================================

function renderSummary(
    countries
) {

    let green = 0;
    let yellow = 0;
    let orange = 0;
    let red = 0;


    countries.forEach(
        country => {

            switch (
                country.status
            ) {

                case "green":

                    green++;

                    break;


                case "yellow":

                    yellow++;

                    break;


                case "orange":

                    orange++;

                    break;


                case "red":

                    red++;

                    break;

            }

        }
    );


    document.getElementById(
        "greenCount"
    ).textContent = green;


    document.getElementById(
        "yellowCount"
    ).textContent = yellow;


    document.getElementById(
        "orangeCount"
    ).textContent = orange;


    document.getElementById(
        "redCount"
    ).textContent = red;

}


// =========================================
// Today Changes
// =========================================

function renderTodayChanges(
    report
) {

    const box =
        document.getElementById(
            "todayChanges"
        );


    if (!box) {

        return;

    }


    const changes =
        report.changes || [];


    if (
        changes.length === 0
    ) {

        box.innerHTML = `

            <div class="text-success">

                오늘 변경사항이 없습니다.

            </div>

        `;

        return;

    }


    let html = "";


    changes.forEach(
        item => {

            html += `

                <div class="
                    border-bottom
                    pb-3
                    mb-3
                ">

                    <h6>

                        ${item.flag || "🌍"}

                        ${item.country}

                    </h6>

                    <div>

                        <strong>

                            ${item.change}

                        </strong>

                    </div>

                    <div class="
                        text-muted
                        small
                    ">

                        ${item.reason || ""}

                    </div>

                </div>

            `;

        }
    );


    box.innerHTML = html;

}


// =========================================
// Country Cards
// =========================================

function renderCountries(
    countries,
    issuesByCountry
) {

    issuesByCountry = issuesByCountry || {};

    const asiaList =
        document.getElementById(
            "asiaList"
        );

    const africaList =
        document.getElementById(
            "africaList"
        );

    const latinList =
        document.getElementById(
            "latinList"
        );

    const middleList =
        document.getElementById(
            "middleList"
        );


    if (
        !asiaList
        || !africaList
        || !latinList
        || !middleList
    ) {

        return;

    }


    asiaList.innerHTML = "";

    africaList.innerHTML = "";

    latinList.innerHTML = "";

    middleList.innerHTML = "";


    countries.forEach(
        country => {

            const card =
                createCountryCard(
                    country,
                    issuesByCountry[country.name] || []
                );


            switch (
                country.region
            ) {

                case "asia":

                    asiaList.innerHTML +=
                        card;

                    break;


                case "africa":

                    africaList.innerHTML +=
                        card;

                    break;


                case "latin":

                    latinList.innerHTML +=
                        card;

                    break;


                case "middle":

                    middleList.innerHTML +=
                        card;

                    break;


                default:

                    asiaList.innerHTML +=
                        card;

            }

        }
    );

}


// =========================================
// Country Card
// =========================================

function createCountryCard(
    country,
    issues
) {

    issues = issues || [];

    // 이미 외교부 해외안전공지(실제 링크)가 있으면, 굳이 검색 링크를 또 보여줄 필요 없음
    const hasOfficialMofaLink = issues.some(
        issue => issue.source === "외교부 해외안전공지"
    );

    const searchUrl = "https://www.google.com/search?q=" +
        encodeURIComponent(country.name + " 외교부 해외안전여행");

    // 외교부(MOFA) 상태를 요약의 첫 줄로 사용
    const summaryLines = [
        {
            label: "🏛️ 외교부",
            text: country.issue || "특이사항 없음",
        },
    ];

    // 나머지 소스(미국국무부/WHO/USGS/뉴스/외교부 안전공지) 이슈를 이어서 추가
    issues.forEach(issue => {

        const sourceLabel = getSourceLabel(issue.source);

        summaryLines.push({
            label: sourceLabel,
            text: `${issue.title}${issue.published_at ? ` (${issue.published_at})` : ""}`,
            url: issue.source_url,
        });

    });

    const summaryHtml = summaryLines.map(line => {

        const content = line.url
            ? `<a href="${line.url}" target="_blank" rel="noopener noreferrer">${line.text}</a>`
            : line.text;

        return `
            <li class="mb-2">
                <strong>${line.label}</strong>: ${content}
            </li>
        `;

    }).join("");

    return `

        <div class="
            col-lg-4
            col-md-6
        " data-status="${country.status}" data-country="${country.name}">

            <div class="
                country-card
                h-100
            ">

                <div class="
                    country-name
                ">

                    ${country.flag
                    || "🌍"}

                    ${country.name}

                </div>


                <div class="
                    mt-2
                ">

                    ${statusBadge(
                        country.status
                    )}

                </div>


                <div class="mt-3">

                    <strong>안전 요약</strong>

                    <ul class="ps-3 mt-2 mb-0 small">
                        ${summaryHtml}
                    </ul>

                </div>


                <div class="mt-2">

                    <small class="text-muted">

                        마지막 갱신: ${country.updated || ""}

                    </small>

                </div>

                ${hasOfficialMofaLink ? "" : `
                <div class="mt-2">
                    <a href="${searchUrl}"
                       target="_blank"
                       rel="noopener noreferrer"
                       class="small text-primary">
                        외교부 안전정보 보기 →
                    </a>
                </div>
                `}

            </div>

        </div>

    `;

}


// =========================================
// Source Label (요약 불릿용 짧은 라벨)
// =========================================

function getSourceLabel(source) {

    switch (source) {

        case "외교부 해외안전공지":
            return "🏛️ 외교부 안전공지";

        case "USGS":
            return "🌍 지진(USGS)";

        case "US State Dept":
            return "🇺🇸 미국 국무부";

        case "WHO":
            return "🏥 WHO";

        case "CDC":
            return "🇺🇸 CDC";

        default:
            return "📰 뉴스";

    }

}


// Country Status Badge
// =========================================

function statusBadge(
    status
) {

    switch (
        status
    ) {

        case "green":

            return `

                <span class="
                    badge
                    bg-success
                ">

                    🟢 활동 가능

                </span>

            `;


        case "yellow":

            return `

                <span class="
                    badge
                    bg-warning
                    text-dark
                ">

                    🟡 모니터링

                </span>

            `;


        case "orange":

            return `

                <span class="
                    badge
                    bg-orange
                ">

                    🟠 조치 검토

                </span>

            `;


        case "red":

            return `

                <span class="
                    badge
                    bg-danger
                ">

                    🔴 긴급 대응

                </span>

            `;


        default:

            return `

                <span class="
                    badge
                    bg-secondary
                ">

                    정보 없음

                </span>

            `;

    }

}


console.log(
    "KOICA-NGO Dashboard loaded"
);
