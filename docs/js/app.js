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
            updateRes
        ] = await Promise.all([
            fetch("data/countries.json"),
            fetch("data/briefing.json"),
            fetch("data/daily_report.json"),
            fetch("data/last_update.json")
        ]);

        const countries = await countriesRes.json();
        const briefing = await briefingRes.json();
        const report = await reportRes.json();
        const update = await updateRes.json();

        document.getElementById("lastUpdate").textContent =
            update.updated;

        renderSummary(countries);

        renderTodayChanges(report);

        renderBriefing(briefing);

        renderCountries(countries);

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
