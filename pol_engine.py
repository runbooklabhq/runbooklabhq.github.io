import os, re, glob, json, urllib.request, urllib.parse, datetime

GUMROAD_TOKEN = os.environ.get("GUMROAD_TOKEN", "")  # GitHub Actions secret; never hard-code it
REPO = "runbooklabhq/runbooklabhq.github.io"
GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ETSY_SHOP_URL = "https://www.etsy.com/shop/RunbookLab"

# --- ETSY EXCLUSIVE LISTINGS ---
ETSY_EXCLUSIVES = [
    {
        "name": "Claude Skills Bundle for Product Launch", 
        "url": "https://www.etsy.com/listing/4597283831/claude-skills-bundle-for-product-launch", 
        "desc": "8 tested SKILL.md files for Claude Code and Cowork: positioning, landing page copy, pricing page, launch plan, Product Hunt kit, community posts, launch emails and launch review."
    },
    {
        "name": "Claude Skills Bundle for Freelancers", 
        "url": "https://www.etsy.com/listing/4597264171/claude-code-skills-bundle-for", 
        "desc": "10 tested SKILL.md files for Claude Code and Cowork that write proposals, price projects, review contracts, guard scope and chase unpaid invoices."
    }
]

BANNED_WORDS = [
    "soil", "garden", "photos", "drive", "notion", 
    "approved by", "operator", "minecraft", "plex"
]

def clean_old_junk_guides():
    for g in glob.glob("guide-*.html"):
        if any(b.replace(" ", "-") in g for b in BANNED_WORDS):
            try: os.remove(g)
            except Exception: pass

def check_operator_commands():
    if not GH_TOKEN: return []
    commands = []
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/issues?state=open&per_page=5",
            headers={"Authorization": f"Bearer {GH_TOKEN}", "User-Agent": "PolEngine"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            issues = json.loads(r.read().decode())
            for iss in issues:
                if iss.get("author_association") != "OWNER": continue  # public repo: ignore issues from others
                title = iss.get("title", "").strip()
                if title: commands.append(title)
                creq = urllib.request.Request(
                    f"https://api.github.com/repos/{REPO}/issues/{iss.get('number')}",
                    data=json.dumps({"state": "closed"}).encode(),
                    headers={"Authorization": f"Bearer {GH_TOKEN}", "User-Agent": "PolEngine", "Content-Type": "application/json"},
                    method="PATCH"
                )
                try: urllib.request.urlopen(creq, timeout=8)
                except Exception: pass
    except Exception: pass
    return commands

def fetch_live_market_radar(extra_cmds):
    signals, raw_keywords = [], []
    base_queries = ["n8n webhook ", "n8n python ", "siem alert automation ", "fastapi webhook ", "pdf invoice ocr python "]
    for cmd in extra_cmds:
        clean_cmd = re.sub(r"(?i)deploy\s+", "", cmd).strip()
        if len(clean_cmd) > 4:
            raw_keywords.append(clean_cmd)
            signals.append(f"Operator Directive: {clean_cmd}")

    cycle_offset = (datetime.datetime.utcnow().day + datetime.datetime.utcnow().hour) % len(base_queries)
    for q in (base_queries[cycle_offset:] + base_queries[:cycle_offset])[:4]:
        try:
            url = "https://suggestqueries.google.com/complete/search?client=firefox&q=" + urllib.parse.quote(q)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                sug = [s for s in json.loads(r.read().decode())[1][:4] if not any(b in s.lower() for b in BANNED_WORDS)]
                if sug:
                    signals.append("Google Intent: " + ", ".join(sug[:3]))
                    raw_keywords.extend(sug[:3])
        except Exception: pass

    raw_keywords.extend(["microsoft sentinel soar playbook n8n python", "wazuh siem webhook alert triage n8n", "automated pdf invoice ocr n8n openai vision", "ai customer support webhook triage n8n"])
    return signals, raw_keywords

def ensure_offer_code(prod_id, code_name, amount_off_cents):
    pid = urllib.parse.quote(prod_id)
    data = urllib.parse.urlencode({"access_token": GUMROAD_TOKEN, "name": code_name, "amount_off": str(amount_off_cents), "offer_type": "cents", "max_purchase_count": "3", "universal": "false"}).encode()
    try: urllib.request.urlopen(urllib.request.Request(f"https://api.gumroad.com/v2/products/{pid}/offer_codes", data=data, method="POST"), timeout=10)
    except: pass

def get_dynamic_pricing(prod):
    sales = int(prod.get("sales_count", 0))
    purl = prod.get("short_url", "")
    pid = prod.get("id", "")
    pname = prod.get("name", "").lower()

    # Claude skills packs: real price + real description, never an auto offer code
    if "claude" in pname and "skill" in pname:
        cents = int(prod.get("price", 0) or 0)
        real_price = (f"{cents/100:.2f}".rstrip("0").rstrip(".") + " EUR") if cents else "see page"
        if "launch" in pname:
            desc = "8 tested SKILL.md files for Claude Code and Cowork: positioning, landing page, pricing page, launch plan, Product Hunt kit, community posts, launch emails, launch review."
        else:
            desc = "10 tested SKILL.md files for Claude Code and Cowork: proposals, pricing, contract review, onboarding, scope guard, status updates, invoice follow-up, weekly review, outreach, testimonials."
        return "skills-" + str(pid or pname)[:12], purl, real_price, real_price, sales, desc

    if "qjimps" in purl or "lead" in pname:
        ptype, code, off_cents, btn_price = "lead", "FLASH19" if sales < 3 else "LAUNCH29" if sales < 9 else "", 2800, "19 EUR" if sales < 3 else "29 EUR" if sales < 9 else "47 EUR"
        desc = "Filters 100+ free email providers, live-scrapes domains without paid APIs, scores ICP fit via GPT-4o-mini."
    elif "eqdqfx" in purl or "invoice" in pname or "ocr" in pname:
        ptype, code, off_cents, btn_price = "invoice", "INVOICE21" if sales < 3 else "INVOICE34" if sales < 9 else "", 2800, "21 EUR" if sales < 3 else "34 EUR" if sales < 9 else "49 EUR"
        desc = "Extracts structured JSON data (VAT, Tax ID, Totals) from PDF invoices using Python FastAPI + OpenAI Vision."
    elif "siem" in pname or "secops" in pname or "waf" in pname:
        ptype, code, off_cents, btn_price = "secops", "SECOPS25" if sales < 3 else "SECOPS39" if sales < 9 else "", 3400, "25 EUR" if sales < 3 else "39 EUR" if sales < 9 else "59 EUR"
        desc = "Eliminate 80% of SOC alert fatigue. Ingests SIEM/WAF webhooks, scores SQLi/LFI payloads, and triggers instant WAF block actions."
    elif "support" in pname or "ticket" in pname or "triage" in pname:
        ptype, code, off_cents, btn_price = "support", "SUPPORT19" if sales < 3 else "SUPPORT29" if sales < 9 else "", 2000, "19 EUR" if sales < 3 else "29 EUR" if sales < 9 else "39 EUR"
        desc = "Urgent support ticket triage. Ingests tickets, scores churn risk & sentiment, alerts Slack, and drafts AI replies."
    else:
        ptype, code, off_cents, btn_price = "secops", "SECOPS25" if sales < 3 else "SECOPS39" if sales < 9 else "", 3400, "25 EUR" if sales < 3 else "39 EUR" if sales < 9 else "59 EUR"
        desc = "Eliminate 80% of SOC alert fatigue. Ingests SIEM/WAF webhooks, scores SQLi/LFI payloads, and triggers instant WAF block actions."

    if sales < 3 and code: ensure_offer_code(pid, code, off_cents)
    tier_label = f"{btn_price} (Flash Tier)" if sales < 3 else f"{btn_price} (Growth Tier)" if sales < 9 else f"{btn_price} (Full Margin Tier)"
    promo_url = f"{purl}/{code}" if code else purl
    return ptype, promo_url, tier_label, btn_price, sales, desc

def build_github_readme(catalog_data):
    readme = (
        "# 🚀 Enterprise B2B Automation Suite (Self-Hosted)\n"
        "[![GitHub release](https://img.shields.io/badge/release-v8.2-blue.svg)](#)\n"
        "Replace 300+ EUR/month SaaS subscriptions with self-hosted Python FastAPI microservices and 1-click importable n8n workflows.\n\n"
        "## 📦 Production-Ready Engines (Gumroad)\n"
    )
    for item in catalog_data:
        readme += f"### {item['name']}\n> {item['desc']}\n**[⚡ Download Blueprint ({item['price']})]({item['url']})**\n\n---\n\n"
    
    readme += "## 🛍️ AI Skills & Prompts (Etsy Exclusives)\n"
    for e in ETSY_EXCLUSIVES:
        readme += f"### {e['name']}\n> {e['desc']}\n**[🛍️ View on Etsy]({e['url']})**\n\n---\n\n"

    with open("README.md", "w", encoding="utf-8") as f: f.write(readme)

GUIDE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>__TITLE__ - Production Blueprint</title>
<style>
body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; max-width: 860px; margin: 0 auto; padding: 40px 20px; line-height: 1.6; }
.card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 28px; margin: 24px 0; }
.btn { display: inline-block; background: #10b981; color: #052e16; font-weight: 700; padding: 15px 26px; border-radius: 8px; text-decoration: none; margin-top: 12px; }
.btn-etsy { background: #f97316; color: #fff; margin-left: 10px; }
h1 { color: #fff; } h2 { color: #38bdf8; margin-top: 0; }
</style>
</head>
<body>
<h1>__TITLE__: Self-Hosted Python FastAPI + n8n Blueprint</h1>
<div class="card">
<h2>Ready-to-Deploy Production Pack (__PRICE__ Flash Access)</h2>
<p>__PROD_DESC__</p>
<a class="btn" href="__PROD_URL__">⚡ Download Blueprint (__PRICE__)</a>
<a class="btn btn-etsy" href="__ETSY_URL__" target="_blank">🛍️ View Shop on Etsy</a>
</div>
<p><a style="color:#38bdf8" href="https://runbooklabhq.github.io/">← Back to Storefront</a></p>
</body>
</html>"""

def auto_spawn_radar_pages(raw_keywords, catalog):
    clean_old_junk_guides()
    for kw in raw_keywords[:12]:
        if any(b in kw.lower() for b in BANNED_WORDS): continue
        slug = re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")[:55].strip("-")
        if len(slug) < 5: continue
        
        target = catalog.get("lead")
        if any(w in kw.lower() for w in ["invoice", "ocr"]): target = catalog.get("invoice", target)
        elif any(w in kw.lower() for w in ["support", "ticket"]): target = catalog.get("support", target)
        elif any(w in kw.lower() for w in ["siem", "secops"]): target = catalog.get("secops", target)

        if not target: continue
        page_html = GUIDE_TEMPLATE.replace("__TITLE__", kw.title()).replace("__KEYWORD__", kw).replace("__PRICE__", target["price"]).replace("__PROD_NAME__", target["name"]).replace("__PROD_DESC__", target["desc"]).replace("__PROD_URL__", target["url"]).replace("__ETSY_URL__", ETSY_SHOP_URL)
        with open(f"guide-{slug}.html", "w", encoding="utf-8") as f: f.write(page_html)
    return sorted(glob.glob("guide-*.html"))

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Runbook Lab - Microsoft 365 hardening kits and Claude skills</title>
<style>
body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; max-width: 920px; margin: 0 auto; padding: 40px 20px; line-height: 1.6; }
.card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 28px; margin: 24px 0; }
.badge { background: #f59e0b; color: #000; font-weight: 800; padding: 4px 10px; border-radius: 6px; font-size: 0.85rem; display: inline-block; margin-bottom: 8px; }
.btn { display: inline-block; background: #10b981; color: #052e16; font-weight: 700; padding: 14px 24px; border-radius: 8px; text-decoration: none; margin-top: 10px; }
.btn-etsy { background: #f97316; color: #fff; }
h1 { color: #fff; } h2 { color: #38bdf8; margin-top: 0; }
.links a { color:#34d399; }
.prod-image { width: 100%; max-height: 400px; object-fit: cover; border-radius: 8px; margin-bottom: 15px; border: 1px solid #334155; }
</style>
</head>
<body>
<h1>Runbook Lab</h1>
<p>Practical Microsoft 365 security for admins and MSPs: hardening checklists you can import into Jira, read-only PowerShell checks, and notes on Microsoft deadlines. Plus tested Claude Code skills.</p>
<p class="links">Find us: <a rel="me" href="https://runbooklab.gumroad.com/">Gumroad (kits)</a> · <a rel="me" href="https://github.com/runbooklabhq">GitHub</a> · <a rel="me" href="https://www.agensi.io/creators/runbooklab">Agensi (skills)</a> · <a rel="me" href="https://www.linkedin.com/company/runbooklab/">LinkedIn</a> · <a rel="me" href="https://bsky.app/profile/runbooklab.bsky.social">Bluesky</a> · <a rel="me" href="https://mastodon.social/@runbooklab">Mastodon</a> · <a rel="me" href="https://dev.to/runbooklab">dev.to</a></p>
<div class="card"><h2>Guides</h2><ul>__GUIDE_LINKS__</ul></div>
<h1 style="margin-top:50px;">Kits, skills and blueprints</h1>
__PRODUCT_CARDS__

<p style="color:#94a3b8;font-size:.9rem;margin-top:40px">© Runbook Lab · Not affiliated with or endorsed by Microsoft or Anthropic.</p>
</body>
</html>"""

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pol Cloud Live Dashboard v8.2</title>
<style>
body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; max-width: 920px; margin: 0 auto; }
.box { background: #1e293b; padding: 20px; border-radius: 10px; margin-bottom: 18px; border: 1px solid #334155; }
h2 { color: #38bdf8; margin-top: 0; } a { color: #10b981; font-weight: bold; }
</style>
</head>
<body>
<h1>POL AUTONOMOUS ENGINE v8.2</h1>
<div class="box">
<h2>1. Live Gumroad Portfolio</h2>
<p><b>Total Sales:</b> __SALES__ | <b>Net Revenue:</b> __REV__ USD</p>
__ROWS__
</div>
<div class="box" style="border-color:#f97316">
<h2 style="color:#f97316">2. Etsy Exclusive Listings</h2>
<ul>__ETSY_DASH__</ul>
</div>
<div class="box"><h2>3. Auto-Spawned SEO Pages</h2><ul>__GUIDES__</ul></div>
</body>
</html>"""

def build_storefront_and_sitemap(product_cards_html, etsy_cards_html, all_guides, etsy_dash_html, rows, total_sales, total_rev):
    guide_links_html = "".join(f'<li><a style="color:#38bdf8" href="https://runbooklabhq.github.io/{g}">{g.replace("guide-","").replace(".html","").replace("-"," ").title()}</a></li>\n' for g in all_guides)
    
    idx_html = INDEX_TEMPLATE.replace("__PRODUCT_CARDS__", product_cards_html).replace("__ETSY_CARDS__", etsy_cards_html).replace("__GUIDE_LINKS__", guide_links_html)
    with open("index.html", "w", encoding="utf-8") as f: f.write(idx_html)
    
    dash_html = DASHBOARD_TEMPLATE.replace("__SALES__", str(total_sales)).replace("__REV__", f"{total_rev:.2f}").replace("__ROWS__", rows).replace("__ETSY_DASH__", etsy_dash_html).replace("__GUIDES__", "".join(f'<li><a href="https://runbooklabhq.github.io/{g}">{g}</a></li>\n' for g in all_guides))
    with open("dashboard.html", "w", encoding="utf-8") as f: f.write(dash_html)

    today_iso = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    base_urls = ["https://runbooklabhq.github.io/"] + [f"https://runbooklabhq.github.io/{g}" for g in all_guides]
    with open("sitemap.xml", "w", encoding="utf-8") as f: 
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{u}</loc><lastmod>{today_iso}</lastmod></url>\n" for u in base_urls) + '</urlset>')

def run_cycle():
    if not GUMROAD_TOKEN:
        raise SystemExit("GUMROAD_TOKEN secret is missing: add it in repo Settings > Secrets and variables > Actions")
    req = urllib.request.Request(f"https://api.gumroad.com/v2/products?access_token={GUMROAD_TOKEN}")
    with urllib.request.urlopen(req) as resp: prods = json.loads(resp.read().decode()).get("products", [])

    extra_cmds = check_operator_commands()
    signals, raw_keywords = fetch_live_market_radar(extra_cmds)
    
    total_sales = sum(int(p.get("sales_count", 0)) for p in prods)
    total_rev = sum(float(p.get("sales_usd_cents", 0)) / 100.0 for p in prods)
    rows, product_cards_html, catalog, catalog_data = "", "", {}, []

    for idx, p in enumerate(prods, 1):
        pname = p.get("name", "")
        ptype, promo_url, price_tier_label, btn_price, psales, desc = get_dynamic_pricing(p)
        banner_url = p.get("preview_url") or p.get("thumbnail_url") or "https://via.placeholder.com/1280x720/1e293b/38bdf8?text=Image+Processing"
        
        catalog[ptype] = {"name": pname, "url": promo_url, "price": btn_price, "desc": desc}
        catalog_data.append({"name": pname, "desc": desc, "price": btn_price, "url": promo_url, "banner_url": banner_url})

        rows += f'<div style="padding:10px;border-bottom:1px solid #334155"><b>{pname}</b> - Sales: <b>{psales}</b> | Revenue: <b>{(float(p.get("sales_usd_cents", 0)) / 100.0):.2f} USD</b></div>\n'
        
        product_cards_html += (
            f'<div class="card"><span class="badge">EARLY ADOPTER FLASH TIER ({btn_price})</span><br><br>'
            f'<img src="{banner_url}" class="prod-image" alt="{pname}">'
            f'<h2>{pname}</h2><p>{desc}</p>'
            f'<a class="btn" href="{promo_url}">⚡ Get Instant Access ({btn_price})</a>'
            f'</div>\n'
        )

    # Build Etsy Cards
    etsy_cards_html = "".join(
        f'<div class="card" style="border-color:#f97316">'
        f'<span class="badge" style="background:#f97316;color:#fff">ETSY EXCLUSIVE</span><br><br>'
        f'<h2>{e["name"]}</h2><p>{e["desc"]}</p>'
        f'<a class="btn btn-etsy" href="{e["url"]}" target="_blank" style="margin-left:0;">🛍️ View Details on Etsy</a>'
        f'</div>\n'
        for e in ETSY_EXCLUSIVES
    )
    
    etsy_dash_html = "".join(f'<li><a href="{e["url"]}" style="color:#f97316" target="_blank">{e["name"]}</a></li>\n' for e in ETSY_EXCLUSIVES)

    build_github_readme(catalog_data)
    all_guides = auto_spawn_radar_pages(raw_keywords, catalog)
    build_storefront_and_sitemap(product_cards_html, etsy_cards_html, all_guides, etsy_dash_html, rows, total_sales, total_rev)

if __name__ == "__main__":
    run_cycle()
