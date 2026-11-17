# Extract plain text from every test assignment (doc/docx via macOS textutil, pdf via pypdf, txt as is)
# into out/<category>/<name>.txt and print a report: length and personal-data hits (emails, phones, @handles, links).
import json, re, subprocess, sys
from pathlib import Path
from pypdf import PdfReader

SRC = Path("/Users/rusau/Documents/test-assignments/Список тестовых заданий")
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+?\d[\d\s()\-]{8,}\d)")
HANDLE = re.compile(r"(?<![\w.])@[A-Za-z][\w]{3,}")
URL = re.compile(r"https?://\S+")

report = []
for f in sorted(SRC.rglob("*")):
    if not f.is_file() or f.name == ".DS_Store":
        continue
    cat = f.parent.name
    ext = f.suffix.lower()
    text = ""
    try:
        if ext in (".doc", ".docx"):
            text = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(f)], capture_output=True, text=True, timeout=60).stdout
        elif ext == ".pdf":
            text = "\n".join((p.extract_text() or "") for p in PdfReader(str(f)).pages)
        elif ext == ".txt":
            raw = f.read_bytes()
            for enc in ("utf-8", "cp1251", "utf-16"):
                try:
                    text = raw.decode(enc); break
                except UnicodeDecodeError:
                    continue
    except Exception as e:  # a broken file is reported, not fatal
        text = ""
        print("ERR", f, e, file=sys.stderr)
    text = re.sub(r"[ \t]+\n", "\n", text).strip()
    dst = OUT / cat / (f.stem + ".txt")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    report.append({
        "file": f"{cat}/{f.name}", "ext": ext, "chars": len(text),
        "emails": sorted(set(EMAIL.findall(text)))[:5],
        "phones": sorted(set(p.strip() for p in PHONE.findall(text)))[:5],
        "handles": sorted(set(HANDLE.findall(text)))[:5],
        "urls": sorted(set(URL.findall(text)))[:6],
    })
json.dump(report, open(OUT / "report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for r in report:
    flags = " ".join(k for k in ("emails", "phones", "handles") if r[k])
    print(f'{r["chars"]:>6}  {r["ext"]:<5} {r["file"][:70]:<70} {flags}')
