#!/usr/bin/env python3
"""Generate one cover image per guide via kie.ai GPT Image 2 (gpt-image-2-text-to-image),
then compress to covers/<slug>.webp (~1200px). Key: .kie_key (gitignored) or $KIE_API_KEY.

  python3 gen_covers.py [slug ...]   # default: all; skips slugs that already have a cover
"""
import json, os, pathlib, re, subprocess, sys, time, io
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
KEY = os.environ.get("KIE_API_KEY", "").strip() or (HERE/".kie_key").read_text().strip()
API = "https://api.kie.ai/api/v1/jobs"
RAW = HERE/"covers_raw"; OUT = HERE/"covers"
RAW.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)

STYLE = ("Flat modern editorial vector illustration, warm friendly brand style. Soft cream background. "
         "Primary accent warm coral-orange, secondary mint-green and soft sky-blue, charcoal-navy ink linework. "
         "Clean minimal composition, generous negative space, rounded shapes, subtle soft shadows, no photorealism. "
         "Absolutely no text, no letters, no words, no numbers anywhere in the image. Travel and AI-search theme. "
         "Centered, balanced, 3:2 landscape. Subject: ")

SUBJECTS = {
 "get-your-travel-agency-recommended-by-chatgpt":
   "a tidy travel agent's desk with a small globe and a paper airplane, and a glowing rounded chat bubble floating above it recommending a trip, warm and inviting.",
 "why-isnt-my-travel-agency-showing-up-in-chatgpt":
   "a world map dotted with location pins; a large magnifying glass highlights one pin glowing coral while the others stay muted grey, suggesting a business being found or overlooked.",
 "how-to-claim-your-travel-agency-in-chatgpt":
   "a friendly travel-agency storefront sign with a large glowing verified checkmark badge and a small passport stamp beside it, suggesting claiming and verifying a profile.",
 "make-your-travel-website-visible-to-ai":
   "a simple browser window showing a small travel website, with a cute friendly robot reading it through a magnifier, light signal lines and gears around it, suggesting a site being read by AI.",
 "chatgpt-business-listing-requirements-travel-agencies":
   "a clipboard with a neat checklist next to a small globe, a phone and a tag, suggesting listing requirements and verification steps for a travel business.",
 "chatgpt-business-hub-for-travel-agencies":
   "a clean analytics dashboard panel with simple rounded bar charts, a small globe and tiny airplane icons, suggesting a business insights dashboard for travel.",
 "chatgpt-business-agent-for-travel-agencies":
   "a friendly rounded robot concierge standing beside a travel desk bell and a small suitcase, with a chat bubble, suggesting an AI customer agent for a travel business.",
 "chatgpt-vs-google-business-profile-travel-agencies":
   "two rounded profile cards side by side being compared, one with a chat bubble and one with a map pin, a small balance-scale motif between them, suggesting a comparison.",
 "chatgpt-business-profile-for-travel-agencies":
   "an optimistic hero scene: a travel desk with an open laptop, a globe, a paper airplane and a glowing friendly AI assistant orb with a chat bubble, warm and welcoming.",
}

def curl(args, t=120):
    return json.loads(subprocess.check_output(["curl","-s","-H",f"Authorization: Bearer {KEY}"]+args, timeout=t))

def create(slug):
    d = curl(["-X","POST",f"{API}/createTask","-H","Content-Type: application/json",
              "-d", json.dumps({"model":"gpt-image-2-text-to-image",
                                "input":{"prompt":STYLE+SUBJECTS[slug],"image_size":"3:2"}})])
    tid = (d.get("data") or {}).get("taskId")
    if not tid: raise SystemExit(f"{slug}: createTask failed {json.dumps(d)[:200]}")
    return tid

def finish(slug, tid):
    t0=time.time()
    while time.time()-t0 < 360:
        r = curl([f"{API}/recordInfo?taskId={tid}"]); data=r.get("data",{})
        if data.get("successFlag")==1 or str(data.get("state","")).lower() in ("success","succeeded","completed"):
            url = re.findall(r'https?://[^\s"\\]+\.(?:jpe?g|png|webp)', data.get("resultJson") or json.dumps(data), re.I)
            if not url: raise SystemExit(f"{slug}: no url in {json.dumps(data)[:200]}")
            png = subprocess.check_output(["curl","-s","-L",url[0]], timeout=120)
            (RAW/f"{slug}.png").write_bytes(png)
            im = Image.open(io.BytesIO(png)).convert("RGB")
            if im.width>1200: im=im.resize((1200,round(1200*im.height/im.width)))
            im.save(OUT/f"{slug}.webp","WEBP",quality=82,method=6)
            print(f"  ok {slug}  {(OUT/f'{slug}.webp').stat().st_size//1024} KB"); return
        if str(data.get("state","")).lower() in ("fail","failed","error"):
            raise SystemExit(f"{slug}: failed {data.get('failMsg')}")
        time.sleep(6)
    raise SystemExit(f"{slug}: timeout")

def main(slugs):
    todo=[s for s in (slugs or SUBJECTS) if not (OUT/f"{s}.webp").exists()]
    print(f"generating {len(todo)} covers")
    tasks={s:create(s) for s in todo}          # fire all, then poll (parallel generation)
    for s,tid in tasks.items(): finish(s,tid)
    print("done")

if __name__=="__main__": main(sys.argv[1:])
