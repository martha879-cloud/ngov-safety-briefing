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

    try {

        const [
            countriesRes,
            briefingRes,
            reportRes,
            updateRes,
            safetyIssuesRes,
            newsIssuesRes
        ] = await Promise.all([

            fetch("data/countries.json"),
            fetch("data/briefing.json"),
            fetch("data/daily_report.json"),
            fetch("data/last_update.json"),
            fetch("data/safety_issues.json"),
            fetch("data/news_issues.json")

        ]);


        // HTTP 오류 확인
        if (!countriesRes.ok) {
            throw new Error(
                "countries.json을 불러오지 못했습니다."
            );
        }

        if (!briefingRes.ok) {
            throw new Error(
                "briefing.json을 불러오지 못했습니다."
            );
        }

        if (!reportRes.ok) {
            throw new Error(
                "daily_report.json을 불러오지 못했습니다."
            );
        }

        if (!updateRes.ok) {
            throw new Error(
                "last_update.json을 불러오지 못했습니다."
            );
        }

        if (!newsRes.ok) {
            throw new Error(
                "news_issues.json을 불러오지 못했습니다."
            );
        }


        // JSON 데이터 변환
        const countries =
            await countriesRes.json();

        const briefing =
            await briefingRes.json();

        const report =
            await reportRes.json();

        const update =
            await updateRes.json();
        
        const safetyIssuesData = 
            await safetyIssuesRes.json();

        const newsData =
            await newsRes.json();


        // 마지막 업데이트
        const lastUpdate =
            document.getElementById(
                "lastUpdate"
            );

        if (lastUpdate) {

            lastUpdate.textContent =
                update.updated
                || "정보 없음";

         const allIssues = [
             ...(safetyIssuesData.issues || []),
             ...(newsIssuesData.issues || [])
];

renderRecentIssues(allIssues);
        }


        // KPI
        renderSummary(
            countries
        );


        // 오늘 브리핑
        renderBriefing(
            briefing
        );


        // 오늘 변경사항
        renderTodayChanges(
            report
        );


        // 최근 주요 안전 이슈
        renderNewsIssues(
            newsData
        );


        // 국가 카드
        renderCountries(
            countries
        );


        // 세계 지도
        const map =
            initMap();

        renderMapCountries(
            map,
            countries
        );


        console.log(
            "Dashboard loaded successfully"
        );

        console.log(
            "News issues:",
            newsData.issues
        );

    } catch (err) {

        console.error(
            "Dashboard loading error:",
            err
        );

        const briefingBox =
            document.getElementById(
                "briefing"
            );

        if (briefingBox) {

            briefingBox.innerHTML = `

                <div class="text-danger">

                    데이터를 불러오지 못했습니다.

                </div>

            `;

        }


        const issuesBox =
            document.getElementById(
                "recentIssues"
            );

        if (issuesBox) {

            issuesBox.innerHTML = `

                <div class="alert alert-danger mb-0">

                    안전 이슈 데이터를
                    불러오지 못했습니다.

                    <br>

                    <small>

                        ${err.message}

                    </small>

                </div>

            `;

        }

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
// Today Briefing
// =========================================

function renderBriefing(
    data
) {

    const box =
        document.getElementById(
            "briefing"
        );


    if (!box) {

        return;

    }


    const summary =
        data.summary || [];


    if (
        summary.length === 0
    ) {

        box.innerHTML = `

            <div class="text-muted">

                오늘의 안전 브리핑이
                없습니다.

            </div>

        `;

        return;

    }


    let html = "";


    summary.forEach(
        text => {

            html += `

                <div class="mb-2">

                    ✅ ${text}

                </div>

            `;

        }
    );


    box.innerHTML = html;

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
// Recent News Safety Issues
// =========================================

function renderNewsIssues(
    data
) {

    const box =
        document.getElementById(
            "recentIssues"
        );


    if (!box) {

        return;

    }


    const issues =
        Array.isArray(
            data.issues
        )
        ? data.issues
        : [];


    if (
        issues.length === 0
    ) {

        box.innerHTML = `

            <div class="alert alert-success mb-0">

                현재 등록된 주요 안전 이슈가
                없습니다.

            </div>

        `;

        return;

    }


    // 최신 날짜 순 정렬
    const sortedIssues =
        [...issues].sort(
            (a, b) => {

                const dateA =
                    new Date(
                        a.published_at
                        || "1900-01-01"
                    );

                const dateB =
                    new Date(
                        b.published_at
                        || "1900-01-01"
                    );

                return (
                    dateB - dateA
                );

            }
        );


    // 최대 10개 표시
    const recentIssues =
        sortedIssues.slice(
            0,
            10
        );


    let html = `

        <div class="row g-3">

    `;


    recentIssues.forEach(
        issue => {

            const severity =
                issue.severity
                || "low";


            html += `

                <div class="
                    col-lg-6
                    col-xl-4
                ">

                    <div class="
                        card
                        h-100
                        shadow-sm
                        border-${getSeverityBorder(
                            severity
                        )}
                    ">

                        <div class="
                            card-body
                        ">

                            <div class="
                                d-flex
                                justify-content-between
                                align-items-start
                                gap-2
                                mb-2
                            ">

                                <strong>

                                    ${getSeverityIcon(
                                        severity
                                    )}

                                    ${issue.country
                                    || "국가 정보 없음"}

                                </strong>

                                <span class="
                                    badge
                                    ${getSeverityBadge(
                                        severity
                                    )}
                                ">

                                    ${getSeverityText(
                                        severity
                                    )}

                                </span>

                            </div>


                            <h6 class="
                                fw-bold
                            ">

                                ${issue.title
                                || "안전 이슈"}

                            </h6>


                            <p class="
                                text-muted
                                small
                            ">

                                ${issue.summary
                                || "상세 내용이 없습니다."}

                            </p>


                            <div class="
                                small
                                mb-2
                            ">

                                <strong>

                                    봉사단 영향

                                </strong>

                                <br>

                                ${issue.volunteer_impact
                                || "현지 상황 확인 필요"}

                            </div>


                            <div class="
                                small
                                mb-3
                            ">

                                <strong>

                                    권장 조치

                                </strong>

                                <br>

                                ${issue.recommended_action
                                || "최신 상황을 확인하세요."}

                            </div>


                            <div class="
                                d-flex
                                justify-content-between
                                align-items-end
                                gap-2
                            ">

                                <small class="
                                    text-muted
                                ">

                                    ${issue.source
                                    || "뉴스"}

                                    <br>

                                    ${issue.published_at
                                    || ""}

                                </small>


                                ${createSourceButton(
                                    issue.source_url
                                )}

                            </div>

                        </div>

                    </div>

                </div>

            `;

        }
    );


    html += `

        </div>

    `;


    box.innerHTML = html;

}


// =========================================
// Source Button
// =========================================

function createSourceButton(
    sourceUrl
) {

    if (
        !sourceUrl
    ) {

        return "";

    }


    return `

        <a
            href="${sourceUrl}"
            target="_blank"
            rel="noopener noreferrer"
            class="
                btn
                btn-sm
                btn-outline-primary
            "
        >

            원문 보기

        </a>

    `;

}


// =========================================
// Severity Helpers
// =========================================

function getSeverityBorder(
    severity
) {

    switch (
        severity
    ) {

        case "critical":

            return "danger";


        case "high":

            return "warning";


        case "medium":

            return "primary";


        default:

            return "success";

    }

}


function getSeverityBadge(
    severity
) {

    switch (
        severity
    ) {

        case "critical":

            return "bg-danger";


        case "high":

            return (
                "bg-warning " +
                "text-dark"
            );


        case "medium":

            return "bg-primary";


        default:

            return "bg-success";

    }

}


function getSeverityIcon(
    severity
) {

    switch (
        severity
    ) {

        case "critical":

            return "🔴";


        case "high":

            return "🟠";


        case "medium":

            return "🟡";


        default:

            return "🟢";

    }

}


function getSeverityText(
    severity
) {

    switch (
        severity
    ) {

        case "critical":

            return "긴급";


        case "high":

            return "높음";


        case "medium":

            return "주의";


        default:

            return "정보";

    }

}


// =========================================
// Country Cards
// =========================================

function renderCountries(
    countries
) {

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
                    country
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
    country
) {

    return `

        <div class="
            col-lg-4
            col-md-6
        ">

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


                <div class="
                    mt-3
                ">

                    <strong>

                        상황

                    </strong>

                    <br>

                    ${country.issue
                    || "특이사항 없음"}

                </div>


                <div class="
                    mt-3
                ">

                    <small class="
                        text-muted
                    ">

                        ${country.source
                        || ""}

                    </small>

                </div>


                <div>

                    <small class="
                        text-muted
                    ">

                        ${country.updated
                        || ""}

                    </small>

                </div>

            </div>

        </div>

    `;

}


// =========================================
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


// =========================================
// World Map
// =========================================

function initMap() {

    const map = L.map(
        "map",
        {

            worldCopyJump:
                false,

            maxBounds:
                [
                    [-90, -180],
                    [90, 180]
                ],

            maxBoundsViscosity:
                1.0

        }
    ).setView(
        [20, 20],
        2
    );


    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {

            attribution:
                "&copy; OpenStreetMap contributors",

            noWrap:
                true

        }
    ).addTo(
        map
    );


    setTimeout(
        () => {

            map.invalidateSize();

        },
        300
    );


    return map;

}


// =========================================
// Map Country Markers
// =========================================

function renderMapCountries(
    map,
    countries
) {

    countries.forEach(
        country => {

            if (
                country.lat == null
                || country.lng == null
            ) {

                return;

            }


            let color =
                "green";


            switch (
                country.status
            ) {

                case "yellow":

                    color =
                        "orange";

                    break;


                case "orange":

                    color =
                        "darkorange";

                    break;


                case "red":

                    color =
                        "red";

                    break;

            }


            L.circleMarker(
                [
                    country.lat,
                    country.lng
                ],
                {

                    radius:
                        8,

                    color:
                        color,

                    fillColor:
                        color,

                    fillOpacity:
                        0.8

                }
            )
            .addTo(
                map
            )
            .bindPopup(
                `

                    <strong>

                        ${country.flag
                        || "🌍"}

                        ${country.name}

                    </strong>

                    <br>

                    ${country.issue
                    || "특이사항 없음"}

                `
            );

        }
    );

}


console.log(
    "KOICA-NGO Dashboard loaded"
);

// ==========================================
// 최근 주요 안전 이슈
// ==========================================

function renderRecentIssues(issues) {

    const container =
        document.getElementById("recentIssues");

    if (!container) {
        return;
    }

    if (!issues || issues.length === 0) {

        container.innerHTML = `
            <div class="text-success">
                현재 등록된 주요 안전 이슈가 없습니다.
            </div>
        `;

        return;
    }

    // 최신 날짜 순으로 정렬
    const sortedIssues = [...issues].sort(
        (a, b) => {

            const dateA =
                new Date(a.published_at);

            const dateB =
                new Date(b.published_at);

            return dateB - dateA;
        }
    );

    let html = "";

    sortedIssues
        .slice(0, 10)
        .forEach(issue => {

            const severity = getSeverityInfo(
                issue.severity
            );

            const category = getCategoryInfo(
                issue.category
            );

            const sourceBadge =
                issue.source ===
                "외교부 해외안전공지"
                    ? `
                    <span class="badge bg-primary">
                        🏛️ 외교부
                    </span>
                    `
                    : `
                    <span class="badge bg-dark">
                        📰 뉴스
                    </span>
                    `;

            const sourceLink =
                issue.source_url
                    ? `
                    <a
                        href="${issue.source_url}"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="btn btn-sm btn-outline-secondary mt-2"
                    >
                        원문 보기
                    </a>
                    `
                    : "";

            html += `

                <div class="
                    border
                    rounded
                    p-3
                    mb-3
                    bg-white
                ">

                    <div class="
                        d-flex
                        justify-content-between
                        align-items-start
                        flex-wrap
                        gap-2
                    ">

                        <div>

                            <strong>
                                ${issue.country}
                            </strong>

                            ${sourceBadge}

                            <span
                                class="
                                    badge
                                    ${severity.className}
                                "
                            >
                                ${severity.icon}
                                ${severity.label}
                            </span>

                            <span class="
                                badge
                                bg-light
                                text-dark
                                border
                            ">
                                ${category.icon}
                                ${category.label}
                            </span>

                        </div>

                        <small class="
                            text-muted
                        ">
                            ${issue.published_at || ""}
                        </small>

                    </div>

                    <h5 class="mt-3">

                        ${issue.title}

                    </h5>

                    <p class="
                        mb-2
                        text-secondary
                    ">

                        ${issue.summary || ""}

                    </p>

                    <div class="
                        alert
                        alert-light
                        mb-2
                    ">

                        <strong>
                            봉사단 영향:
                        </strong>

                        ${issue.volunteer_impact || ""}

                    </div>

                    <div class="
                        alert
                        alert-warning
                        mb-2
                    ">

                        <strong>
                            권장 조치:
                        </strong>

                        ${issue.recommended_action || ""}

                    </div>

                    ${sourceLink}

                </div>

            `;
        });

    container.innerHTML = html;
}


// ==========================================
// 위험도 표시
// ==========================================

function getSeverityInfo(severity) {

    switch (severity) {

        case "critical":

            return {
                icon: "🔴",
                label: "긴급",
                className: "bg-danger"
            };

        case "high":

            return {
                icon: "🟠",
                label: "높음",
                className: "bg-warning text-dark"
            };

        case "medium":

            return {
                icon: "🟡",
                label: "주의",
                className: "bg-info text-dark"
            };

        default:

            return {
                icon: "🟢",
                label: "낮음",
                className: "bg-success"
            };

    }

}


// ==========================================
// 이슈 유형 표시
// ==========================================

function getCategoryInfo(category) {

    switch (category) {

        case "natural_disaster":

            return {
                icon: "🌪️",
                label: "자연재해"
            };

        case "health":

            return {
                icon: "🦠",
                label: "보건·감염병"
            };

        case "transport":

            return {
                icon: "✈️",
                label: "교통·항공"
            };

        case "conflict":

            return {
                icon: "⚠️",
                label: "분쟁·시위"
            };

        case "security":

            return {
                icon: "🚨",
                label: "치안·범죄"
            };

        default:

            return {
                icon: "📢",
                label: "안전공지"
            };

    }

}
