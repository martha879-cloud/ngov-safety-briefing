// =========================================
// KOICA-NGO Safety Dashboard v3.0
// =========================================

document.addEventListener("DOMContentLoaded", () => {
    loadDashboard();
});


async function loadDashboard() {

    try {

        const [
            countriesRes,
            briefingRes,
            reportRes,
            updateRes,
            issuesRes
        ] = await Promise.all([

            fetch("./data/countries.json"),

            fetch("./data/briefing.json"),

            fetch("./data/daily_report.json"),

            fetch("./data/last_update.json"),

            fetch("./data/safety_issues.json")

        ]);


        if (!countriesRes.ok) {
            throw new Error(
                `countries.json 오류: ${countriesRes.status}`
            );
        }


        const countries = await countriesRes.json();


        let briefing = {
            summary: []
        };


        let report = {
            changes: []
        };


        let update = {
            updated: "-"
        };


        let safetyData = {
            issues: []
        };


        if (briefingRes.ok) {

            briefing = await briefingRes.json();

        }


        if (reportRes.ok) {

            report = await reportRes.json();

        }


        if (updateRes.ok) {

            update = await updateRes.json();

        }


        if (issuesRes.ok) {

            safetyData = await issuesRes.json();

        }


        document.getElementById(
            "lastUpdate"
        ).textContent = update.updated || "-";


        renderSummary(
            countries,
            safetyData.issues
        );


        renderBriefing(
            briefing,
            safetyData.issues
        );


        renderTodayChanges(
            report
        );


        renderRecentIssues(
            safetyData.issues
        );


        renderCountries(
            countries,
            safetyData.issues
        );


        const map = initMap();


        renderMapCountries(
            map,
            countries,
            safetyData.issues
        );


    } catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );


        const briefingBox =
            document.getElementById(
                "briefing"
            );


        if (briefingBox) {

            briefingBox.innerHTML = `

                <div class="alert alert-danger">

                    데이터를 불러오지 못했습니다.

                    <br>

                    <small>
                        ${error.message}
                    </small>

                </div>

            `;

        }

    }

}


// =========================================
// Summary
// =========================================

function renderSummary(
    countries,
    issues
) {

    let green = 0;

    let yellow = 0;

    let orange = 0;

    let red = 0;


    countries.forEach(country => {

        const countryIssues =
            issues.filter(
                issue =>
                    issue.country ===
                    country.name
            );


        let highestSeverity =
            "none";


        countryIssues.forEach(
            issue => {

                const severity =
                    issue.severity;


                if (
                    severity ===
                    "critical"
                ) {

                    highestSeverity =
                        "critical";

                }

                else if (
                    severity ===
                    "high" &&
                    highestSeverity !==
                    "critical"
                ) {

                    highestSeverity =
                        "high";

                }

                else if (
                    severity ===
                    "medium" &&
                    highestSeverity ===
                    "none"
                ) {

                    highestSeverity =
                        "medium";

                }

            }
        );


        if (
            highestSeverity ===
            "critical"
        ) {

            red++;

        }

        else if (
            highestSeverity ===
            "high"
        ) {

            orange++;

        }

        else if (
            highestSeverity ===
            "medium"
        ) {

            yellow++;

        }

        else {

            green++;

        }

    });


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
// Briefing
// =========================================

function renderBriefing(
    briefing,
    issues
) {

    const box =
        document.getElementById(
            "briefing"
        );


    if (!box) {

        return;

    }


    if (
        issues &&
        issues.length > 0
    ) {

        const highCount =
            issues.filter(
                issue =>
                    issue.severity ===
                    "high" ||
                    issue.severity ===
                    "critical"
            ).length;


        box.innerHTML = `

            <div class="mb-2">

                오늘 확인된 주요 안전 이슈는

                <strong>
                    ${issues.length}건
                </strong>
                입니다.

            </div>

            <div>

                우선 확인이 필요한 이슈는

                <strong>
                    ${highCount}건
                </strong>
                입니다.

            </div>

        `;

        return;

    }


    if (
        briefing &&
        Array.isArray(
            briefing.summary
        )
    ) {

        box.innerHTML =
            briefing.summary
                .map(
                    text =>
                        `<div>
                            ✅ ${text}
                        </div>`
                )
                .join("");

        return;

    }


    box.innerHTML = `

        <div class="text-success">

            현재 등록된 주요 안전 이슈가 없습니다.

        </div>

    `;

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


    if (
        !report ||
        !Array.isArray(
            report.changes
        ) ||
        report.changes.length === 0
    ) {

        box.innerHTML = `

            <div class="text-muted">

                현재 등록된 변경사항이 없습니다.

            </div>

        `;

        return;

    }


    box.innerHTML =
        report.changes
            .map(
                item => `

                <div class="border-bottom py-2">

                    <strong>

                        ${item.flag || "🌍"}

                        ${item.country}

                    </strong>

                    <div>

                        ${item.change}

                    </div>

                    <small class="text-muted">

                        ${item.reason || ""}

                    </small>

                </div>

            `
            )
            .join("");

}


// =========================================
// Recent Issues
// =========================================

function renderRecentIssues(
    issues
) {

    const box =
        document.getElementById(
            "recentIssues"
        );


    if (!box) {

        return;

    }


    if (
        !issues ||
        issues.length === 0
    ) {

        box.innerHTML = `

            <div class="text-success">

                최근 주요 안전 이슈가 없습니다.

            </div>

        `;

        return;

    }


    const severityOrder = {

        critical: 4,

        high: 3,

        medium: 2,

        low: 1

    };


    const sortedIssues =
        [...issues].sort(
            (a, b) =>

                (
                    severityOrder[
                        b.severity
                    ] || 0
                )

                -

                (
                    severityOrder[
                        a.severity
                    ] || 0
                )
        );


    box.innerHTML =
        sortedIssues
            .map(
                issue => `

                <div class="border-bottom py-3">

                    <div class="d-flex
                                justify-content-between
                                align-items-start">

                        <div>

                            <strong>

                                ${issue.country}

                            </strong>

                            ${categoryLabel(
                                issue.category
                            )}

                        </div>

                        ${severityBadge(
                            issue.severity
                        )}

                    </div>

                    <div class="mt-2">

                        <strong>

                            ${issue.title}

                        </strong>

                    </div>

                    <div class="text-muted mt-1">

                        ${issue.summary}

                    </div>

                    <div class="mt-2">

                        <small>

                            <strong>
                                봉사단 영향:
                            </strong>

                            ${issue.volunteer_impact}

                        </small>

                    </div>

                    <div>

                        <small>

                            <strong>
                                권장 조치:
                            </strong>

                            ${issue.recommended_action}

                        </small>

                    </div>

                    <div class="mt-2">

                        <small class="text-muted">

                            ${issue.published_at}

                            ·

                            ${issue.source}

                        </small>

                    </div>

                </div>

            `
            )
            .join("");

}


// =========================================
// Countries
// =========================================

function renderCountries(
    countries,
    issues
) {

    const containers = {

        asia:
            document.getElementById(
                "asiaList"
            ),

        africa:
            document.getElementById(
                "africaList"
            ),

        latin:
            document.getElementById(
                "latinList"
            ),

        middle:
            document.getElementById(
                "middleList"
            )

    };


    Object.values(
        containers
    ).forEach(
        container => {

            if (container) {

                container.innerHTML = "";

            }

        }
    );


    countries.forEach(
        country => {

            const countryIssues =
                issues.filter(
                    issue =>
                        issue.country ===
                        country.name
                );


            const card =
                createCountryCard(
                    country,
                    countryIssues
                );


            const container =
                containers[
                    country.region
                ];


            if (container) {

                container.innerHTML +=
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

    const mainIssue =
        getMainIssue(
            issues
        );


    let issueHtml = `

        <div class="text-success mt-3">

            🟢 최근 등록된
            주요 안전 이슈 없음

        </div>

    `;


    if (mainIssue) {

        issueHtml = `

            <div class="mt-3">

                ${categoryLabel(
                    mainIssue.category
                )}

                ${severityBadge(
                    mainIssue.severity
                )}

            </div>

            <div class="mt-2">

                <strong>

                    ${mainIssue.title}

                </strong>

            </div>

            <div class="text-muted mt-1">

                ${mainIssue.summary}

            </div>

            <div class="mt-2">

                <small>

                    <strong>
                        권장 조치:
                    </strong>

                    ${mainIssue.recommended_action}

                </small>

            </div>

        `;

    }


    return `

        <div class="col-lg-4 col-md-6">

            <div class="country-card h-100">

                <div class="country-name">

                    ${country.flag || "🌍"}

                    ${country.name}

                </div>

                ${issueHtml}

                <div class="mt-3">

                    <small class="text-muted">

                        여행경보:

                        ${country.travel_warning_level
                            || "-"}

                        단계

                        ${country.travel_warning_label
                            || ""}

                    </small>

                </div>

            </div>

        </div>

    `;

}


// =========================================
// Main Issue
// =========================================

function getMainIssue(
    issues
) {

    if (
        !issues ||
        issues.length === 0
    ) {

        return null;

    }


    const order = {

        critical: 4,

        high: 3,

        medium: 2,

        low: 1

    };


    return [...issues].sort(
        (a, b) =>

            (
                order[
                    b.severity
                ] || 0
            )

            -

            (
                order[
                    a.severity
                ] || 0
            )
    )[0];

}


// =========================================
// Labels
// =========================================

function categoryLabel(
    category
) {

    const labels = {

        security:
            "🚨 치안",

        conflict:
            "⚔️ 분쟁·정세",

        natural_disaster:
            "🌧️ 재난·기상",

        health:
            "🦠 보건·감염병",

        transport:
            "✈️ 이동·교통",

        official_notice:
            "📢 안전공지"

    };


    return labels[
        category
    ] || "📌 기타";

}


function severityBadge(
    severity
) {

    const badges = {

        critical:
            `<span class="badge bg-danger">
                🔴 즉시 확인
            </span>`,

        high:
            `<span class="badge bg-warning text-dark">
                🟠 우선 확인
            </span>`,

        medium:
            `<span class="badge bg-info text-dark">
                🟡 모니터링
            </span>`,

        low:
            `<span class="badge bg-secondary">
                참고
            </span>`

    };


    return badges[
        severity
    ] || "";

}


// =========================================
// Map
// =========================================

function initMap() {

    const map = L.map(
        "map"
    ).setView(
        [20, 20],
        2
    );


    L.tileLayer(

        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",

        {

            attribution:
                "&copy; OpenStreetMap contributors"

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


function renderMapCountries(
    map,
    countries,
    issues
) {

    countries.forEach(
        country => {

            if (
                country.lat == null ||
                country.lng == null
            ) {

                return;

            }


            const countryIssues =
                issues.filter(
                    issue =>
                        issue.country ===
                        country.name
                );


            const mainIssue =
                getMainIssue(
                    countryIssues
                );


            let color =
                "green";


            if (
                mainIssue
            ) {

                if (
                    mainIssue.severity ===
                    "critical"
                ) {

                    color = "red";

                }

                else if (
                    mainIssue.severity ===
                    "high"
                ) {

                    color = "orange";

                }

                else if (
                    mainIssue.severity ===
                    "medium"
                ) {

                    color = "gold";

                }

            }


            L.circleMarker(

                [
                    country.lat,
                    country.lng
                ],

                {

                    radius: 8,

                    color: color,

                    fillColor: color,

                    fillOpacity: 0.8

                }

            )

            .addTo(
                map
            )

            .bindPopup(`

                <strong>

                    ${country.flag || "🌍"}

                    ${country.name}

                </strong>

                <br>

                ${mainIssue
                    ? mainIssue.title
                    : "최근 주요 이슈 없음"}

            `);

        }
    );

}
