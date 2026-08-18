// 안전관리 아카이브 페이지 로직.
// event_log.json(전체 변경 이력) / status_timeseries.json(국가별 상태 시계열) /
// status_history_full.json(전체 국가수 색상별 분포 추이) / countries.json 을 읽어서
// 차트 2개 + 이벤트 목록 2개를 그린다.

const STATUS_COLOR = {
    green: "#198754",
    yellow: "#ffc107",
    orange: "#fd7e14",
    red: "#dc3545",
};

const STATUS_LABEL_KO = {
    green: "🟢 활동 가능",
    yellow: "🟡 모니터링",
    orange: "🟠 조치 검토",
    red: "🔴 긴급 대응",
};

const SEVERITY_TO_STATUS = ["green", "yellow", "orange", "red"];

let overallChartInstance = null;
let countryChartInstance = null;

let allCountries = [];
let allEventLog = [];
let allTimeseries = {};
let allHistoryFull = [];

async function safeFetchJson(url, fallback) {

    try {

        const bustedUrl = url + (url.includes("?") ? "&" : "?") + "t=" + Date.now();

        const res = await fetch(bustedUrl, { cache: "no-store" });

        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }

        return await res.json();

    } catch (err) {

        console.warn(`${url} 로드 실패, 기본값 사용:`, err);

        return fallback;

    }

}

function formatDateLabel(dateStr) {
    // "2026-08-18" -> "8/18"
    const parts = (dateStr || "").split("-");
    if (parts.length !== 3) return dateStr;
    return `${parseInt(parts[1], 10)}/${parseInt(parts[2], 10)}`;
}

function filterByRange(historyFull, range) {

    if (range === "all") {
        return historyFull;
    }

    const days = parseInt(range, 10);

    return historyFull.slice(-days);

}

function renderOverallChart(range) {

    const emptyEl = document.getElementById("overallEmpty");
    const canvasEl = document.getElementById("overallChart");

    if (!allHistoryFull.length) {
        emptyEl.style.display = "block";
        canvasEl.style.display = "none";
        return;
    }

    emptyEl.style.display = "none";
    canvasEl.style.display = "block";

    const rows = filterByRange(allHistoryFull, range);

    const labels = rows.map(r => r.label || formatDateLabel(r.date));

    const datasets = ["green", "yellow", "orange", "red"].map(status => ({
        label: STATUS_LABEL_KO[status],
        data: rows.map(r => r[status] || 0),
        backgroundColor: STATUS_COLOR[status],
        borderColor: STATUS_COLOR[status],
        fill: true,
        stack: "status",
        tension: 0.15,
    }));

    if (overallChartInstance) {
        overallChartInstance.destroy();
    }

    overallChartInstance = new Chart(canvasEl.getContext("2d"), {
        type: "bar",
        data: { labels, datasets },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "bottom" },
                tooltip: { mode: "index", intersect: false },
            },
            scales: {
                x: { stacked: true },
                y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } },
            },
        },
    });

}

function populateCountrySelect() {

    const select = document.getElementById("countrySelect");
    select.innerHTML = "";

    // 지역 구분 없이 이름 가나다순으로 (국가 수가 20개라 충분히 다루기 쉬움)
    const sorted = [...allCountries].sort((a, b) => a.name.localeCompare(b.name, "ko"));

    sorted.forEach(country => {
        const option = document.createElement("option");
        option.value = country.name;
        option.textContent = `${country.flag} ${country.name}`;
        select.appendChild(option);
    });

    select.addEventListener("change", () => renderCountrySection(select.value));

    if (sorted.length) {
        renderCountrySection(sorted[0].name);
    }

}

function renderCountryChart(countryName) {

    const series = allTimeseries[countryName] || [];
    const canvasEl = document.getElementById("countryChart");

    const labels = series.map(e => formatDateLabel(e.date));
    const data = series.map(e => e.severity_num ?? 0);

    if (countryChartInstance) {
        countryChartInstance.destroy();
    }

    countryChartInstance = new Chart(canvasEl.getContext("2d"), {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "위험 단계",
                data,
                stepped: true,
                borderColor: "#0d6efd",
                backgroundColor: "rgba(13,110,253,0.15)",
                fill: true,
                pointBackgroundColor: series.map(e => STATUS_COLOR[e.status] || "#999"),
                pointRadius: 4,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => {
                            const status = series[ctx.dataIndex]?.status;
                            return STATUS_LABEL_KO[status] || "";
                        },
                    },
                },
            },
            scales: {
                y: {
                    min: 0,
                    max: 3,
                    ticks: {
                        stepSize: 1,
                        callback: value => STATUS_LABEL_KO[SEVERITY_TO_STATUS[value]] || value,
                    },
                },
            },
        },
    });

}

function renderCountryEvents(countryName) {

    const container = document.getElementById("countryEvents");

    const events = allEventLog
        .filter(e => e.country === countryName)
        .sort((a, b) => (a.date < b.date ? 1 : -1));

    if (!events.length) {
        container.innerHTML = `<p class="text-muted mb-0">아직 기록된 변경 이력이 없습니다.</p>`;
        return;
    }

    container.innerHTML = events.map(e => `
        <div class="change-item">
            <div class="d-flex justify-content-between flex-wrap">
                <h6 class="mb-1">${e.source || ""} · ${e.change || ""}</h6>
                <span class="text-muted small">${e.date}</span>
            </div>
            ${e.reason ? `<div class="small">${e.reason}</div>` : ""}
        </div>
    `).join("");

}

function renderCountrySection(countryName) {
    renderCountryChart(countryName);
    renderCountryEvents(countryName);
}

function renderAllEvents() {

    const container = document.getElementById("allEvents");

    const events = [...allEventLog].sort((a, b) => (a.date < b.date ? 1 : -1)).slice(0, 200);

    if (!events.length) {
        container.innerHTML = `<p class="text-muted mb-0">아직 쌓인 변경 이력이 없습니다.</p>`;
        return;
    }

    container.innerHTML = events.map(e => `
        <div class="change-item">
            <div class="d-flex justify-content-between flex-wrap">
                <h6 class="mb-1">${e.flag || ""} ${e.country || ""} · ${e.source || ""}</h6>
                <span class="text-muted small">${e.date}</span>
            </div>
            <div class="small mb-1"><strong>${e.change || ""}</strong></div>
            ${e.reason ? `<div class="small">${e.reason}</div>` : ""}
        </div>
    `).join("");

}

function setupRangeButtons() {

    const buttons = document.querySelectorAll("#rangeButtons button");

    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            buttons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            renderOverallChart(btn.dataset.range);
        });
    });

}

async function init() {

    const [countries, eventLog, timeseries, historyFull] = await Promise.all([
        safeFetchJson("data/countries.json", []),
        safeFetchJson("data/archive/event_log.json", []),
        safeFetchJson("data/archive/status_timeseries.json", {}),
        safeFetchJson("data/archive/status_history_full.json", []),
    ]);

    allCountries = countries;
    allEventLog = eventLog;
    allTimeseries = timeseries;
    allHistoryFull = historyFull;

    setupRangeButtons();
    renderOverallChart("all");
    populateCountrySelect();
    renderAllEvents();

}

document.addEventListener("DOMContentLoaded", init);
