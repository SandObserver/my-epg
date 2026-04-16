import os, requests
from datetime import datetime, timezone, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring, indent

YOUTUBE_API_KEY  = os.environ["YOUTUBE_API_KEY"]
CHANNEL_ID_YT    = "UCnUdm0u-2FRffBnxQYHuTHA"
XMLTV_CHANNEL_ID = "manoto.tv"
CHANNEL_NAME     = "Manoto TV"
CHANNEL_LANG     = "fa"

base = "https://www.googleapis.com/youtube/v3"

r = requests.get(f"{base}/search", params={
    "part": "snippet", "channelId": CHANNEL_ID_YT,
    "eventType": "live", "type": "video",
    "key": YOUTUBE_API_KEY, "maxResults": 1,
}, timeout=15)
r.raise_for_status()
items = r.json().get("items", [])

if items:
    title = items[0]["snippet"]["title"]
else:
    r2 = requests.get(f"{base}/search", params={
        "part": "snippet", "channelId": CHANNEL_ID_YT,
        "eventType": "completed", "type": "video",
        "order": "date", "key": YOUTUBE_API_KEY, "maxResults": 1,
    }, timeout=15)
    r2.raise_for_status()
    items2 = r2.json().get("items", [])
    title = items2[0]["snippet"]["title"] if items2 else CHANNEL_NAME

now   = datetime.now(tz=timezone.utc)
start = now.replace(hour=0, minute=0, second=0, microsecond=0)
stop  = start + timedelta(hours=24)
fmt   = "%Y%m%d%H%M%S %z"

tv = Element("tv", attrib={"generator-info-name": "manoto-epg"})
ch = SubElement(tv, "channel", id=XMLTV_CHANNEL_ID)
SubElement(ch, "display-name", lang=CHANNEL_LANG).text = "من‌و‌تو"
SubElement(ch, "display-name", lang="en").text = CHANNEL_NAME
prog = SubElement(tv, "programme",
    start=start.strftime(fmt).strip(),
    stop=stop.strftime(fmt).strip(),
    channel=XMLTV_CHANNEL_ID)
SubElement(prog, "title", lang=CHANNEL_LANG).text = title

try: indent(tv, space="  ")
except TypeError: pass

xml = b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(tv, encoding="unicode").encode("utf-8")

import os as _os
_os.makedirs("output", exist_ok=True)
with open("output/manoto.xml", "wb") as f:
    f.write(xml)

print(f"Done. Title: {title}")
