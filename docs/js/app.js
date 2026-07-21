// =========================================
// KOICA-NGO Dashboard v1.0
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
    historyRes
] = await Promise.all([
    fetch("data/countries.json"),
    fetch("data/briefing.json"),
    fetch("data/daily_report.json"),
    fetch("data/last_update.json"),
    fetch("data/history.json")
]);
        const history = await historyRes.json();
        const countries = await countriesRes.json();
        const briefing = await briefingRes.json();
        const report = await reportRes.json();
        const update = await updateRes.json();

        // 마지막 업데이트
        document.getElementById("lastUpdate").textContent = update.updated;

        // KPI
        renderSummary(countries);

        // 브리핑
        renderBriefing(briefing);

        // 변경사항
        renderTodayChanges(report);

        // 국가 카드
        renderCountries(countries);

        // 지도
        const map = initMap();
        renderMapCountries(map, countries);

    } catch (err) {

        console.error(err);

        document.getElementById("briefing").innerHTML =
            "<div class='text-danger'>데이터를 불러오지 못했습니다.</div>";

    }
}

// ===========================
// Summary
// ===========================

function renderSummary(countries){

    let green=0;
    let yellow=0;
    let orange=0;
    let red=0;

    countries.forEach(c=>{

        switch(c.status){

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

    });

    document.getElementById("greenCount").textContent=green;
    document.getElementById("yellowCount").textContent=yellow;
    document.getElementById("orangeCount").textContent=orange;
    document.getElementById("redCount").textContent=red;

}

// ===========================
// Today Changes
// ===========================

function renderTodayChanges(report){

    const box=document.getElementById("todayChanges");

    if(!box) return;

    if(!report.changes || report.changes.length===0){

        box.innerHTML=
        "<div class='text-success'>오늘 변경사항이 없습니다.</div>";

        return;

    }

    let html="";

    report.changes.forEach(item=>{

        html+=`

        <div class="change-item">

            <h5>${item.flag} ${item.country}</h5>

            <div><strong>${item.change}</strong></div>

            <div>${item.reason}</div>

        </div>

        `;

    });

    box.innerHTML=html;

}

// ===========================
// Briefing
// ===========================

function renderBriefing(data){

    let html="";

    data.summary.forEach(text=>{

        html+=`<div>✅ ${text}</div>`;

    });

    document.getElementById("briefing").innerHTML=html;

}
// ===========================
// Countries
// ===========================

function renderCountries(countries){

    // 지역별 컨테이너
    const asiaList = document.getElementById("asiaList");
    const africaList = document.getElementById("africaList");
    const latinList = document.getElementById("latinList");
    const middleList = document.getElementById("middleList");

    // 기존 내용 초기화
    asiaList.innerHTML = "";
    africaList.innerHTML = "";
    latinList.innerHTML = "";
    middleList.innerHTML = "";

    countries.forEach(country => {

        const card = createCountryCard(country);

        switch(country.region){

            case "asia":
                asiaList.innerHTML += card;
                break;

            case "africa":
                africaList.innerHTML += card;
                break;

            case "latin":
                latinList.innerHTML += card;
                break;

            case "middle":
                middleList.innerHTML += card;
                break;

            default:
                asiaList.innerHTML += card;
        }

    });

}

// ===========================
// Country Card
// ===========================

function createCountryCard(country){

    return `

   <div class="col-lg-4 col-md-6">

        <div class="country-card">

            <div class="country-name">

                ${country.flag || "🌍"} ${country.name}

            </div>

            <div class="mt-2">

                ${statusBadge(country.status)}

            </div>

            <div class="mt-3">

                <strong>상황</strong><br>

                ${country.issue || "특이사항 없음"}

            </div>

            <div class="mt-3">

                <small class="text-muted">

                    ${country.source || ""}

                </small>

            </div>

            <div>

                <small class="text-muted">

                    ${country.updated || ""}

                </small>

            </div>

        </div>

    </div>

    `;

}

// ===========================
// Status Badge
// ===========================

function statusBadge(status){

    switch(status){

        case "green":
            return `<span class="badge bg-success">🟢 활동 가능</span>`;

        case "yellow":
            return `<span class="badge bg-warning text-dark">🟡 모니터링</span>`;

        case "orange":
            return `<span class="badge bg-orange">🟠 조치 검토</span>`;

        case "red":
            return `<span class="badge bg-danger">🔴 긴급 대응</span>`;

        default:
            return `<span class="badge bg-secondary">정보 없음</span>`;
    }

}
function initMap() {

    const map = L.map("map", {
        worldCopyJump: false,
        maxBounds: [[-90, -180], [90, 180]],
        maxBoundsViscosity: 1.0
    }).setView([20, 20], 2);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        noWrap: true
    }).addTo(map);

    setTimeout(() => {
        map.invalidateSize();
    }, 200);

    return map;
}

function renderMapCountries(map, countries) {

    countries.forEach(country => {

        if (country.lat == null || country.lng == null) {
            return;
        }

        let color = "green";

        switch (country.status) {

            case "yellow":
                color = "orange";
                break;

            case "orange":
                color = "darkorange";
                break;

            case "red":
                color = "red";
                break;
        }

        L.circleMarker([country.lat, country.lng], {

            radius: 8,
            color: color,
            fillColor: color,
            fillOpacity: 0.8

        })
        .addTo(map)
        .bindPopup(`
            <strong>${country.flag} ${country.name}</strong><br>
            ${country.issue}
        `);

    });

}
console.log("Dashboard v2.0 loaded");
