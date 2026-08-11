# The Health & Well-being Hub — static site

This directory is a self-contained, statically generated NDIS provider
website (SEO/local-lead-gen rebuild — see the project's SEO report for
the full audit). It does not depend on the Django app in the rest of
this repo; it can be deployed as-is to any static host (Netlify, GitHub
Pages, Cloudflare Pages, an S3+CDN bucket, or served by any web server
pointed at this directory).

## Rebuilding the site

All page content lives in `content.py` (services/locations/blog/FAQ
copy) and `pages.py` (per-page titles/meta/schema wiring). Templates are
in `templates/`, shared CSS/JS in `static/`. After editing either file,
regenerate the static HTML:

```
cd health-wellbeing-hub
python3 build.py
```

This rewrites every `*/index.html` file, `sitemap.xml` and `robots.txt`
from scratch (see `clean_generated_dirs()` in `build.py` — it only ever
touches generated output directories, never `templates/`, `static/`,
or the Python source files).

Requires Python 3 + Jinja2 (`pip install jinja2`).

## Required manual configuration before/at launch

### 1. Google Tag Manager (GTM)
Every page's `<head>` loads GTM with a placeholder container ID
(`GTM_CONTAINER_ID` in `templates/base.html`). Create a real GTM
container at tagmanager.google.com, then replace `GTM_CONTAINER_ID` in
`templates/base.html` (both the `<script>` and `<noscript>` blocks) with
your real ID (format `GTM-XXXXXXX`), and rebuild.

### 2. GA4 + Google Ads conversion tracking (configure inside GTM, not in code)
The site pushes structured events to `window.dataLayer` for every
trackable interaction (see `static/js/main.js`). Event names:

| Event | Fires on |
|---|---|
| `phone_click` | any `tel:` link click |
| `whatsapp_click` | any WhatsApp link click |
| `email_click` | any `mailto:` link click |
| `enquiry_cta_click` | any "Make an enquiry" / "Get started" link click |
| `referral_click` | any "Refer a participant" link click |
| `enquiry_submitted` | successful enquiry form submit |
| `referral_submitted` | successful referral form submit |

Every trackable element also carries `data-track-location` (e.g.
`nav`, `sticky_mobile_bar`, `service_hero`) so you can see which part of
the site is driving conversions.

In GTM: create a GA4 Configuration tag, then GA4 Event tags (or Google
Ads Conversion tags) triggered on Custom Event = each event name above.
This keeps no GA4 measurement ID or Google Ads conversion ID hardcoded
in the codebase — it's all configured server-side in GTM, which is also
easier for a non-developer to maintain going forward.

### 3. Google Search Console
- Add the property for `https://www.thehealthwellbeinghub.com`.
- Easiest verification method: use the same GTM container (Search
  Console supports "Google Tag Manager" as a verification method
  directly), or replace the placeholder in the
  `<meta name="google-site-verification" ...>` tag in
  `templates/base.html` with the code GSC gives you, then rebuild.
- Submit `https://www.thehealthwellbeinghub.com/sitemap.xml`.

### 4. Enquiry & referral forms
Neither form has a backend in this codebase. On submit, `main.js`:
1. Pushes the `enquiry_submitted` / `referral_submitted` dataLayer event.
2. POSTs to `FORM_ENDPOINT` (in `static/js/main.js`) if one is configured.
3. Always falls back to opening a pre-filled `mailto:` to
   `thehealthwellbeinghub@gmail.com` so an enquiry is never silently lost.

Recommended: wire up a real endpoint (Formspree, Netlify Forms, a
Google Form via its formResponse endpoint, or a small server endpoint)
and set `FORM_ENDPOINT` in `static/js/main.js`, then rebuild. This is a
one-line change once you've picked a provider.

### 5. Domain / canonical URL
All canonical URLs, Open Graph tags and JSON-LD assume
`https://www.thehealthwellbeinghub.com`. If the real production domain
differs, update `SITE["base_url"]` in `build.py` and rebuild.
