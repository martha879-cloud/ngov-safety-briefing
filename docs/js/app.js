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

        // last_update.json
        const updateRes = await fetch("data/last_update.json");
        const update = await updateRes.json();

        document.getElementById("lastUpdate").innerHTML = update.updated;

        renderBriefing(briefing);

        renderCountries(countries);

    } catch (e) {

        console.error(e);

        document.getElementById("briefing").innerHTML =
            "데이터를 불러오지 못했습니다.";

    }

}
