// ===============================
// KOICA-NGO Safety Dashboard
// ===============================

const countries = [
    // Asia / CIS
    { id:"timor-leste", flag:"🇹🇱", name:"동티모르", region:"asia", status:"green"},
    { id:"laos", flag:"🇱🇦", name:"라오스", region:"asia", status:"green"},
    { id:"mongolia", flag:"🇲🇳", name:"몽골", region:"asia", status:"green"},
    { id:"bangladesh", flag:"🇧🇩", name:"방글라데시", region:"asia", status:"yellow"},
    { id:"vietnam", flag:"🇻🇳", name:"베트남", region:"asia", status:"green"},
    { id:"indonesia", flag:"🇮🇩", name:"인도네시아", region:"asia", status:"green"},
    { id:"cambodia", flag:"🇰🇭", name:"캄보디아", region:"asia", status:"green"},
    { id:"philippines", flag:"🇵🇭", name:"필리핀", region:"asia", status:"green"},
    { id:"kyrgyzstan", flag:"🇰🇬", name:"키르기스스탄", region:"asia", status:"green"},

    // Africa
    { id:"rwanda", flag:"🇷🇼", name:"르완다", region:"africa", status:"green"},
    { id:"malawi", flag:"🇲🇼", name:"말라위", region:"africa", status:"green"},
    { id:"morocco", flag:"🇲🇦", name:"모로코", region:"africa", status:"green"},
    { id:"uganda", flag:"🇺🇬", name:"우간다", region:"africa", status:"green"},
    { id:"egypt", flag:"🇪🇬", name:"이집트", region:"africa", status:"green"},
    { id:"tanzania", flag:"🇹🇿", name:"탄자니아", region:"africa", status:"green"},
    { id:"kenya", flag:"🇰🇪", name:"케냐", region:"africa", status:"yellow"},

    // Latin America
    { id:"guatemala", flag:"🇬🇹", name:"과테말라", region:"latin", status:"green"},
    { id:"dominican", flag:"🇩🇴", name:"도미니카공화국", region:"latin", status:"green"},
    { id:"peru", flag:"🇵🇪", name:"페루", region:"latin", status:"yellow"},

    // Middle East
    { id:"jordan", flag:"🇯🇴", name:"요르단", region:"middle", status:"green"}
];

const regionMap = {
    asia: document.getElementById("asiaList"),
    africa: document.getElementById("africaList"),
    latin: document.getElementById("latinList"),
    middle: document.getElementById("middleList")
};

// 마지막 업데이트
document.getElementById("lastUpdate").textContent =
    new Date().toLocaleString("ko-KR");

// 브리핑 예시
document.getElementById("briefing").innerHTML = `
<ul class="mb-0">
<li>외교부 신규 여행경보 변경 없음</li>
<li>WHO 감염병 특이사항 없음</li>
<li>USGS 규모 5.0 이상 지진 모니터링 중</li>
</ul>
`;

// 우선 확인 국가
document.getElementById("priorityCountries").innerHTML = `
<ul class="mb-0">
<li>🇰🇪 케냐 - 홍수 모니터링</li>
<li>🇵🇪 페루 - 지진 정보 확인</li>
<li>🇧🇩 방글라데시 - 시위 동향 확인</li>
</ul>
`;

let green=0;
let yellow=0;
let orange=0;
let red=0;

countries.forEach(country=>{

    switch(country.status){
        case "green": green++; break;
        case "yellow": yellow++; break;
        case "orange": orange++; break;
        case "red": red++; break;
    }

    const colorClass={
        green:"status-green",
        yellow:"status-yellow",
        orange:"status-orange",
        red:"status-red"
    };

    const statusText={
        green:"정상 활동",
        yellow:"모니터링",
        orange:"조치 검토",
        red:"긴급 대응"
    };

    const card=`
<div class="col-lg-3 col-md-4 col-6">

<div class="country-card"
onclick="location.href='country.html?id=${country.id}'">

<div class="country-name">

${country.flag} ${country.name}

</div>

<div class="country-status ${colorClass[country.status]}">

${statusText[country.status]}

</div>

<div class="country-update">

📅 ${new Date().toLocaleDateString("ko-KR")}

</div>

</div>

</div>
`;

    regionMap[country.region].innerHTML+=card;

});

document.getElementById("greenCount").textContent=green;
document.getElementById("yellowCount").textContent=yellow;
document.getElementById("orangeCount").textContent=orange;
document.getElementById("redCount").textContent=red;
