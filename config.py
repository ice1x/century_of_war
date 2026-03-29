"""
config.py
=========
Centralized project settings. Imported by app.py, fetch_wars.py, wars_gantt.py.
"""

from datetime import datetime

# ── General ──────────────────────────────────────────────────────────────────
CURRENT_YEAR = datetime.now().year
CSV_FILE = "wars.csv"

# ── Wikipedia scraper (fetch_wars) ───────────────────────────────────────────
BASE_URL = "https://en.wikipedia.org"
HEADERS = {"User-Agent": "WarsTimelineBot/1.0 (educational project)"}

LIST_PAGES = [
    "/wiki/List_of_wars:_1900%E2%80%931944",
    "/wiki/List_of_wars:_1945%E2%80%931989",
    "/wiki/List_of_wars:_1990%E2%80%932002",
    "/wiki/List_of_wars:_2003%E2%80%93present",
]

# ── Region classification (wars_gantt) ───────────────────────────────────────
REGION_COLORS = {
    "Europe":      "#e05252",
    "Middle East": "#e08844",
    "Asia":        "#d4b445",
    "Africa":      "#7ab648",
    "Americas":    "#4a9fd4",
    "Pacific":     "#7b6fd4",
    "Global":      "#c45abf",
    "Other":       "#8a8a8a",
}

REGION_KEYWORDS = {
    "Europe":      ["europe","european","balkan","greek","greece","yugoslav",
                    "russian","russia","ukrainian","ukrain","polish","poland",
                    "german","germany","french","france","spain","spanish",
                    "italian","italy","british","britain","irish","ireland",
                    "finnish","finland","hungarian","hungary","romanian","romania",
                    "bulgarian","bulgaria","serbian","serbia","croatian","croatia",
                    "bosnian","bosnia","czech","slovak","austria","dutch",
                    "netherlands","belgian","belgium","swedish","norway",
                    "norwegian","danish","denmark","swiss","portugal","portuguese",
                    "albanian","albania","macedon","montenegr","moldov",
                    "baltic","latvian","lithuanian","estonian","chechen",
                    "chechnya","kosovo","crimea","cyprus","troubles"],
    "Middle East": ["arab","iraq","iran","persian","israel","israeli","lebanese",
                    "lebanon","syrian","syria","yemeni","yemen","gulf","ottoman",
                    "turkey","turkish","afghan","afghanistan","kurd","kurdish",
                    "palestinian","palesti","hezbollah","houthi","bahrain",
                    "qatar","saudi","jordan","oman","emirat"],
    "Asia":        ["china","chinese","korean","korea","vietnam","vietnamese",
                    "india","indian","pakistan","burm","myanmar","cambodia",
                    "cambodian","laos","laotian","thailand","thai","indonesia",
                    "indonesian","malay","philippine","filipino","sino",
                    "japan","japanese","tibet","tibetan","taiwan","formosa",
                    "bangladesh","bengal","nepal","sri lank","ceylon",
                    "kashmir","xinjiang","uyghur","khmer","hmong","moro",
                    "boxer rebellion","taiping","sikh","assam","manipur",
                    "naxal","tamil"],
    "Africa":      ["africa","african","ethiopia","ethiopian","somali","somalia",
                    "sudan","sudanese","congo","congolese","angola","angolan",
                    "mozambi","rwanda","rwandan","liberia","liberian",
                    "sierra leone","nigeria","nigerian","egypt","egyptian",
                    "algeri","libya","libyan","kenya","kenyan","zimbabwe",
                    "uganda","ugandan","chad","chadian","mali","malian",
                    "eritrea","eritrean","burundi","cameroon","central african",
                    "ivory coast","ghana","senegal","niger ","namibia",
                    "south africa","morocco","moroccan","tunisia","tunisian",
                    "darfur","sahara","sahel","mau mau","biafra","boko haram",
                    "hutu","tutsi","zulu","boer","rhodesia","madagascar",
                    "mozambique"],
    "Americas":    ["america","american","colombia","colombian","mexico",
                    "mexican","peru","peruvian","bolivia","bolivian","panama",
                    "cuba","cuban","dominican","haiti","haitian",
                    "central america","nicaragu","guatemal","hondur",
                    "el salvador","salvadoran","venezuela","venezuelan",
                    "chile","chilean","argentin","brazil","brazilian",
                    "ecuador","ecuadori","paraguayan","paraguay","uruguay",
                    "falkland","malvinas","farc","contra","zapatist",
                    "canad","puerto ric","jamaica"],
    "Pacific":     ["pacific","papua","samoa","fiji","hawaii","solomon islands",
                    "new zealand","australia","australian","timor","bougainville",
                    "oceani","mariana","midway","guadalcanal","iwo jima",
                    "okinawa"],
    "Global":      ["world war","cold war","global","war on terror"],
}
