# Tell Bing and Yandex (IndexNow) that the site's pages changed: every URL from sitemap.xml in one request.
# The key is the name of the *.txt file of 32 hex characters in the repo root.
import json, re, sys, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
key = next(p.stem for p in ROOT.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}", p.stem))
urls = re.findall(r"<loc>([^<]+)</loc>", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))
body = json.dumps({"host": "artichokeee.github.io", "key": key, "keyLocation": f"https://artichokeee.github.io/{key}.txt", "urlList": urls}).encode()
for api in ("https://api.indexnow.org/indexnow", "https://yandex.com/indexnow"):
    req = urllib.request.Request(api, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(api, r.status, len(urls), "адресов")
    except urllib.error.HTTPError as e:
        print(api, e.code, e.read()[:200])
