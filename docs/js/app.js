// ==========================
// KOICA-NGO Dashboard v0.5
// ==========================

document.addEventListener("DOMContentLoaded", () => {
    loadDashboard();
});

async function loadDashboard() {

    try {

        // countries.json
        const countryRes = await fetch("data/countries.json");
        const countries = await countryRes.json();

        // briefing.json
        const briefingRes = await fetch("data/briefing.json");
        const briefing = await briefingRes.json();
        
        const reportRes = await fetch("data/daily_report.json");
        const report = await reportRes.json();

        const updateRes = await fetch("data/last_update.json");
        const update = await updateRes.json();

        document.getElementById("lastUpdate").innerHTML = update.updated;

function renderTodayChanges(report){

    const box = document.getElementById("todayChanges");

    if(!box) return;

    if(report.changes.length===0){

        box.innerHTML="<div class='text-success'>오늘 변경사항이 없습니다.</div>";

        return;

    }

    let html="";

    report.changes.forEach(item=>{

        html+=`

        <div class="change-item">

            <h5>${item.flag} ${item.country}</h5>

            <strong>${item.change}</strong><br>

            ${item.reason}

        </div>

        `;

    });

    box.innerHTML=html;

}

renderBriefing(briefing);

renderCountries(countries);
    } catch (e) {

        console.error(e);

        document.getElementById("briefing").innerHTML =
            "데이터를 불러오지 못했습니다.";

    }

}

function renderBriefing(data){

    let html="";

    data.summary.forEach(item=>{

        html+=`<div class="mb-2">✅ ${item}</div>`;

    });

    document.getElementById("briefing").innerHTML=html;

}

function renderCountries(countries){

    let green=0;
    let yellow=0;
    let orange=0;
    let red=0;

    countries.forEach(country=>{

        switch(country.status){

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

        createCountryCard(country);

    });

    document.getElementById("greenCount").innerHTML=green;
    document.getElementById("yellowCount").innerHTML=yellow;
    document.getElementById("orangeCount").innerHTML=orange;
    document.getElementById("redCount").innerHTML=red;

}
function createCountryCard(country){
    
    const asiaList = document.getElementById("asiaList");
    const africaList = document.getElementById("africaList");
    const latinList = document.getElementById("latinList");
    const middleList = document.getElementById("middleList");
    
    const html=`

    <div class="col-lg-3 col-md-4 col-sm-6">

        <div class="country-card">

            <div class="country-name">

                ${country.flag} ${country.name}

            </div>

            <div class="mt-2">

                ${statusBadge(country.status)}

            </div>

            <div class="mt-3">

                ${country.issue}

            </div>

            <small class="text-muted">

                ${country.updated}

            </small>

        </div>

    </div>

    `;

    switch(country.region){

        case "asia":

            asiaList.innerHTML+=html;

            break;

        case "africa":

            africaList.innerHTML+=html;

            break;

        case "latin":

            latinList.innerHTML+=html;

            break;

        case "middle":

            middleList.innerHTML+=html;

            break;

    }

}
function statusBadge(status){

    switch(status){

        case "green":

            return `<span class="badge bg-success">🟢 활동 가능</span>`;

        case "yellow":

            return `<span class="badge bg-warning text-dark">🟡 모니터링</span>`;

        case "orange":

            return `<span class="badge bg-orange text-white">🟠 조치 검토</span>`;

        case "red":

            return `<span class="badge bg-danger">🔴 긴급 대응</span>`;

    }

}
