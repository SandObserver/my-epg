import json, re, requests
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring, indent

SCHEDULE_URL = "https://www.iranintl.com/tvschedule"
CHANNEL_ID   = "iranintl.iitv"
CHANNEL_NAME = "Iran International"
CHANNEL_LANG = "fa"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "fa,en;q=0.9",
}

def _extract_schedule_data(html):
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"([\s\S]*?)"\]\)', html)
    combined = "".join(chunks)
    key_match = re.search(r'\\"scheduleData\\":\s*(\[)', combined)
    if not key_match:
        raise ValueError("scheduleData not found in page")
    start = key_match.start(1)
    depth, i = 0, start
    while i < len(combined):
        ch = combined[i]
        if ch == '\\': i += 2; continue
        if ch == '[': depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                raw = combined[start:i+1]; break
        i += 1
    else:
        raise ValueError("Could not find end of scheduleData array")
    unescaped = raw.replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n')
    return json.loads(unescaped)

def _parse_duration(d):
    parts = d.split(":")
    try: return int(parts[0]) * 60 + int(parts[1])
    except: return 0

resp = requests.get(SCHEDULE_URL, headers=HEADERS, timeout=30)
resp.raise_for_status()
schedule_days = _extract_schedule_data(resp.text)

programmes = []
for day in schedule_days:
    for item in day.get("items", []):
        prog = item.get("programme", {})
        try:
            start_dt = datetime.fromisoformat(item.get("broadcastTime", "").replace("Z", "+00:00"))
        except Exception:
            continue
        dur_m  = _parse_duration(item.get("duration", "00:00:00:00"))
        from datetime import timedelta
        end_dt = start_dt + timedelta(minutes=dur_m)
        programmes.append({
            "start": start_dt.strftime("%Y%m%d%H%M%S %z").strip(),
            "stop":  end_dt.strftime("%Y%m%d%H%M%S %z").strip(),
            "title": prog.get("title", "") or prog.get("englishTitle", ""),
            "type":  prog.get("type", ""),
            "slug":  prog.get("slug"),
        })

tv = Element("tv", attrib={"generator-info-name": "iranintl-epg"})
ch = SubElement(tv, "channel", id=CHANNEL_ID)
SubElement(ch, "display-name", lang=CHANNEL_LANG).text = "ایران اینترنشنال"
SubElement(ch, "display-name", lang="en").text = CHANNEL_NAME
SubElement(ch, "icon", src="https://www.iranintl.com/images/ii/ii-logo-fa.svg")

for p in programmes:
    el = SubElement(tv, "programme", start=p["start"], stop=p["stop"], channel=CHANNEL_ID)
    SubElement(el, "title", lang=CHANNEL_LANG).text = p["title"]
    if p["type"]: SubElement(el, "category", lang="en").text = p["type"]
    if p["slug"]: SubElement(el, "url").text = f"https://www.iranintl.com/vod/{p['slug']}"

try: indent(tv, space="  ")
except TypeError: pass

xml = b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(tv, encoding="unicode").encode("utf-8")

import os
os.makedirs("output", exist_ok=True)
with open("output/iranintl.xml", "wb") as f:
    f.write(xml)

print(f"Done. {len(programmes)} programmes written.")
