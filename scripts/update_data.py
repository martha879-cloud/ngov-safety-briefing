COUNTRIES = [
    # Asia / CIS
    {"id":"timor-leste","name":"동티모르","flag":"🇹🇱","region":"asia"},
    {"id":"laos","name":"라오스","flag":"🇱🇦","region":"asia"},
    {"id":"mongolia","name":"몽골","flag":"🇲🇳","region":"asia"},
    {"id":"bangladesh","name":"방글라데시","flag":"🇧🇩","region":"asia"},
    {"id":"vietnam","name":"베트남","flag":"🇻🇳","region":"asia"},
    {"id":"indonesia","name":"인도네시아","flag":"🇮🇩","region":"asia"},
    {"id":"cambodia","name":"캄보디아","flag":"🇰🇭","region":"asia"},
    {"id":"philippines","name":"필리핀","flag":"🇵🇭","region":"asia"},
    {"id":"kyrgyzstan","name":"키르기스스탄","flag":"🇰🇬","region":"asia"},

    # Africa
    {"id":"rwanda","name":"르완다","flag":"🇷🇼","region":"africa"},
    {"id":"malawi","name":"말라위","flag":"🇲🇼","region":"africa"},
    {"id":"morocco","name":"모로코","flag":"🇲🇦","region":"africa"},
    {"id":"uganda","name":"우간다","flag":"🇺🇬","region":"africa"},
    {"id":"egypt","name":"이집트","flag":"🇪🇬","region":"africa"},
    {"id":"tanzania","name":"탄자니아","flag":"🇹🇿","region":"africa"},
    {"id":"kenya","name":"케냐","flag":"🇰🇪","region":"africa"},

    # Latin America
    {"id":"guatemala","name":"과테말라","flag":"🇬🇹","region":"latin"},
    {"id":"dominican-republic","name":"도미니카공화국","flag":"🇩🇴","region":"latin"},
    {"id":"peru","name":"페루","flag":"🇵🇪","region":"latin"},

    # Middle East
    {"id":"jordan","name":"요르단","flag":"🇯🇴","region":"middle"}
]
from datetime import datetime

def build_default_country(country):
    return {
        "id": country["id"],
        "name": country["name"],
        "flag": country["flag"],
        "region": country["region"],

        "status": "green",
        "priority": 1,

        "issue": "특이사항 없음",

        "source": "",

        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),

        "links": []
    }
    countries=[]

for country in COUNTRIES:

    countries.append(build_default_country(country))
    import json

with open(DATA_DIR/"countries.json","w",encoding="utf-8") as f:

    json.dump(
        countries,
        f,
        ensure_ascii=False,
        indent=2
    )
