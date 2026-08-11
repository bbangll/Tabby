#!/usr/bin/env python3
"""Static site generator for The Health & Well-being Hub.

Renders Jinja2 templates in templates/ into plain static HTML under the
site root (this directory), using content defined in content.py. Output
is committed to the repo so the site is crawlable with no build step at
serve time — re-run this script after editing templates/content.py.
"""
import datetime
import os
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

import content as C

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(ROOT, "templates")

SITE = {
    "name": "The Health & Well-being Hub",
    "short_name": "H & W",
    "base_url": "https://www.thehealthwellbeinghub.com",
    "phone_display": "0433 604 507",
    "phone_tel": "0433604507",
    "phone_e164": "+61433604507",
    "email": "thehealthwellbeinghub@gmail.com",
    "whatsapp_url": "https://wa.me/61433604507",
    "address_street": "73 Jacaranda Avenue",
    "address_locality": "Logan",
    "address_region": "QLD",
    "address_postcode": "4114",
    "address_full": "73 Jacaranda Avenue, Logan QLD 4114",
    "ndis_reg_number": "4050045262",
    "abn": "91 643 237 045",
    "abn_compact": "91643237045",
    "founder_name": "Kholoud Abdalla",
    "hours": "Mon–Fri 8:00am–5:00pm · Support available 7 days",
    "enquire_url": "/contact/",
    "year": datetime.date.today().year,
}

PAGE_REGISTRY = []  # populated by render(); drives sitemap.xml


def url(path):
    """Site-root-relative URL. Centralised so a future subpath deploy
    only needs to change this function."""
    if not path.startswith("/"):
        path = "/" + path
    return path


def asset(path):
    return path


def icon(name, cls=""):
    classes = ("icon " + cls).strip()
    return Markup(
        '<svg class="{}" aria-hidden="true"><use href="#i-{}"></use></svg>'.format(classes, name)
    )


env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.globals["site"] = SITE
env.globals["url"] = url
env.globals["asset"] = asset
env.globals["icon"] = icon
env.globals["services"] = C.SERVICES
env.globals["locations"] = C.LOCATIONS
env.globals["blog_posts"] = C.BLOG_POSTS
env.globals["current_year"] = SITE["year"]


def render(template_name, out_path, changefreq="monthly", priority="0.6", lastmod=None, **ctx):
    """Render template_name with ctx (plus is_active(prefix) bound to
    out_path) to out_path/index.html and register it for the sitemap."""

    def is_active(prefix):
        return out_path == prefix or (prefix != "/" and out_path.startswith(prefix))

    ctx.setdefault("canonical", out_path)
    ctx["is_active"] = is_active

    tmpl = env.get_template(template_name)
    html = tmpl.render(**ctx)

    if out_path == "/":
        dest_dir = ROOT
    else:
        dest_dir = os.path.join(ROOT, out_path.strip("/"))
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, "index.html")
    with open(dest_file, "w", encoding="utf-8") as f:
        f.write(html)

    PAGE_REGISTRY.append(
        {"path": out_path, "changefreq": changefreq, "priority": priority, "lastmod": lastmod or LASTMOD}
    )
    print("wrote", dest_file)


LASTMOD = datetime.date.today().isoformat()


def write_static_text(rel_path, text):
    dest = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", dest)


def build_sitemap():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for p in sorted(PAGE_REGISTRY, key=lambda p: p["path"]):
        loc = SITE["base_url"] + p["path"]
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append(f"    <lastmod>{p['lastmod']}</lastmod>")
        lines.append(f"    <changefreq>{p['changefreq']}</changefreq>")
        lines.append(f"    <priority>{p['priority']}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    write_static_text("sitemap.xml", "\n".join(lines) + "\n")


def build_robots():
    text = f"""# robots.txt for {SITE['base_url']}
User-agent: *
Allow: /

Sitemap: {SITE['base_url']}/sitemap.xml
"""
    write_static_text("robots.txt", text)


def copy_static():
    src = os.path.join(ROOT, "static")
    # static/ is already in place under the site root; nothing to copy for
    # this generator since templates reference /static/... directly.
    if not os.path.isdir(src):
        raise SystemExit("static/ directory missing")


def clean_generated_dirs():
    """Remove previously generated page directories so renamed/removed
    pages don't leave stale files behind. Only touches known output dirs,
    never templates/, static/, build.py or content.py."""
    keep = {"templates", "static", "build.py", "content.py", "README-SEO.md",
            "robots.txt", "sitemap.xml", "index.html", ".gitignore"}
    for entry in os.listdir(ROOT):
        if entry in keep or entry.startswith("."):
            continue
        full = os.path.join(ROOT, entry)
        if os.path.isdir(full):
            shutil.rmtree(full)


def main():
    clean_generated_dirs()
    copy_static()

    import pages  # noqa: E402  (registers all render() calls)

    pages.build(render, SITE, C)

    build_sitemap()
    build_robots()
    print(f"\nBuilt {len(PAGE_REGISTRY)} pages.")


if __name__ == "__main__":
    main()
