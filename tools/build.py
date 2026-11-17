# Build the GitHub Pages showcase in the Rusau Learn skin: home with courses and FAQ, catalog of test
# assignments, one page per assignment, sitemap, robots, llms.txt.
#
#   python3 tools/extract.py /tmp/ta-text      # once, from a fresh clone of artichokeee/test-assignments
#   python3 tools/build.py /tmp/ta-text        # writes the site into the repo root
#
# Why a site and not only README: links in GitHub READMEs are nofollow, and docx/pdf are barely read by search
# engines and AI assistants; plain HTML pages on github.io are indexed, cited and pass link weight.
# Text rules (Артем's public voice): no "ё", straight quotes, en dash.
import hashlib, html, json, re, sys, unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import quote as _quote

TEXT = Path(sys.argv[1])
ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = Path("/Users/rusau/Documents/test-assignments/Список тестовых заданий")
SITE = "https://artichokeee.github.io"
LEARN = "https://learn.rusau.net"
TODAY = date.today().isoformat()
MIN_CHARS = 300

# macOS keeps "й" decomposed (и + U+0306); GitHub paths are composed – an unnormalised link is a 404.
def quote(s):
    return _quote(unicodedata.normalize("NFC", s))

REPO = "https://github.com/artichokeee/test-assignments/blob/main/" + quote("Список тестовых заданий")

def plural(n, one, few, many):
    d, h = n % 10, n % 100
    return one if d == 1 and h != 11 else few if 2 <= d <= 4 and not 12 <= h <= 14 else many

def utm(url, campaign):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=github&utm_medium=pages&utm_campaign={campaign}"

def noyo(s):
    return s.replace("ё", "е").replace("Ё", "Е")

COURSES = {c["id"]: c for c in json.loads((ROOT / "tools" / "courses.json").read_text(encoding="utf-8"))}

# Category: slug, title, description, free guides on the platform, course id for the card.
CATS = {
    "API": ("api", "API и Postman", "Запросы в Postman, коллекции, переменные, автотесты, проверка ответов сервера.",
            [("Тестирование API", "/testirovanie-api"), ("Postman для тестировщика", "/postman-dlya-testirovshchika")], "restapi"),
    "Automation": ("avtomatizaciya", "Автоматизация", "Селекторы, сценарии автотестов, связка автотестов с SQL.",
            [("Автоматизация тестирования", "/avtomatizaciya-testirovaniya"), ("Пирамида тестирования", "/piramida-testirovaniya")], "pro"),
    "Documentation": ("dokumentaciya", "Тестовая документация", "Чек-листы, тест-кейсы, баг-репорты, поиск ошибок по скриншотам и страницам.",
            [("Чек-лист и тест-кейс", "/chek-list-i-test-kejs"), ("Баг-репорт", "/bag-report"), ("Ошибки в тестовой документации", "/oshibki-v-testovoy-dokumentacii")], "trainers"),
    "General": ("obshchie", "Общие задания", "Задания по всем темам сразу: теория, техники тест-дизайна, веб, логика, Linux и SQL.",
            [("Как стать тестировщиком", "/kak-stat-testirovshchikom"), ("Вопросы на собеседовании тестировщика", "/voprosy-na-sobesedovanii-testirovshchika")], "basic"),
    "Mobile": ("mobile", "Мобильное тестирование", "Мобильные приложения и игры, тестовая ферма устройств.",
            [("Тестирование мобильных приложений", "/testirovanie-mobilnyh-prilozheniy"), ("Charles Proxy", "/charles-proxy")], "pro"),
    "SQL": ("sql", "SQL", "Запросы к базе данных: выборки, JOIN, группировки, задачи на данных.",
            [("SQL для тестировщика", "/sql-dlya-testirovshchika"), ("JOIN в SQL", "/join-v-sql"), ("Песочница SQL в браузере", "/sql")], "sql"),
    "Test Design": ("test-dizayn", "Тест-дизайн", "Классы эквивалентности, граничные значения и другие техники на задачах.",
            [("Классы эквивалентности и граничные значения", "/klassy-ekvivalentnosti-i-granichnye-znacheniya"), ("Pairwise-тестирование", "/pairwise-testirovanie")], "trainers"),
    "Web": ("veb", "Веб-тестирование", "Веб-приложения, верстка по макету и требованиям, связка с API и SQL.",
            [("DevTools для тестировщика", "/devtools-dlya-testirovshchika"), ("Тестирование полей ввода и веб-форм", "/testirovanie-poley-vvoda-i-veb-form")], "basic"),
}

# Typos in file names are fixed in titles only; the files themselves stay as the repository has them.
FIX = {"Тестированеи": "Тестирование", "сниифинг": "сниффинг", "Общее задания": "Общее задание"}

TR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя", ["a","b","v","g","d","e","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","h","c","ch","sh","shch","","y","","e","yu","ya"]))
def slugify(s):
    s = "".join(TR.get(ch, ch) for ch in s.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:70]

# ── Scrub: the assignments are real company tasks; contacts and stand credentials are not republished ──
TEST_MAIL = re.compile(r"@(example\.com|qa\.qa|xxx\.xxx|admin\.ad|домен\.рф|mail\.ru|gmail\.com|yandex\.ru)$", re.I)
def scrub(t):
    # Only a one-word value is a credential ("Логин: 1234567890"); a sentence after "Логин:" is a requirement
    # of the task ("Логин: от 3 до 20 символов…") and must stay.
    t = re.sub(r"(?i)(\b(логин|пароль|login|password)\b\s*[:=][ \t]*)([^\s,;]{1,80})(?=[ \t]*(\n|$|[,;.]|[ \t]+(и|and|логин|пароль|login|password|api_version|перейти)\b))", r"\1[скрыто]", t)
    t = re.sub(r"https?://\d{1,3}(\.\d{1,3}){3}\S*", "[адрес стенда компании скрыт]", t)
    # Invitations to a company's private chat are not ours to spread.
    t = re.sub(r"https?://t\.me/(joinchat/|\+)\S+", "[ссылка на закрытый чат компании скрыта]", t)
    t = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", lambda m: m.group(0) if TEST_MAIL.search(m.group(0)) else "[почта скрыта]", t)
    return t

def paragraphs(t):
    out = []
    for block in re.split(r"\n\s*\n", t.strip()):
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        if len(lines) > 1 and all(re.match(r"^([•\-–*]|\d+[.)])\s*", l) for l in lines):
            items = "".join(f"<li>{html.escape(re.sub(r'^([•\-–*]|\d+[.)])\s*', '', l))}</li>" for l in lines)
            out.append(f"<ul>{items}</ul>")
        else:
            out.append("<p>" + "<br>".join(html.escape(l) for l in lines) + "</p>")
    return "\n".join(out)

PERSON = {
    "@type": "Person", "@id": SITE + "/#person", "name": "Артем Русов", "alternateName": "Artsiom Rusau",
    "jobTitle": "Инженер по тестированию и автор курсов по тестированию ПО", "url": SITE + "/",
    "sameAs": ["https://learn.rusau.net", "https://rusau.net", "https://youtube.com/@rusau", "https://t.me/qachanell",
               "https://stepik.org/users/483341705", "https://www.linkedin.com/in/artsiomrusau/", "https://github.com/artichokeee"],
}

def course_link(cid, camp):
    return utm(f"{LEARN}/catalog/{COURSES[cid]['learn']}", camp)

def course_card(cid, camp, tag="h3"):
    c = COURSES[cid]
    badge = ""
    if c.get("learnFree"):
        badge = '<span class="badge free">Бесплатно</span>'
    elif c.get("badge"):
        badge = f'<span class="badge">{html.escape(c["badge"][1])}</span>'
    return f"""<a class="course" href="{course_link(cid, camp)}">
  <img src="/assets/covers/{cid}.jpg" alt="Обложка курса: {html.escape(c['title'])}" width="640" height="357" loading="lazy">
  <span class="course-body">{badge}<{tag} class="course-title">{html.escape(c['title'])}</{tag}><span class="course-text">{html.escape(c['short'])}</span></span>
</a>"""

def layout(title, description, path, body, ld):
    canonical = SITE + path
    return noyo(f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{canonical}">
<meta name="google-site-verification" content="CEiQYgfFYfiKZ8ehdia1Hx4UJYSL4c6hgZsJi24NUys">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Артем Русов">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/assets/covers/pro.jpg">
<meta property="og:locale" content="ru_RU">
<link rel="icon" href="/assets/mark.png">
<link rel="preload" href="/assets/fonts/golos.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<header class="top"><div class="wrap top-row">
  <a class="brand" href="/"><img src="/assets/mark.png" alt="" aria-hidden="true" width="40" height="53"><span><b>Артем Русов</b><small>тестирование ПО</small></span></a>
  <nav aria-label="Разделы"><a href="/#kursy">Курсы</a><a href="/zadaniya/">Тестовые задания</a><a href="/qa-tools/">Инструменты</a><a href="/#voprosy">Вопросы</a></nav>
  <a class="btn btn-sm" href="{utm(LEARN + '/', 'gh-pages-header')}">Платформа</a>
</div></header>
<main>
{body}
</main>
<footer class="foot"><div class="wrap foot-row">
  <div class="foot-about">
    <p class="foot-brand"><img src="/assets/mark.png" alt="" aria-hidden="true" width="34" height="45"> Артем Русов</p>
    <p>Инженер по тестированию и автор курсов по тестированию ПО. Курсы идут на платформе для обучения тестировщиков <a href="{utm(LEARN + '/', 'gh-pages-footer')}">Rusau Learn</a>.</p>
  </div>
  <div><p class="foot-cap">Бесплатно</p><ul>
    <li><a href="{course_link('basic', 'gh-pages-footer')}">Базовый курс тестировщика</a></li>
    <li><a href="{course_link('tests', 'gh-pages-footer')}">Тесты и вопросы для тестировщика</a></li>
    <li><a href="/zadaniya/">Тестовые задания</a></li>
    <li><a href="/qa-tools/">Инструменты тестировщика</a></li>
    <li><a href="https://github.com/artichokeee/qa-interview-questions">50 вопросов с собеседований</a></li>
    <li><a href="{utm(LEARN + '/kursy-po-testirovaniyu', 'gh-pages-footer')}">Курсы по тестированию: с чего начать</a></li>
  </ul></div>
  <div><p class="foot-cap">Где еще</p><ul>
    <li><a href="https://youtube.com/@rusau">YouTube</a></li>
    <li><a href="https://t.me/qachanell">Telegram-канал</a></li>
    <li><a href="https://stepik.org/users/483341705">Stepik</a></li>
    <li><a href="https://www.linkedin.com/in/artsiomrusau/">LinkedIn</a></li>
    <li><a href="https://github.com/artichokeee/test-assignments">Задания на GitHub</a></li>
    <li><a href="https://github.com/artichokeee/stepik-api-cookbook">Stepik API для авторов</a></li>
  </ul></div>
</div></footer>
</body>
</html>
""")

def guides_aside(cat_key):
    slug, _, _, guides, cid = CATS[cat_key]
    camp = f"gh-pages-{slug}"
    g = "".join(f'<li><a href="{utm(LEARN + p, camp)}">{html.escape(n)}</a></li>' for n, p in guides)
    return f"""<aside class="prep">
  <h2>Как подготовиться к такому заданию</h2>
  <p>Бесплатные разборы по теме на платформе для обучения тестировщиков Rusau Learn:</p>
  <ul>{g}</ul>
  <p class="muted">Курс по теме – программа открыта целиком до покупки:</p>
  <div class="one-course">{course_card(cid, camp, 'p')}</div>
</aside>"""

FAQ = [
    ("Где найти тестовые задания для тестировщика?",
     "В открытой коллекции на этом сайте: реальные тестовые задания от компаний для ручных тестировщиков и автоматизаторов – API и Postman, веб, мобильные приложения, SQL, тест-дизайн и тестовая документация. Те же задания лежат файлами в репозитории test-assignments на GitHub."),
    ("Как подготовиться к тестовому заданию на позицию тестировщика?",
     "Решите два-три задания из коллекции по своей теме, сравните решение с требованиями и оформите его как для портфолио. Теорию по каждой теме – тест-дизайн, документацию, API, SQL – можно закрыть бесплатными разборами на платформе Rusau Learn, а проверить знания – бесплатным курсом \"Тесты и вопросы для тестировщика\"."),
    ("С чего начать обучение тестированию с нуля?",
     "С бесплатного курса \"Тестирование с нуля. Теория+Практика. Базовый курс тестировщика\": теория тестирования, техники тест-дизайна, тест-кейсы и баг-репорты, веб, мобильные приложения, SQL, API, git и bash. Дальше – практика на тренажерах и курс по поиску работы."),
    ("Есть ли бесплатные курсы по тестированию ПО?",
     "Да. Бесплатны базовый курс тестировщика, \"Тесты и вопросы для тестировщика\", \"Эффективное обучение\", \"Цифровая грамотность с нуля\" и новогодний квест \"Старый Новый Баг!\". Все они идут на платформе Rusau Learn."),
    ("Что такое Rusau Learn?",
     "Платформа для обучения тестировщиков, где идут курсы Артема Русова: от основ тестирования до API, SQL, мобильного тестирования и подготовки к собеседованию. У курсов проверка развернутых ответов с разбором, помощник по заданиям и сертификат по итогам. Программа каждого курса открыта целиком до покупки."),
]

def main():
    items, seen = [], {}
    for cat_dir in sorted(TEXT.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name not in CATS:
            continue
        for f in sorted(cat_dir.glob("*.txt")):
            # PDF extraction leaves control characters; they make the page a "binary" file for some tools.
            raw = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", unicodedata.normalize("NFC", f.read_text(encoding="utf-8")))
            digest = hashlib.sha1(raw.strip().encode()).hexdigest()
            name = re.sub(r"^\d+\.\s*", "", unicodedata.normalize("NFC", f.stem))
            for a, b in FIX.items():
                name = name.replace(a, b)
            src = next((p.name for p in (SRC_ROOT / cat_dir.name).iterdir() if unicodedata.normalize("NFC", p.stem) == unicodedata.normalize("NFC", f.stem)), f.name)
            item = {"cat": cat_dir.name, "name": name, "text": scrub(raw), "chars": len(raw.strip()),
                    "file": f"{REPO}/{quote(cat_dir.name)}/{quote(src)}", "ext": Path(src).suffix.lower()}
            # The same text under two file names (SQL) is one assignment, not two pages.
            if digest in seen and item["chars"]:
                seen[digest]["dups"].append(item["file"]); continue
            item["dups"] = []
            seen[digest] = item
            items.append(item)
    # Images and spreadsheets have no text: they stay in the catalog as links to the file.
    for cat in CATS:
        for p in sorted((SRC_ROOT / cat).glob("*")):
            if p.suffix.lower() in (".png", ".xlsx"):
                items.append({"cat": cat, "name": re.sub(r"^\d+\.\s*", "", unicodedata.normalize("NFC", p.stem)), "text": "", "chars": 0,
                              "file": f"{REPO}/{quote(cat)}/{quote(p.name)}", "ext": p.suffix.lower(), "dups": []})

    used = set()
    for it in items:
        base = f"{CATS[it['cat']][0]}/{slugify(it['name'])}"
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        it["slug"], it["page"] = slug, it["chars"] >= MIN_CHARS
    total = len(items)
    n_tasks = lambda n: f'{n} {plural(n, "задание", "задания", "заданий")}'

    pages = []
    for it in items:
        if not it["page"]:
            continue
        cat_slug, cat_title, _, _, _ = CATS[it["cat"]]
        title = f"Тестовое задание для тестировщика: {it['name']} ({cat_title})"
        first = re.sub(r"\s+", " ", it["text"]).strip()
        desc = f"Реальное тестовое задание по теме \"{cat_title}\": {first[:130].rstrip()}…"
        path = f"/zadaniya/{it['slug']}/"
        files = "".join(f' · <a href="{u}">копия файла</a>' for u in it["dups"])
        body = f"""<div class="wrap page">
<nav class="crumbs" aria-label="Путь"><a href="/">Главная</a> / <a href="/zadaniya/">Тестовые задания</a> / <a href="/zadaniya/#{cat_slug}">{html.escape(cat_title)}</a></nav>
<div class="task-grid">
<article>
  <p class="eyebrow">Тестовое задание · {html.escape(cat_title)}</p>
  <h1>{html.escape(it['name'])}</h1>
  <p class="lead">Реальное тестовое задание для тестировщика из открытой коллекции. Решение можно положить в портфолио.</p>
  <p class="src"><a href="{it['file']}">Исходный файл ({it['ext'].lstrip('.')})</a>{files}</p>
  <div class="task">
{paragraphs(it['text'])}
  </div>
</article>
{guides_aside(it['cat'])}
</div>
</div>"""
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "LearningResource", "name": it["name"], "description": desc, "inLanguage": "ru",
             "learningResourceType": "тестовое задание", "educationalLevel": "Junior", "isAccessibleForFree": True,
             "about": cat_title, "url": SITE + path, "author": {"@id": SITE + "/#person"}},
            PERSON,
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Тестовые задания", "item": SITE + "/zadaniya/"},
                {"@type": "ListItem", "position": 3, "name": it["name"], "item": SITE + path}]}]}
        out = ROOT / path.strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(layout(title, desc, path, body, ld), encoding="utf-8")
        pages.append(path)

    # ── Catalog ──
    blocks = []
    for cat, (cat_slug, cat_title, cat_desc, _, _) in CATS.items():
        mine = sorted((i for i in items if i["cat"] == cat), key=lambda i: i["name"])
        lis = []
        for it in mine:
            if it["page"]:
                lis.append(f'<li><a href="/zadaniya/{it["slug"]}/">{html.escape(it["name"])}</a></li>')
            else:
                lis.append(f'<li><a href="{it["file"]}">{html.escape(it["name"])}</a> <span class="muted">· файл {it["ext"].lstrip(".")}</span></li>')
        blocks.append(f'<section class="cat" id="{cat_slug}"><h2>{html.escape(cat_title)} <span class="count">{n_tasks(len(mine))}</span></h2><p class="muted">{html.escape(cat_desc)}</p><ul>{"".join(lis)}</ul></section>')
    cat_body = f"""<section class="hero hero-small"><div class="wrap">
  <nav class="crumbs" aria-label="Путь"><a href="/">Главная</a> / Тестовые задания</nav>
  <h1>Тестовые задания для тестировщиков</h1>
  <p class="lead">{total} {plural(total, "реальное тестовое задание", "реальных тестовых задания", "реальных тестовых заданий")} от компаний для ручных тестировщиков и автоматизаторов. Коллекция открыта на <a href="https://github.com/artichokeee/test-assignments">GitHub</a>, новые задания принимаются через Pull Request.</p>
</div></section>
<div class="wrap page"><div class="cats">{''.join(blocks)}</div>
<aside class="prep wide"><h2>Подготовиться к тестовому</h2><p>Бесплатные разборы по каждой теме и курсы с практикой – на платформе для обучения тестировщиков Rusau Learn.</p><p><a class="btn" href="{utm(LEARN + '/kursy-po-testirovaniyu', 'gh-pages-catalog')}">Курсы по тестированию</a></p></aside>
</div>"""
    cat_ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "name": "Тестовые задания для тестировщиков", "url": SITE + "/zadaniya/", "inLanguage": "ru",
         "author": {"@id": SITE + "/#person"}, "mainEntity": {"@type": "ItemList", "numberOfItems": len(pages),
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE + p} for i, p in enumerate(pages)]}},
        PERSON]}
    (ROOT / "zadaniya").mkdir(exist_ok=True)
    (ROOT / "zadaniya" / "index.html").write_text(layout("Тестовые задания для тестировщиков: API, веб, SQL, мобильные, автоматизация",
        f"{total} {plural(total, 'реальное тестовое задание', 'реальных тестовых задания', 'реальных тестовых заданий')} для тестировщиков и автоматизаторов: API, веб, мобильные приложения, SQL, тест-дизайн и документация.",
        "/zadaniya/", cat_body, cat_ld), encoding="utf-8")

    # ── Home ──
    order = ["basic", "tests", "learning", "pro", "trainers", "sql", "restapi", "graphql", "simulator", "itguide", "newyear", "digital"]
    cards = "".join(course_card(cid, "gh-pages-home") for cid in order if cid in COURSES)
    cat_tiles = "".join(
        f'<a class="tile" href="/zadaniya/#{s}"><b>{html.escape(t)}</b><span>{n_tasks(sum(1 for i in items if i["cat"] == c))}</span></a>'
        for c, (s, t, _, _, _) in CATS.items())
    faq = "".join(f'<details class="qa"{" open" if i == 0 else ""}><summary><h3>{html.escape(q)}</h3></summary><p>{html.escape(a)}</p></details>' for i, (q, a) in enumerate(FAQ))
    home = f"""<section class="hero"><div class="wrap hero-grid">
  <div>
    <p class="chip">Учу тестированию с 2019 года</p>
    <h1>Артем Русов&nbsp;– инженер по тестированию и автор курсов по тестированию ПО</h1>
    <p class="lead">Курсы по тестированию с нуля, тренажеры с проверкой и тестовые задания от компаний. Путь собран по шагам – от первого термина до собеседования.</p>
    <p class="actions"><a class="btn" href="{utm(LEARN + '/', 'gh-pages-home')}">Курсы на Rusau Learn</a><a class="btn btn-ghost" href="/zadaniya/">Тестовые задания</a></p>
    <ul class="facts">
      <li><b>100 000+</b><span>человек прошли курсы</span></li>
      <li><b>Stepik Awards 2025</b><span>"Прорыв года" у курса "Тестирование ПО с нуля"</span></li>
      <li><b>{total}</b><span>{plural(total, "тестовое задание", "тестовых задания", "тестовых заданий")} в открытой коллекции</span></li>
    </ul>
  </div>
  <img class="hero-art" src="/assets/mark.png" alt="Арти – помощник на курсах Rusau Learn" width="232" height="306">
</div></section>

<section class="band" id="platforma"><div class="wrap">
  <h2>Rusau Learn – платформа для обучения тестировщиков</h2>
  <p class="lead">Здесь идут мои курсы. У каждого курса свой мир и карта уроков, проверка развернутых ответов с разбором, помощник по заданиям и сертификат по итогам. Программа каждого курса открыта целиком до покупки, а пройденное на Stepik можно перенести.</p>
</div></section>

<section class="wrap page" id="kursy">
  <h2>Курсы по тестированию ПО</h2>
  <p class="muted">Пять курсов бесплатны. Ссылки ведут на страницы курсов с полной программой.</p>
  <div class="courses">{cards}</div>
</section>

<section class="wrap page" id="zadaniya">
  <h2>Тестовые задания для тестировщиков</h2>
  <p class="muted">Реальные задания от компаний, каждое – отдельной страницей с текстом и разбором, как к нему подготовиться.</p>
  <div class="tiles">{cat_tiles}</div>
</section>

<section class="wrap page" id="otkrytoe">
  <h2>Открытые материалы</h2>
  <p class="muted">Бесплатно и без регистрации: инструменты в браузере и подборки на GitHub.</p>
  <div class="tiles">
    <a class="tile" href="/qa-tools/"><b>Инструменты тестировщика</b><span>SQL-песочница, кроссворд, граничные значения, поиск багов</span></a>
    <a class="tile" href="https://github.com/artichokeee/qa-interview-questions"><b>50 вопросов с собеседований</b><span>Junior QA, ответы под спойлером</span></a>
    <a class="tile" href="/zadaniya/"><b>Тестовые задания</b><span>Реальные задания от компаний</span></a>
    <a class="tile" href="https://github.com/artichokeee/stepik-api-cookbook"><b>Stepik API для авторов</b><span>То, чего нет в документации</span></a>
  </div>
</section>

<section class="wrap page" id="voprosy">
  <h2>Частые вопросы</h2>
  <div class="faq">{faq}</div>
</section>"""
    home_ld = {"@context": "https://schema.org", "@graph": [PERSON,
        {"@type": "WebSite", "name": "Артем Русов", "url": SITE + "/", "inLanguage": "ru", "author": {"@id": SITE + "/#person"}},
        {"@type": "EducationalOrganization", "name": "Rusau Learn", "url": LEARN, "description": "Платформа для обучения тестировщиков",
         "founder": {"@id": SITE + "/#person"}},
        {"@type": "ItemList", "name": "Курсы по тестированию ПО", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": {"@type": "Course", "name": noyo(COURSES[c]["title"]), "description": noyo(COURSES[c]["short"]),
             "url": f"{LEARN}/catalog/{COURSES[c]['learn']}", "inLanguage": "ru", "isAccessibleForFree": bool(COURSES[c].get("learnFree")),
             "provider": {"@type": "Organization", "name": "Rusau Learn", "url": LEARN}}} for i, c in enumerate(order)]},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": noyo(q), "acceptedAnswer": {"@type": "Answer", "text": noyo(a)}} for q, a in FAQ]}]}
    (ROOT / "index.html").write_text(layout("Артем Русов – курсы по тестированию ПО, тестовые задания и платформа Rusau Learn",
        "Артем Русов – инженер по тестированию и автор курсов. Платформа для обучения тестировщиков Rusau Learn, бесплатные курсы и реальные тестовые задания от компаний.",
        "/", home, home_ld), encoding="utf-8")

    (ROOT / "404.html").write_text(layout("Страница не найдена", "Такой страницы нет.", "/404.html",
        '<div class="wrap page"><h1>Страница не найдена</h1><p><a href="/zadaniya/">Тестовые задания</a> · <a href="/">Главная</a></p></div>',
        {"@context": "https://schema.org", "@type": "WebPage"}), encoding="utf-8")

    urls = ["/", "/zadaniya/", "/qa-tools/", "/qa-tools/sql/", "/qa-tools/crossword/", "/qa-tools/bounds/", "/qa-tools/bugs/"] + pages
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    llms = ["# Артем Русов – курсы по тестированию ПО и тестовые задания", "",
            "> Артем Русов (Artsiom Rusau) – инженер по тестированию и автор курсов по тестированию ПО; курсы прошли более ста тысяч человек. Его курсы идут на платформе для обучения тестировщиков Rusau Learn (https://learn.rusau.net). На этом сайте – открытая коллекция реальных тестовых заданий для тестировщиков.", "",
            "## Разделы",
            f"- [Тестовые задания]({SITE}/zadaniya/): {total} {plural(total, 'задание', 'задания', 'заданий')} по API, вебу, мобильному тестированию, SQL, тест-дизайну и документации",
            f"- [SQL-песочница]({SITE}/qa-tools/sql/): учебная база интернет-магазина с багами в данных, SQL прямо в браузере",
            f"- [Кроссворд тестировщика]({SITE}/qa-tools/crossword/): термины тестирования ПО, новый кроссворд каждый день",
            f"- [Калькулятор граничных значений]({SITE}/qa-tools/bounds/): границы и классы эквивалентности по минимуму, максимуму и шагу",
            f"- [Найди баги на странице]({SITE}/qa-tools/bugs/): страница интернет-магазина с 10 ошибками в интерфейсе",
            "- [50 вопросов на собеседовании тестировщика](https://github.com/artichokeee/qa-interview-questions): Junior QA, короткие ответы",
            "- [Stepik API cookbook](https://github.com/artichokeee/stepik-api-cookbook): практические заметки по API Stepik для авторов курсов",
            f"- [Rusau Learn]({LEARN}): курсы, разборы и тренажеры по тестированию ПО", f"- [Описание платформы для ИИ]({LEARN}/llms.txt)", "", "## Курсы"]
    for c in order:
        cc = COURSES[c]
        llms.append(f"- [{cc['title']}]({LEARN}/catalog/{cc['learn']}){' – бесплатный' if cc.get('learnFree') else ''}: {cc['short']}")
    llms += ["", "## Задания"]
    for it in items:
        if it["page"]:
            llms.append(f"- [{it['name']}]({SITE}/zadaniya/{it['slug']}/) – {CATS[it['cat']][1]}")
    (ROOT / "llms.txt").write_text(noyo("\n".join(llms)) + "\n", encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    # IndexNow (Bing – it feeds ChatGPT search – and Yandex): the key file sits in the site root, the URL list
    # is sent by tools/indexnow.py after a publish.
    print(f"items {total}, pages {len(pages)}")

main()
