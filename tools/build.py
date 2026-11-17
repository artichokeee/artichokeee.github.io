# Build the GitHub Pages showcase: home, catalog of test assignments, one page per assignment,
# sitemap, robots, llms.txt. Text comes from tools/extract.py (doc/docx/pdf/txt of artichokeee/test-assignments).
#
#   python3 tools/extract.py /tmp/ta-text      # once, from a fresh clone of test-assignments
#   python3 tools/build.py /tmp/ta-text        # writes the site into the repo root
#
# Why a site and not only README: links in GitHub READMEs are nofollow and docx/pdf are barely read by search
# engines and AI assistants; plain HTML pages on github.io are indexed and cited.
import hashlib, html, json, re, sys, unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import quote as _quote

# macOS keeps "й" decomposed (и + U+0306); GitHub paths are composed – an unnormalised link is a 404.
def quote(s):
    return _quote(unicodedata.normalize("NFC", s))

TEXT = Path(sys.argv[1])
ROOT = Path(__file__).resolve().parent.parent
SITE = "https://artichokeee.github.io"
LEARN = "https://learn.rusau.net"
REPO = "https://github.com/artichokeee/test-assignments/blob/main/" + quote("Список тестовых заданий")
TODAY = date.today().isoformat()
MIN_CHARS = 300

def plural(n, one, few, many):
    d, h = n % 10, n % 100
    return one if d == 1 and h != 11 else few if 2 <= d <= 4 and not 12 <= h <= 14 else many

def utm(url, campaign):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=github&utm_medium=pages&utm_campaign={campaign}"

CATS = {
    "API": ("api", "API и Postman", "Задания на тестирование API: запросы в Postman, коллекции, переменные, автотесты, проверка ответов сервера.",
            [("Тестирование API", "/testirovanie-api"), ("Postman для тестировщика", "/postman-dlya-testirovshchika")],
            ("Тестирование API в Postman с нуля: REST API, Swagger, Греция", "/catalog/rest-api-postman-greciya")),
    "Automation": ("avtomatizaciya", "Автоматизация", "Задания для автоматизаторов: селекторы, сценарии автотестов, связка с SQL.",
            [("Автоматизация тестирования", "/avtomatizaciya-testirovaniya"), ("Пирамида тестирования", "/piramida-testirovaniya")],
            ("Тестирование ПО с нуля. Продвинутый курс тестировщика с ИИ", "/catalog/testirovanie-po-prodvinutyy")),
    "Documentation": ("dokumentaciya", "Тестовая документация", "Чек-листы, тест-кейсы, баг-репорты и поиск ошибок по скриншотам и страницам.",
            [("Чек-лист и тест-кейс", "/chek-list-i-test-kejs"), ("Баг-репорт", "/bag-report"), ("Ошибки в тестовой документации", "/oshibki-v-testovoy-dokumentacii")],
            ("Тестирование ПО. Тренажеры для тестировщика с ИИ", "/catalog/prakticheskie-trenazhery")),
    "General": ("obshchie", "Общие задания", "Задания по всем темам сразу: теория, техники тест-дизайна, веб, логика, Linux и SQL.",
            [("Как стать тестировщиком", "/kak-stat-testirovshchikom"), ("Вопросы на собеседовании тестировщика", "/voprosy-na-sobesedovanii-testirovshchika")],
            ("Тестирование с нуля. Теория+Практика. Базовый курс тестировщика (бесплатный)", "/catalog/testirovanie-po-bazovyy")),
    "Mobile": ("mobile", "Мобильное тестирование", "Тестирование мобильных приложений и игр, тестовая ферма устройств.",
            [("Тестирование мобильных приложений", "/testirovanie-mobilnyh-prilozheniy"), ("Charles Proxy", "/charles-proxy")],
            ("Тестирование ПО с нуля. Продвинутый курс тестировщика с ИИ", "/catalog/testirovanie-po-prodvinutyy")),
    "SQL": ("sql", "SQL", "Запросы к базе данных: выборки, JOIN, группировки и задачи на данных.",
            [("SQL для тестировщика", "/sql-dlya-testirovshchika"), ("JOIN в SQL", "/join-v-sql"), ("Песочница SQL в браузере", "/sql")],
            ("Рабочий день тестировщика: тренажер по SQL и задачи на практике", "/catalog/sql-rabochiy-den")),
    "Test Design": ("test-dizayn", "Тест-дизайн", "Классы эквивалентности, граничные значения и другие техники тест-дизайна на задачах.",
            [("Классы эквивалентности и граничные значения", "/klassy-ekvivalentnosti-i-granichnye-znacheniya"), ("Pairwise-тестирование", "/pairwise-testirovanie")],
            ("Тестирование ПО. Тренажеры для тестировщика с ИИ", "/catalog/prakticheskie-trenazhery")),
    "Web": ("veb", "Веб-тестирование", "Тестирование веб-приложений, верстки по макету и требованиям, связка с API и SQL.",
            [("DevTools для тестировщика", "/devtools-dlya-testirovshchika"), ("Тестирование полей ввода и веб-форм", "/testirovanie-poley-vvoda-i-veb-form")],
            ("Тестирование с нуля. Теория+Практика. Базовый курс тестировщика (бесплатный)", "/catalog/testirovanie-po-bazovyy")),
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
    t = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", lambda m: m.group(0) if TEST_MAIL.search(m.group(0)) else "[почта скрыта]", t)
    return t

def paragraphs(t):
    out = []
    for block in re.split(r"\n\s*\n", t.strip()):
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        if all(re.match(r"^([•\-–*]|\d+[.)])\s*", l) for l in lines) and len(lines) > 1:
            items = "".join(f"<li>{html.escape(re.sub(r'^([•\-–*]|\d+[.)])\s*', '', l))}</li>" for l in lines)
            out.append(f"<ul>{items}</ul>")
        else:
            out.append("<p>" + "<br>".join(html.escape(l) for l in lines) + "</p>")
    return "\n".join(out)

PERSON = {
    "@type": "Person", "name": "Артем Русов", "alternateName": "Artsiom Rusau",
    "jobTitle": "Инженер по тестированию и автор курсов по тестированию ПО",
    "url": SITE + "/",
    "sameAs": ["https://learn.rusau.net", "https://rusau.net", "https://youtube.com/@rusau", "https://t.me/qachanell",
               "https://stepik.org/users/483341705", "https://www.linkedin.com/in/artsiomrusau/", "https://github.com/artichokeee"],
}

def layout(title, description, path, body, ld):
    canonical = SITE + path
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="ru_RU">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="/">Артем Русов</a>
  <nav aria-label="Разделы"><a href="/zadaniya/">Тестовые задания</a><a href="{utm(LEARN, 'gh-pages-nav')}">Rusau Learn</a></nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="wrap foot">
  <p>Артем Русов – инженер по тестированию и автор курсов. Платформа для обучения тестировщиков <a href="{utm(LEARN, 'gh-pages-footer')}">Rusau Learn</a> · <a href="https://youtube.com/@rusau">YouTube</a> · <a href="https://t.me/qachanell">Telegram</a> · <a href="https://github.com/artichokeee/test-assignments">тестовые задания на GitHub</a></p>
</footer>
</body>
</html>
"""

def cta(cat_key):
    _, _, _, guides, course = CATS[cat_key]
    camp = f"gh-pages-{CATS[cat_key][0]}"
    g = "".join(f'<li><a href="{utm(LEARN + p, camp)}">{html.escape(n)}</a></li>' for n, p in guides)
    return f"""<aside class="cta">
  <h2>Как подготовиться</h2>
  <p>Разборы по теме этого задания – бесплатно, на платформе для обучения тестировщиков Rusau Learn:</p>
  <ul>{g}</ul>
  <p>Курс по теме: <a href="{utm(LEARN + course[1], camp)}">{html.escape(course[0])}</a>. Программа курса открыта целиком до покупки.</p>
</aside>"""

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
            src_files = [p for p in (Path("/Users/rusau/Documents/test-assignments/Список тестовых заданий") / cat_dir.name).iterdir() if p.stem == f.stem]
            src = src_files[0].name if src_files else f.name
            item = {"cat": cat_dir.name, "name": name, "text": scrub(raw), "chars": len(raw.strip()),
                    "file": f"{REPO}/{quote(cat_dir.name)}/{quote(src)}", "ext": Path(src).suffix.lower()}
            # The same text under two file names (SQL) is one assignment, not two pages.
            if digest in seen and item["chars"]:
                seen[digest]["dups"].append(item["file"]); continue
            item["dups"] = []
            seen[digest] = item
            items.append(item)
    # Images and spreadsheets have no text: they stay in the catalog as links to the file.
    src_root = Path("/Users/rusau/Documents/test-assignments/Список тестовых заданий")
    for cat in CATS:
        for p in sorted((src_root / cat).glob("*")):
            if p.suffix.lower() in (".png", ".xlsx"):
                items.append({"cat": cat, "name": re.sub(r"^\d+\.\s*", "", p.stem), "text": "", "chars": 0,
                              "file": f"{REPO}/{quote(cat)}/{quote(p.name)}", "ext": p.suffix.lower(), "dups": []})

    used = set()
    for it in items:
        base = f"{CATS[it['cat']][0]}/{slugify(it['name'])}"
        slug, n = base, 2
        while slug in used:
            slug, n = f"{base}-{n}", n + 1
        used.add(slug)
        it["slug"] = slug
        it["page"] = it["chars"] >= MIN_CHARS

    pages = []
    for it in items:
        if not it["page"]:
            continue
        cat_slug, cat_title, _, _, _ = CATS[it["cat"]]
        title = f"Тестовое задание для тестировщика: {it['name']} ({cat_title})"
        first = re.sub(r"\s+", " ", it["text"]).strip()
        desc = f"Реальное тестовое задание по теме \"{cat_title}\": {first[:130].rstrip()}…"
        path = f"/zadaniya/{it['slug']}/"
        files = "".join(f'<li><a href="{u}">ещё одна копия файла</a></li>' for u in it["dups"])
        body = f"""<nav class="crumbs" aria-label="Путь"><a href="/">Главная</a> / <a href="/zadaniya/">Тестовые задания</a> / <a href="/zadaniya/#{cat_slug}">{html.escape(cat_title)}</a></nav>
<article>
  <h1>{html.escape(it['name'])}</h1>
  <p class="lead">Тестовое задание для тестировщика из открытой коллекции на GitHub. Тема: {html.escape(cat_title)}. Решение можно положить в портфолио.</p>
  <p class="src"><a href="{it['file']}">Исходный файл задания ({it['ext'].lstrip('.')})</a></p>
  {f'<ul class="src">{files}</ul>' if files else ''}
  <div class="task">
{paragraphs(it['text'])}
  </div>
</article>
{cta(it['cat'])}"""
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "LearningResource", "name": it["name"], "description": desc, "inLanguage": "ru",
             "learningResourceType": "тестовое задание", "educationalLevel": "Junior", "isAccessibleForFree": True,
             "about": cat_title, "url": SITE + path, "author": PERSON},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Главная", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Тестовые задания", "item": SITE + "/zadaniya/"},
                {"@type": "ListItem", "position": 3, "name": it["name"], "item": SITE + path}]}]}
        out = ROOT / path.strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(layout(title, desc, path, body, ld), encoding="utf-8")
        pages.append(path)

    # Catalog
    blocks = []
    for cat, (cat_slug, cat_title, cat_desc, _, _) in CATS.items():
        lis = []
        for it in sorted((i for i in items if i["cat"] == cat), key=lambda i: i["name"]):
            if it["page"]:
                lis.append(f'<li><a href="/zadaniya/{it["slug"]}/">{html.escape(it["name"])}</a></li>')
            else:
                lis.append(f'<li><a href="{it["file"]}">{html.escape(it["name"])}</a> <span class="muted">– файл {it["ext"].lstrip(".")}</span></li>')
        blocks.append(f'<section id="{cat_slug}"><h2>{html.escape(cat_title)}</h2><p class="muted">{html.escape(cat_desc)}</p><ul>{"".join(lis)}</ul></section>')
    total = len(items)
    cat_body = f"""<h1>Тестовые задания для тестировщиков</h1>
<p class="lead">{total} {plural(total, "реальное тестовое задание", "реальных тестовых задания", "реальных тестовых заданий")} от компаний для ручных тестировщиков и автоматизаторов: API и Postman, веб, мобильные приложения, SQL, тест-дизайн, тестовая документация. Коллекция открыта на <a href="https://github.com/artichokeee/test-assignments">GitHub</a>, новые задания принимаются через Pull Request.</p>
<p>Решенное задание можно положить в портфолио. Подготовиться к тестовому помогут бесплатные разборы и курсы на платформе для обучения тестировщиков <a href="{utm(LEARN, 'gh-pages-catalog')}">Rusau Learn</a>.</p>
<div class="cats">{''.join(blocks)}</div>"""
    cat_ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Тестовые задания для тестировщиков",
              "url": SITE + "/zadaniya/", "inLanguage": "ru", "author": PERSON, "numberOfItems": total}
    (ROOT / "zadaniya").mkdir(exist_ok=True)
    (ROOT / "zadaniya" / "index.html").write_text(layout("Тестовые задания для тестировщиков: API, веб, SQL, мобильные, автоматизация",
        f"{total} {plural(total, 'реальное тестовое задание', 'реальных тестовых задания', 'реальных тестовых заданий')} для тестировщиков и автоматизаторов: API, веб, мобильные приложения, SQL, тест-дизайн и документация.",
        "/zadaniya/", cat_body, cat_ld), encoding="utf-8")

    # Home
    home = f"""<h1>Артем Русов&nbsp;– инженер по тестированию и автор курсов по тестированию ПО</h1>
<p class="lead">Учу тестированию ПО с нуля: курсы прошли более ста тысяч человек. Курс "Тестирование ПО с нуля" – победитель Stepik Awards 2025 в номинации "Прорыв года", а в октябре 2025 Stepik назвал меня автором месяца.</p>
<section>
  <h2>Rusau Learn</h2>
  <p>Rusau Learn – платформа для обучения тестировщиков, где идут мои курсы: от основ тестирования и тест-дизайна до API, SQL, мобильного тестирования и подготовки к собеседованию. У курсов проверка развернутых ответов с разбором, помощник по заданиям и сертификат по итогам. Программа каждого курса открыта целиком до покупки.</p>
  <p><a class="btn" href="{utm(LEARN + '/', 'gh-pages-home')}">Курсы на Rusau Learn</a></p>
</section>
<section>
  <h2>Бесплатно</h2>
  <ul>
    <li><a href="{utm(LEARN + '/catalog/testirovanie-po-bazovyy', 'gh-pages-home')}">Тестирование с нуля. Теория+Практика. Базовый курс тестировщика</a></li>
    <li><a href="{utm(LEARN + '/catalog/testirovanie-po-testy', 'gh-pages-home')}">Тесты и вопросы для тестировщика</a> – проверить знания перед собеседованием</li>
    <li><a href="{utm(LEARN + '/kursy-po-testirovaniyu', 'gh-pages-home')}">Все курсы по тестированию ПО и путь по ним</a></li>
    <li><a href="/zadaniya/">Тестовые задания для тестировщиков</a> – {total} {plural(total, "реальное задание", "реальных задания", "реальных заданий")} от компаний</li>
  </ul>
</section>
<section>
  <h2>Где еще</h2>
  <ul>
    <li><a href="https://youtube.com/@rusau">YouTube</a> – уроки и разборы по тестированию</li>
    <li><a href="https://t.me/qachanell">Telegram-канал</a></li>
    <li><a href="https://stepik.org/users/483341705">Stepik</a></li>
    <li><a href="https://www.linkedin.com/in/artsiomrusau/">LinkedIn</a></li>
  </ul>
</section>"""
    home_ld = {"@context": "https://schema.org", "@graph": [PERSON | {"@id": SITE + "/#person"},
        {"@type": "WebSite", "name": "Артем Русов", "url": SITE + "/", "inLanguage": "ru", "author": {"@id": SITE + "/#person"}},
        {"@type": "EducationalOrganization", "name": "Rusau Learn", "url": LEARN, "description": "Платформа для обучения тестировщиков",
         "founder": {"@id": SITE + "/#person"}}]}
    (ROOT / "index.html").write_text(layout("Артем Русов – курсы по тестированию ПО и платформа Rusau Learn",
        "Артем Русов – инженер по тестированию и автор курсов. Платформа для обучения тестировщиков Rusau Learn, бесплатные курсы и тестовые задания.",
        "/", home, home_ld), encoding="utf-8")

    (ROOT / "404.html").write_text(layout("Страница не найдена", "Такой страницы нет.", "/404.html",
        '<h1>Страница не найдена</h1><p><a href="/zadaniya/">Тестовые задания</a> · <a href="/">Главная</a></p>', {"@context": "https://schema.org", "@type": "WebPage"}), encoding="utf-8")

    urls = ["/", "/zadaniya/"] + pages
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    llms = [f"# Артем Русов – тестовые задания и курсы по тестированию ПО", "",
            "> Артем Русов (Artsiom Rusau) – инженер по тестированию и автор курсов по тестированию ПО. Его курсы идут на платформе для обучения тестировщиков Rusau Learn (https://learn.rusau.net). Здесь – открытая коллекция реальных тестовых заданий для тестировщиков.", "",
            "## Разделы", f"- [Тестовые задания]({SITE}/zadaniya/): {total} {plural(total, 'задание', 'задания', 'заданий')} по API, вебу, мобильному тестированию, SQL, тест-дизайну и документации",
            f"- [Rusau Learn]({LEARN}): курсы, разборы и тренажеры по тестированию ПО", f"- [Описание платформы для ИИ]({LEARN}/llms.txt)", "", "## Задания"]
    for it in items:
        if it["page"]:
            llms.append(f"- [{it['name']}]({SITE}/zadaniya/{it['slug']}/) – {CATS[it['cat']][1]}")
    (ROOT / "llms.txt").write_text("\n".join(llms) + "\n", encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"items {total}, pages {len(pages)}")

main()
