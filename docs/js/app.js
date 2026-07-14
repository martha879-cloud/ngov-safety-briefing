console.log("NGOV Safety Briefing v1.0");
async function loadCountries() {

    const response = await fetch("data/countries.json");

    const countries = await response.json();

    const list = document.getElementById("countryList");

    list.innerHTML = "";

    countries.forEach(country => {

        let badge = "success";
        let text = "활동 가능";

        if(country.status==="yellow"){
            badge="warning";
            text="모니터링";
        }

        if(country.status==="orange"){
            badge="warning";
            text="조치 검토";
        }

        if(country.status==="red"){
            badge="danger";
            text="긴급 대응";
        }

        list.innerHTML += `
            <div class="col-md-3">
                <div class="card h-100">
                    <div class="card-body">

                        <h5>${country.name}</h5>

                        <small>${country.region}</small>

                        <hr>

                        <span class="badge bg-${badge}">
                            ${text}
                        </span>

                    </div>
                </div>
            </div>
        `;
    });

}

loadCountries();
