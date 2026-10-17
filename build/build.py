#!/usr/bin/env python3
"""
Static site generator for ukrainianschooldetroit.org (2026 redesign).

    python3 build/build.py            # writes *.html into the repository root
    python3 build/build.py --artifact DIR   # also writes a preview copy for an artifact host

Content sources:
  data/news.json      latest announcements (title, date, image, link to the original post)
  data/homework.json  weekly homework PDFs per class (trimester 1, 2026-27)
  data/exams.json     past written matura exams by year and subject
  data/lessons.json   culture / history lecture PDFs
  build/handbook.txt  the student handbook text (Правила учнів)

Everything else (page copy, navigation, schedule) lives in this file.
"""
import datetime
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BUILD = ROOT / "build"

SITE_NAME = "Рідна Школа · Детройт"
SITE_URL = "https://www.ukrainianschooldetroit.org/"
EMAIL = "ukrainianschooldetroit@gmail.com"
FACEBOOK = "https://www.facebook.com/ukrainianschooldetroit/"
CALENDAR_ID = "ukrainianschooldetroit@gmail.com"
CALENDAR_EMBED = ("https://calendar.google.com/calendar/embed?src=ukrainianschooldetroit%40gmail.com"
                  "&ctz=America%2FNew_York&showTitle=0&showPrint=0&showCalendars=0&wkst=1")
CALENDAR_EMBED_AGENDA = CALENDAR_EMBED + "&mode=AGENDA"
REG_FORM = "https://docs.google.com/forms/d/e/1FAIpQLSfZHVqJ1GHoxHxrS5rL2ZjTMxNOfBLRr1xKLbROMEiRnCYvKw/viewform"
REG_FORM_EMBED = REG_FORM + "?embedded=true"
PAYPAL = "https://www.paypal.com/donate?hosted_button_id=YQTA6DRX49RN6"
OLD_SITE = "https://ukrainianschooldetroit.org/"
UPLOADS = "https://ukrainianschooldetroit.org/wp-content/uploads/"

YEAR = datetime.date.today().year

MONTHS_UK = ["січня", "лютого", "березня", "квітня", "травня", "червня",
             "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]
MONTHS_EN = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]


def esc(s):
    return html.escape(s, quote=True)


def t(uk, en, tag="span"):
    """Bilingual inline fragment: Ukrainian shown by default, English when the toggle is on."""
    return f'<{tag} class="lang-uk">{uk}</{tag}><{tag} class="lang-en">{en}</{tag}>'


def tp(uk, en):
    """Bilingual paragraph pair."""
    return f'<p class="lang-uk">{uk}</p><p class="lang-en">{en}</p>'


def date_uk(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {MONTHS_UK[m - 1]} {y}"


def date_en(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{MONTHS_EN[m - 1]} {d}, {y}"


# ---------------------------------------------------------------- icons
ICONS = {
    "pen": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>',
    "calendar": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
    "users": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "form": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M9 13h6M9 17h6"/></svg>',
    "book": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
    "award": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="6"/><path d="M8.2 13.9 7 22l5-3 5 3-1.2-8.1"/></svg>',
    "file": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>',
    "link": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    "info": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
    "play": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="m10 8 6 4-6 4z"/></svg>',
}

ICONS.update({
    "arrow": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 5l7 7-7 7"/></svg>',
    "heart": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 21s-7-4.534-7-10a4 4 0 0 1 7-2.646A4 4 0 0 1 19 11c0 5.466-7 10-7 10Z"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 4h16v16H4z"/><path d="m22 6-10 7L2 6"/></svg>',
    "facebook": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13 22v-8h3l1-4h-4V7.5c0-1.1.5-2 2-2h2V2c-.5-.1-1.8-.2-3-.2-3 0-5 1.7-5 5v3.2H6v4h3V22h4Z"/></svg>',
    "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
})

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="14" fill="#0f2a5c"/>
<rect x="8" y="8" width="48" height="48" rx="10" fill="#e3b23c"/>
<text x="32" y="42" text-anchor="middle" font-family="Arial, sans-serif" font-weight="700" font-size="26" fill="#16213a">РШ</text>
</svg>"""

# ---------------------------------------------------------------- navigation
NAV = [
    ("about.html", "Про школу", "About"),
    ("parents.html", "Батькам", "Parents"),
    ("homework.html", "Домашні завдання", "Homework"),
    ("calendar.html", "Календар", "Calendar"),
    ("lessons.html", "Матеріали", "Resources"),
    ("contact.html", "Контакт", "Contact"),
]


def promo():
    n = news[0]
    iso = news_iso(n)
    return f"""
<div class="promo">
  <div class="wrap">
    <p><span class="flag" aria-hidden="true"></span><span class="t"><b>{t("Новина", "News")}</b> · {esc(news_title(n))} · {t(date_uk(iso), date_en(iso))}</span></p>
    <a href="{PAYPAL}" rel="noopener">{t("Підтримати школу", "Support the school")}{ICONS['arrow']}</a>
  </div>
</div>"""


def header():
    links = "".join(f'<a href="{href}">{t(uk, en)}</a>' for href, uk, en in NAV)
    links += f'<a class="nav-reg" href="registration.html">{t("Реєстрація", "Register")}</a>'
    return f"""
<a class="skip-link" href="#main">{t("Перейти до змісту", "Skip to content")}</a>
{promo()}
<header class="site-header" id="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="index.html" aria-label="Рідна Школа — головна">
      <span class="brand-mark" aria-hidden="true">РШ</span>
      <span class="brand-text">
        <strong>{t("Рідна Школа", "Ridna Shkola")}</strong>
        <span>{t("Школа українознавства · Детройт", "Ukrainian school · Detroit")}</span>
      </span>
    </a>
    <nav class="site-nav" id="site-nav" aria-label="Головна навігація">{links}</nav>
    <div class="header-actions">
      <div class="lang-switch" role="group" aria-label="Мова / Language">
        <button type="button" data-lang="uk" aria-pressed="true">UA</button>
        <button type="button" data-lang="en" aria-pressed="false">EN</button>
      </div>
      <a class="btn btn-line" href="registration.html">{t("Реєстрація", "Register")}</a>
      <a class="btn btn-blue" href="{PAYPAL}" rel="noopener">{ICONS['heart']}<span>{t("Пожертва", "Donate")}</span></a>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Меню / Menu">{ICONS['menu']}</button>
    </div>
  </div>
</header>
"""


def footer():
    return f"""
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <a class="brand" href="index.html">
        <span class="brand-mark" aria-hidden="true">РШ</span>
        <span class="brand-text"><strong>{t("Рідна Школа", "Ridna Shkola")}</strong><span>{t("Школа українознавства · Детройт", "Ukrainian school · Detroit")}</span></span>
      </a>
      <p class="lang-uk">Школа Українознавства Товариства «Рідна Школа» в Детройті. Суботня школа української мови, літератури, історії, географії та культури для дітей від дошкілля до 11 класу.</p>
      <p class="lang-en">School of Ukrainian Language and Culture of the Ridna Shkola Society in Detroit. A Saturday school of Ukrainian language, literature, history, geography and culture, preschool through grade 11.</p>
      <div class="social">
        <a href="{FACEBOOK}" rel="noopener" aria-label="Facebook">{ICONS['facebook']}</a>
        <a href="mailto:{EMAIL}" aria-label="Email">{ICONS['mail']}</a>
      </div>
    </div>
    <div>
      <h3>{t("Меню", "Menu")}</h3>
      <ul>
        <li><a href="about.html">{t("Про школу", "About the school")}</a></li>
        <li><a href="parents.html">{t("Для батьків", "For parents")}</a></li>
        <li><a href="registration.html">{t("Реєстрація та оплата", "Registration and payments")}</a></li>
        <li><a href="homework.html">{t("Домашні завдання", "Homework")}</a></li>
        <li><a href="calendar.html">{t("Календар", "Calendar")}</a></li>
        <li><a href="handbook.html">{t("Шкільний правильник", "Student handbook")}</a></li>
      </ul>
    </div>
    <div>
      <h3>{t("Навчання", "Learning")}</h3>
      <ul>
        <li><a href="lessons.html">{t("Лекції та матеріали", "Lessons and materials")}</a></li>
        <li><a href="exams.html">{t("Матура / іспити", "Final exams (Matura)")}</a></li>
        <li><a href="downloads.html">{t("Корисні ресурси", "Useful resources")}</a></li>
        <li><a href="https://www.shkilnarada.org/" rel="noopener">{t("Шкільна Рада УККА", "Education Council (UCCA)")}</a></li>
        <li><a href="http://www.encyclopediaofukraine.com/default.asp" rel="noopener">Encyclopedia of Ukraine</a></li>
      </ul>
    </div>
    <div>
      <h3>{t("Контакт", "Contact")}</h3>
      <p style="margin-top:0">{t("Воррен, Мічиган", "Warren, Michigan")}<br>{t("Щосуботи, 9:15 – 13:15", "Saturdays, 9:15 am – 1:15 pm")}<br><a href="mailto:{EMAIL}">{EMAIL}</a></p>
      <a class="btn btn-gold" href="{PAYPAL}" rel="noopener">{ICONS['heart']}{t("Пожертва", "Donate")}</a>
    </div>
  </div>
  <div class="footer-bottom">
    <div class="wrap">
      <span>© {YEAR} {t("Школа Українознавства Т-ва «Рідна Школа», Детройт", "School of Ukrainian Language and Culture, Detroit")} · <a href="{OLD_SITE}" rel="noopener">{t("Архів новин", "News archive")}</a></span>
      <span class="glory"><span class="flag" aria-hidden="true"></span>Слава Україні · Glory to Ukraine</span>
    </div>
  </div>
</footer>
"""


def layout(slug, title_uk, title_en, desc, body):
    return f"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title_uk)} — {SITE_NAME}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title_uk)} — {SITE_NAME}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="uk_UA">
<meta property="og:locale:alternate" content="en_US">
<meta name="theme-color" content="#0a3d7e">
<link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=Literata:wght@500;600;700&display=swap">
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
{header()}
<main id="main">
{body}
</main>
{footer()}
<script src="assets/js/main.js" defer></script>
</body>
</html>
"""


def page_head(eyebrow_uk, eyebrow_en, title_uk, title_en, intro_uk="", intro_en=""):
    intro = tp(intro_uk, intro_en) if intro_uk else ""
    return f"""
<section class="page-head">
  <div class="wrap">
    <span class="eyebrow on-dark">{t(eyebrow_uk, eyebrow_en)}</span>
    <h1>{t(title_uk, title_en)}</h1>
    {intro}
  </div>
</section>
"""


def file_item(href, label, meta_uk="", meta_en="", icon="file"):
    meta = f'<span class="meta">{t(meta_uk, meta_en)}</span>' if meta_uk else ""
    return f'<li>{ICONS[icon]}<div><a href="{esc(href)}" rel="noopener">{label}</a>{meta}</div></li>'


# ---------------------------------------------------------------- data
news = json.load(open(DATA / "news.json", encoding="utf-8"))
homework = json.load(open(DATA / "homework.json", encoding="utf-8"))
exams = json.load(open(DATA / "exams.json", encoding="utf-8"))
lessons = json.load(open(DATA / "lessons.json", encoding="utf-8"))

EN_MONTH_TO_NUM = {m: i + 1 for i, m in enumerate(MONTHS_EN)}


def news_iso(item):
    d, m, y = item["date"].split()
    return f"{y}-{EN_MONTH_TO_NUM[m]:02d}-{int(d):02d}"


def news_title(item):
    if item["title"]:
        return item["title"].strip()
    txt = (item.get("text") or "").strip()
    if txt:
        first = re.split(r"[.!?\n]", txt)[0].strip()
        if 10 < len(first) < 90:
            return first
    return "Оголошення Рідної Школи"


def news_card(item):
    iso = news_iso(item)
    img = item.get("local") or ""
    title = esc(news_title(item))
    excerpt = esc((item.get("text") or "").replace("\n", " ").strip()[:180])
    thumb = f'<div class="thumb"><img src="{img}" alt="" loading="lazy" width="{item.get("w", 600)}" height="{item.get("h", 800)}"></div>' if img else ""
    body = f"<p>{excerpt}</p>" if excerpt else ""
    return f"""
<article class="news-card">
  {thumb}
  <div class="body">
    <time datetime="{iso}">{t(date_uk(iso), date_en(iso))}</time>
    <h3><a href="{esc(item['url'])}" rel="noopener">{title}</a></h3>
    {body}
    <a class="more" href="{esc(item['url'])}" rel="noopener">{t("Переглянути оголошення →", "View announcement →")}</a>
  </div>
</article>"""


# ---------------------------------------------------------------- home
LEVELS = [
    ("Дошкілля", "Preschool", "Дошкілля", "Preschool", "Групи «а» і «б»: знайомство з українською мовою через гру.", "Groups A and B: first steps in Ukrainian through play.", "var(--gold)"),
    ("1–4 клас", "Grades 1–4", "Початкова школа", "Early grades", "Читання, письмо й розмова. У більшості класів є паралельні групи «а» і «б».", "Reading, writing and speaking. Most grades run parallel A and B groups.", "var(--blue)"),
    ("5–8 клас", "Grades 5–8", "Середня школа", "Middle grades", "Мова й література, історія та народознавство. Групи «а» і «б» у 6 і 7 класах.", "Language and literature, history and folk studies. Grades 6 and 7 have A and B groups.", "#059669"),
    ("9–11 клас", "Grades 9–11", "Старша школа", "Upper grades", "Мова, література, історія, культура й географія. У 11 класі учні складають матуру.", "Language, literature, history, culture and geography. Grade 11 sits the matura exams.", "#e11d48"),
]

YEAR_COLORS = [("#0a3d7e", "#06224a"), ("#f5b800", "#b45309"), ("#047857", "#064e3b"), ("#be123c", "#881337"),
               ("#334155", "#0f172a"), ("#4338ca", "#312e81"), ("#0e7490", "#164e63"), ("#a21caf", "#701a75"), ("#57534e", "#292524")]


def home():
    feat = news[0]
    fiso = news_iso(feat)
    feature = f"""
      <div class="feature">
        <div class="feature-img">
          <img src="{feat['local']}" alt="" width="{feat.get('w', 600)}" height="{feat.get('h', 900)}">
          <span class="feature-badge"><i></i>{t("Нове оголошення", "Latest announcement")}</span>
          <div class="feature-title">{esc(news_title(feat))}</div>
        </div>
        <div class="feature-foot">
          <div><div class="k">{t("Дата", "Date")}</div><div class="v">{t(date_uk(fiso), date_en(fiso))}</div></div>
          <a class="btn btn-dark" href="{esc(feat['url'])}" rel="noopener">{t("Переглянути", "View")}{ICONS['arrow']}</a>
        </div>
      </div>"""
    hero = f"""
<section class="hero">
  <div class="wrap hero-inner">
    <div>
      <span class="pill"><span class="dot"></span>{t("Детройт · Воррен, Мічиган", "Detroit · Warren, Michigan")}</span>
      <h1 class="lang-uk">Вчимо дітей бути <span class="gradient-text">українцями.</span> Уже 75 років, щосуботи.</h1>
      <h1 class="lang-en">Raising Ukrainian kids in Michigan. <span class="gradient-text">Seventy-five years</span> of Saturdays.</h1>
      <p class="lede lang-uk">Школа Українознавства Товариства «Рідна Школа»: українська мова, література, історія, географія та культура для дітей від дошкілля до 11 класу. Навчаємо з <b>1951 року</b>.</p>
      <p class="lede lang-en">The School of Ukrainian Language and Culture of the Ridna Shkola Society: language, literature, history, geography and culture for children from preschool through grade 11. Teaching since <b>1951</b>.</p>
      <div class="hero-actions">
        <a class="btn btn-gold btn-lg" href="registration.html">{t("Реєстрація на 2026–27", "Register for 2026–27")}{ICONS['arrow']}</a>
        <a class="btn btn-glass btn-lg" href="homework.html">{t("Домашні завдання", "Homework")}</a>
        <a class="btn btn-lg" style="color:rgba(255,255,255,.85)" href="about.html">{t("Про школу", "About us")}</a>
      </div>
      <div class="hero-stats">
        <div><div class="n">75</div><div class="l">{t("років навчання", "years of teaching")}</div></div>
        <div><div class="n">12</div><div class="l">{t("рівнів: дошкілля та 1–11 класи", "levels: preschool and grades 1–11")}</div></div>
        <div><div class="n">33</div><div class="l">{t("навчальні суботи щороку", "school Saturdays a year")}</div></div>
      </div>
    </div>
    <div>{feature}
    </div>
  </div>
</section>
"""
    strip = f"""
<section class="strip" aria-label="Швидкі посилання / Quick links">
  <div class="wrap">
    <div class="strip-grid">
      <a class="quick" href="registration.html"><span class="tile">{ICONS['users']}</span><span><strong>{t("Реєстрація", "Registration")}</strong><span class="desc">{t("Зареєструйте дитину на 2026–27", "Enroll your child for 2026–27")}</span></span></a>
      <a class="quick" href="homework.html"><span class="tile tile-gold">{ICONS['pen']}</span><span><strong>{t("Домашні завдання", "Homework")}</strong><span class="desc">{t("PDF для кожного класу, щотижня", "A PDF for every class, weekly")}</span></span></a>
      <a class="quick" href="calendar.html"><span class="tile tile-emerald">{ICONS['calendar']}</span><span><strong>{t("Календар", "Calendar")}</strong><span class="desc">{t("Навчальні дні, свята, вихідні", "School days, holidays, breaks")}</span></span></a>
      <a class="quick" href="{PAYPAL}" rel="noopener"><span class="tile tile-rose">{ICONS['heart']}</span><span><strong>{t("Пожертва", "Donate")}</strong><span class="desc">{t("Підтримайте школу та її учнів", "Support the school and its students")}</span></span></a>
    </div>
  </div>
</section>
"""
    about = f"""
<section class="section" id="about">
  <div class="wrap split">
    <div class="sticky">
      <span class="eyebrow">{t("Про школу", "About the school")}</span>
      <h2 style="margin-top:.75rem">{t("Школа, де діти <em style='font-style:normal;color:var(--accent)'>ростуть</em> українцями", "A school where children <em style='font-style:normal;color:var(--accent)'>grow up</em> Ukrainian")}</h2>
      <p class="lead lang-uk">Рідна Школа обігріває своєю любов’ю не одне покоління українців на американській землі. Тут батьки довіряють учителям найдорожче: своїх дітей, яких навчають рідної мови, культури та історії.</p>
      <p class="lead lang-en">For generations, Ridna Shkola has been where Ukrainian American families bring their children to learn their language, culture and history from teachers who treat them as their own.</p>
      <blockquote class="quote">
        <span class="lang-uk">«Навчити її бути українцями на чужині».</span>
        <span class="lang-en">"To teach them to be Ukrainian abroad."</span>
        <cite>{t("М. Дольницький та І. Білоус, засновники школи", "M. Dolnytsky and I. Bilous, founders of the school")}</cite>
      </blockquote>
      <a class="link-arrow" href="about.html">{t("Читати про школу", "Read about the school")}{ICONS['arrow']}</a>
    </div>
    <div class="values">
      <div class="card value"><span class="tile tile-solid tile-blue">{ICONS['pen']}</span><h3>{t("Мова", "Language")}</h3><p>{t("Читання, письмо та розмова українською від дошкілля до 11 класу.", "Reading, writing and speaking Ukrainian from preschool to grade 11.")}</p></div>
      <div class="card value"><span class="tile tile-solid tile-gold">{ICONS['book']}</span><h3>{t("Історія й географія", "History and geography")}</h3><p>{t("Лекції з історії та географії України, що завершуються матурою.", "Lectures on Ukrainian history and geography, leading up to the matura.")}</p></div>
      <div class="card value"><span class="tile tile-solid tile-emerald">{ICONS['award']}</span><h3>{t("Культура й звичаї", "Culture and customs")}</h3><p>{t("Народознавство, одяг, їжа та свята: від Святвечора до вишиванки.", "Folk studies, clothing, food and holidays, from Sviat Vechir to the vyshyvanka.")}</p></div>
      <div class="card value"><span class="tile tile-solid tile-rose">{ICONS['users']}</span><h3>{t("Громада", "Community")}</h3><p>{t("Свято Першого Дзвоника, Свято Букварика, зустрічі, концерти й живі лекції.", "The First Bell celebration, Bukvaryk festival, guest talks, concerts and live lectures.")}</p></div>
    </div>
  </div>
</section>
"""
    levels_html = "".join(
        f"""<a class="level" style="--bar:{bar}" href="homework.html">
          <div class="k">{t(k_uk, k_en)}</div>
          <div class="big">{t(big_uk, big_en)}</div>
          <p>{t(d_uk, d_en)}</p>
          <span class="go">{t("Завдання для класу", "Class homework")}{ICONS['arrow']}</span>
        </a>"""
        for k_uk, k_en, big_uk, big_en, d_uk, d_en, bar in
        [(l[3] if False else l[2], l[3], l[0], l[1], l[4], l[5], l[6]) for l in LEVELS]
    )
    levels = f"""
<section class="section section-alt" id="levels">
  <div class="wrap">
    <div class="section-head">
      <div>
        <span class="eyebrow">{t("Класи", "Grades")}</span>
        <h2>{t("Дванадцять рівнів, одна подорож", "Twelve levels, one journey")}</h2>
      </div>
      <p>{t("Від першого слова в дошкіллі до матури в 11 класі: щотижневі завдання та лекції для кожного класу.", "From the first words in preschool to the matura in grade 11, with weekly assignments and lectures for every class.")}</p>
    </div>
    <div class="levels">{levels_html}</div>
  </div>
</section>
"""
    cards = "".join(news_card(n) for n in news[:6])
    newsec = f"""
<section class="section" id="news">
  <div class="wrap">
    <div class="section-head">
      <div>
        <span class="eyebrow">{t("Новини", "News")}</span>
        <h2>{t("Оголошення та події", "Announcements and events")}</h2>
      </div>
      <a class="btn btn-line" href="{FACEBOOK}" rel="noopener">{t("Більше на Facebook", "More on Facebook")}{ICONS['arrow']}</a>
    </div>
    <div class="news-grid">{cards}</div>
  </div>
</section>
"""
    day = f"""
<section class="section section-alt" id="day">
  <div class="wrap split even">
    <div>
      <span class="eyebrow">{t("Шкільний день", "The school day")}</span>
      <h2 style="margin-top:.75rem">{t("Щосуботи, з 9:15 до 13:15", "Every Saturday, 9:15 am to 1:15 pm")}</h2>
      <p class="lead lang-uk">П’ять 45-хвилинних занять і велика перерва. Приміщення відкрите з 9:00; день розпочинається і закінчується молитвою.</p>
      <p class="lead lang-en">Five 45-minute periods and a long break. Doors open at 9:00 am; the day begins and ends with a prayer.</p>
      <div class="panel" style="padding:.5rem 1rem">
        <table class="timetable">
          <thead><tr><th>{t("Урок", "Period")}</th><th>{t("Початок", "Starts")}</th></tr></thead>
          <tbody>
            <tr><td class="n">I</td><td>9:15</td></tr>
            <tr><td class="n">II</td><td>10:00</td></tr>
            <tr><td class="n">III</td><td>10:45</td></tr>
            <tr class="break"><td class="n">—</td><td>{t("Велика перерва 11:25 – 11:45", "Long break 11:25 – 11:45")}</td></tr>
            <tr><td class="n">IV</td><td>11:45</td></tr>
            <tr><td class="n">V</td><td>12:30</td></tr>
          </tbody>
        </table>
      </div>
    </div>
    <div>
      <div class="embed">
        <iframe src="{CALENDAR_EMBED_AGENDA}" title="Google Calendar: Рідна Школа" loading="lazy" style="min-height:520px"></iframe>
        <div class="embed-note">{t("Найближчі дати.", "Upcoming dates.")} <a href="calendar.html">{t("Повний календар", "Full calendar")}</a> · <a href="https://calendar.google.com/calendar/u/0/embed?src={CALENDAR_ID}" rel="noopener">{t("відкрити в Google Calendar", "open in Google Calendar")}</a></div>
      </div>
    </div>
  </div>
</section>
"""
    years = sorted(exams, reverse=True)[:9]
    pos = [("30%", "20%"), ("70%", "30%"), ("50%", "70%"), ("40%", "30%"), ("60%", "60%"), ("30%", "50%"), ("50%", "30%"), ("70%", "60%"), ("20%", "40%")]
    ycards = "".join(
        f'<a class="year-card" href="exams.html" style="--a:{YEAR_COLORS[i][0]};--b:{YEAR_COLORS[i][1]};--x:{pos[i][0]};--y:{pos[i][1]}"><span class="y"><b>{y}</b><span>{t("Матура · іспити", "Matura · exams")} →</span></span></a>'
        for i, y in enumerate(years)
    )
    matura = f"""
<section class="section" id="matura">
  <div class="wrap">
    <div class="section-head">
      <div>
        <span class="eyebrow">{t("Матура", "Final exams")}</span>
        <h2>{t("Архів письмових іспитів", "Archive of written exams")}</h2>
      </div>
      <p>{t("Мова, література, історія, географія й культура: іспити за кожен рік, щоб випускники могли підготуватися.", "Language, literature, history, geography and culture: exams from every year, so graduating students can practise.")}</p>
    </div>
    <div class="years">{ycards}</div>
  </div>
</section>
"""
    donate = f"""
<section class="section" style="padding-top:0" id="donate">
  <div class="wrap">
    <div class="donate">
      <div class="donate-inner">
        <div>
          <span class="eyebrow on-dark">{t("Підтримка", "Support")}</span>
          <h2>{t("Підтримайте Рідну Школу", "Support Ridna Shkola")}</h2>
          <p class="lang-uk">Оплата за навчання є другорядною вимогою: школа допомагає родинам із матеріальними труднощами та дітям, чиї батьки воюють або загинули, захищаючи Україну. Ваша пожертва робить це можливим.</p>
          <p class="lang-en">Tuition is never a barrier: the school helps families in financial need and the children of parents serving or fallen in defense of Ukraine. Your donation makes that possible.</p>
        </div>
        <div class="donate-actions">
          <a class="btn btn-gold" href="{PAYPAL}" rel="noopener"><span>{t("Пожертвувати через PayPal", "Donate with PayPal")}</span>{ICONS['arrow']}</a>
          <a class="btn btn-glass" href="registration.html#help"><span>{t("Допомога з оплатою", "Help with tuition")}</span>{ICONS['arrow']}</a>
        </div>
      </div>
    </div>
  </div>
</section>
"""
    return hero + strip + about + levels + newsec + day + matura + donate


# ---------------------------------------------------------------- about
def about():
    body = page_head("Про школу", "About", "Вітаємо в Рідній Школі", "Welcome to Ridna Shkola",
                     "Школа Українознавства Товариства «Рідна Школа» в Детройті відзначила своє 75-ліття у 2026 році.",
                     "The School of Ukrainian Language and Culture of the Ridna Shkola Society in Detroit celebrated its 75th anniversary in 2026.")
    body += f"""
<section class="section">
  <div class="wrap split wide-left">
    <div class="measure">
      <div class="lang-uk">
        <p>Вже понад 75 років школа українознавства «Рідна Школа» м. Детройту обігріває своєю любов’ю не одне покоління українців на американській землі. Саме тут батьки довіряють нашим вчителям найдорожче: своїх дітей, їхнє майбутнє, у надійні руки досвідчених педагогів, котрі вміло навчають їх рідної мови, культури, історії та національних надбань народу.</p>
        <blockquote class="quote">«Метою школи українознавства є і буде забезпечення систематичного виховання молоді поза Україною, а також збереження її від процесу денаціоналізації та навчити її бути українцями на чужині».<cite>М. Дольницький та І. Білоус, першозасновники школи</cite></blockquote>
        <p>Ця мета залишається спільною для сучасних і наступних поколінь батьків, вчителів та діячів школи. Бо, за словами педагога К. Ушинського, мова є найживіший, найбагатший і найміцніший зв’язок, що з’єднує покоління народу в одне велике історичне живе ціле.</p>
        <p>І сьогодні, коли наші брати і сестри відвойовують українську суверенність, нам усім необхідно усвідомити нашу роль у цих історичних подіях. Бо де, як не в школі українознавства, діти з ранніх літ вчаться розуміти красу рідного слова, пошану до історичного минулого, виховуються патріотами Рідного Краю. Але без родини, без підтримки батьків, школа не доб’ється того результату, на який покладає надії кожний учитель. Школа чекає на співпрацю. Тільки разом ми виховаємо наших дітей справжніми українцями.</p>
        <p><strong>Дирекція Рідної Школи м. Детройту</strong></p>
      </div>
      <div class="lang-en">
        <p>For more than 75 years, Ridna Shkola in Detroit has welcomed generation after generation of Ukrainian American children. Parents entrust their children to experienced teachers who pass on the Ukrainian language, culture, history and national heritage.</p>
        <blockquote class="quote">"The purpose of the School of Ukrainian Studies is, and will remain, to give young people outside Ukraine a systematic upbringing, to guard them from losing their national identity, and to teach them to be Ukrainian abroad."<cite>M. Dolnytsky and I. Bilous, founders of the school</cite></blockquote>
        <p>That purpose is shared by today's parents, teachers and volunteers, and by those who will follow. Language, as the educator K. Ushynsky wrote, is the living bond that joins past, present and future generations of a people into one whole.</p>
        <p>Today, as Ukraine defends its sovereignty, each of us has a part to play. Nowhere else do children learn from an early age to love their native word, respect their history and grow up as patriots of their homeland. But the school cannot succeed without families: we count on parents as partners. Only together will we raise our children as true Ukrainians.</p>
        <p><strong>The Administration of Ridna Shkola, Detroit</strong></p>
      </div>
    </div>
    <div>
      <div class="panel">
        <h3>{t("Коротко про школу", "At a glance")}</h3>
        <ul class="fact-list" style="color:inherit">
          <li><b>1951</b><span>{t("Рік заснування; 75-ліття відзначено у 2026 році", "Founded; 75th anniversary celebrated in 2026")}</span></li>
          <li><b>{t("Класи", "Grades")}</b><span>{t("Дошкілля, 1–11 клас; у 11 класі учні складають матуру", "Preschool and grades 1–11; grade 11 sits the matura exams")}</span></li>
          <li><b>{t("Предмети", "Subjects")}</b><span>{t("Українська мова, література, історія, географія, народознавство, культура", "Ukrainian language, literature, history, geography, folk studies, culture")}</span></li>
          <li><b>{t("Мережа", "Network")}</b><span>{t("Школа працює за вимогами Шкільної Ради при УККА", "A member school of the Ukrainian Education Council (UCCA)")}</span></li>
          <li><b>{t("Де", "Where")}</b><span>{t("Воррен, Мічиган (передмістя Детройта)", "Warren, Michigan (metro Detroit)")}</span></li>
        </ul>
      </div>
      <div class="panel" style="margin-top:1.25rem">
        <h3>{t("Педагогічний колектив", "Our teachers")}</h3>
        <img src="assets/img/teachers.jpg" alt="Учителі Школи Українознавства «Рідна Школа» м. Детройту" width="1024" height="819" loading="lazy" style="border-radius:8px">
        <p class="small muted" style="margin:0.75rem 0 0">{t("Контакти учителів: див. сторінку", "Teacher contacts: see the")} <a href="contact.html">{t("Контакт", "Contact page")}</a>.</p>
      </div>
    </div>
  </div>
</section>
"""
    return body


# ---------------------------------------------------------------- parents
def parents():
    body = page_head("Батькам", "Parents", "Для батьків", "For parents",
                     "Усе, що потрібно для початку шкільного року 2026–27: форми, підручники, приладдя та правила.",
                     "Everything you need for the 2026–27 school year: forms, textbooks, supplies and the rules.")
    body += f"""
<section class="section">
  <div class="wrap">
    <div class="notice" style="margin-bottom:2rem">{ICONS['info']}<div>
      <strong class="lang-uk">Реєстрація на 2026–27 шкільний рік відкрита.</strong><strong class="lang-en">Registration for the 2026–27 school year is open.</strong>
      <span class="lang-uk"> Заповніть онлайн-форму або завантажте паперову форму нижче. Підписаний правильник подається разом із реєстрацією.</span><span class="lang-en"> Fill in the online form or download the paper form below. The signed handbook form is submitted with registration.</span>
      <a href="registration.html">{t("Перейти до реєстрації →", "Go to registration →")}</a>
    </div></div>

    <div class="panel-grid">
      <div class="panel">
        <h3>{t("Форми та документи", "Forms and documents")}</h3>
        <ul class="file-list">
          {file_item(UPLOADS + "2026/09/Реєстрація-на-2026-27-рік-форма-оплата.docx", t("Реєстраційна форма 2026–27 (з оплатою)", "Registration form 2026–27 (with payment)"), "Word · заповнюється на кожну дитину", "Word · one per child")}
          {file_item(UPLOADS + "2026/09/Правила-учнів-2026-2027.docx", t("Правила учнів 2026–2027", "Student rules 2026–2027"), "Word · читати разом із дитиною", "Word · read together with your child")}
          {file_item(UPLOADS + "2011/09/Правильник-для-шкільногрхіву.pdf", t("Правильник: форма для підпису батьків та учня", "Handbook: signature form for parent and student"), "PDF · здається до шкільного архіву", "PDF · returned to the school office")}
        </ul>
        <p class="small muted" style="margin:1rem 0 0"><span class="lang-uk">Повний текст правил доступний онлайн на сторінці</span><span class="lang-en">The full rules are available online on the</span> <a href="handbook.html">{t("Шкільний правильник", "Student handbook page")}</a>.</p>
      </div>
      <div class="panel">
        <h3>{t("Після реєстрації", "After registering")}</h3>
        <ol style="padding-left:1.2rem;margin:0;display:grid;gap:0.5rem">
          <li>{t("Перегляньте список підручників для класу вашої дитини (нижче).", "Check the textbook list for your child's grade (below).")}</li>
          <li>{t("Підготуйте шкільне приладдя за списком на 2026–27 рік.", "Prepare school supplies from the 2026–27 list.")}</li>
          <li>{t("Перевірте календар: перший день школи — перша субота після Дня Праці.", "Check the calendar: the first school day is the Saturday after Labor Day.")}</li>
          <li>{t("Щотижня перевіряйте домашні завдання на сайті.", "Check homework on the site every week.")}</li>
        </ol>
        <div style="display:flex;flex-wrap:wrap;gap:0.6rem;margin-top:1.25rem">
          <a class="btn btn-blue" href="calendar.html">{t("Календар", "Calendar")}</a>
          <a class="btn btn-line" href="homework.html">{t("Домашні завдання", "Homework")}</a>
        </div>
      </div>
    </div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2>{t("Підручники та приладдя", "Textbooks and supplies")}</h2>
    <div class="panel-grid">
      <figure class="doc">
        <img src="assets/img/books-2026-27.png" alt="Список підручників на 2026–27 навчальний рік по класах" width="538" height="958" loading="lazy">
        <figcaption>{t("Список підручників на 2026–27 навчальний рік (по класах).", "Required textbooks for 2026–27, by grade.")} <a href="{UPLOADS}2026/09/Список-підручників-на-2026-2027-навчальний-рік.png" rel="noopener">{t("Відкрити у повному розмірі", "Open full size")}</a></figcaption>
      </figure>
      <figure class="doc">
        <img src="assets/img/supplies-2026-27.png" alt="Список шкільного приладдя для учня Рідної Школи на 2026–27 рік" width="725" height="977" loading="lazy">
        <figcaption>{t("Шкільне приладдя для учня Рідної Школи, 2026–27.", "School supplies for a Ridna Shkola student, 2026–27.")} <a href="{UPLOADS}2026/08/Шкільне-приладдя-2026-27.JPG-2.png" rel="noopener">{t("Відкрити у повному розмірі", "Open full size")}</a></figcaption>
      </figure>
    </div>
  </div>
</section>
"""
    return body


# ---------------------------------------------------------------- registration
def registration():
    body = page_head("Реєстрація", "Registration", "Реєстрація та оплата", "Registration and payments",
                     "Зареєструйте дитину на 2026–27 навчальний рік онлайн. Паперова форма та інформація про оплату — нижче.",
                     "Register your child for the 2026–27 school year online. The paper form and tuition details are below.")
    body += f"""
<section class="section">
  <div class="wrap split wide-left">
    <div>
      <h2>{t("Онлайн-форма реєстрації", "Online registration form")}</h2>
      <div class="embed">
        <iframe src="{REG_FORM_EMBED}" title="Форма реєстрації Рідної Школи (Google Forms)" loading="lazy" style="min-height:900px"></iframe>
        <div class="embed-note">{t("Форма не відкривається?", "Form not loading?")} <a href="{REG_FORM}" rel="noopener">{t("Відкрити її у новому вікні", "Open it in a new window")}</a>.</div>
      </div>
    </div>
    <div>
      <div class="panel">
        <h3>{t("Паперова форма", "Paper form")}</h3>
        <ul class="file-list">
          {file_item(UPLOADS + "2026/09/Реєстрація-на-2026-27-рік-форма-оплата.docx", t("Реєстрація на 2026–27 рік: форма та оплата", "Registration 2026–27: form and payment"), "Word", "Word")}
          {file_item(UPLOADS + "2026/09/Правила-учнів-2026-2027.docx", t("Правила учнів 2026–2027 (підписати)", "Student rules 2026–2027 (to sign)"), "Word", "Word")}
        </ul>
      </div>
      <figure class="doc" style="margin-top:1.25rem">
        <img src="assets/img/registration-form-2026-27.jpg" alt="Реєстраційна форма та оплата на 2026–27 рік" width="791" height="1024" loading="lazy">
        <figcaption>{t("Реєстраційна форма з інформацією про оплату, 2026–27.", "Registration form with tuition information, 2026–27.")}</figcaption>
      </figure>
      <div class="panel" id="help" style="margin-top:1.25rem">
        <h3>{t("Допомога з оплатою", "Help with tuition")}</h3>
        <p class="lang-uk small">Оплата за навчання є другорядною вимогою. Рідна Школа завжди готова допомогти родинам, котрі мають матеріальні труднощі, та надає допомогу учням, батьки яких воюють, воювали у ЗСУ чи загинули, захищаючи Батьківщину. Звертайтесь до дирекції.</p>
        <p class="lang-en small">Tuition should never stop a child from attending. The school supports families in financial need and the children of parents who serve, served, or died defending Ukraine. Please speak with the administration.</p>
        <a class="btn btn-line" href="contact.html">{t("Контакт", "Contact")}</a>
      </div>
    </div>
  </div>
</section>
"""
    return body


# ---------------------------------------------------------------- homework
def homework_page():
    weeks = homework["weeks"]
    tabs = "".join(
        f'<button type="button" role="tab" id="tab-{w["iso"]}" aria-controls="week-{w["iso"]}" aria-selected="{"true" if i == 0 else "false"}">{t(date_uk(w["iso"]), date_en(w["iso"]))}</button>'
        for i, w in enumerate(weeks)
    )
    panels = []
    for i, w in enumerate(weeks):
        classes = []
        for row in w["rows"]:
            links = "".join(f'<a href="{esc(l["u"])}" rel="noopener">{esc(l["t"])}</a>' for l in row["links"])
            label = row["cls"] + ("." if row["cls"].endswith("кл") else "")
            classes.append(f'<div class="hw-class"><h3>{esc(label)}</h3><div class="hw-links">{links}</div></div>')
        panels.append(
            f'<h2 class="week-heading">{t(date_uk(w["iso"]), date_en(w["iso"]))}</h2>'
            f'<div class="week-panel" id="week-{w["iso"]}" role="tabpanel" aria-labelledby="tab-{w["iso"]}">{"".join(classes)}</div>'
        )
    body = page_head("Домашні завдання", "Homework", "Завдання 2026–27, триместр 1", "Homework 2026–27, trimester 1",
                     "Оберіть суботу, щоб побачити завдання для кожного класу. Усі файли відкриваються у форматі PDF.",
                     "Pick a Saturday to see the assignments for every class. All files open as PDFs.")
    body += f"""
<section class="section">
  <div class="wrap">
    <div class="week-tabs" role="tablist" aria-label="Тиждень / Week">{tabs}</div>
    {"".join(panels)}
    <p class="small muted" style="margin-top:1.5rem">{t("Завдання за 2-й і 3-й триместри з’являться тут після початку відповідного триместру.", "Trimester 2 and 3 assignments will appear here once each trimester begins.")}
    <a href="{OLD_SITE}" rel="noopener">{t("Архів попередніх років", "Archive of previous years")}</a>.</p>
  </div>
</section>
"""
    return body


# ---------------------------------------------------------------- calendar
def calendar_page():
    body = page_head("Календар", "Calendar", "Шкільний календар 2026–27", "School calendar 2026–27",
                     "Навчальні суботи, свята та вихідні. Зміни через погоду чи інші причини дирекція повідомляє електронною поштою та на Facebook.",
                     "School Saturdays, holidays and breaks. Weather or other closures are announced by email and on Facebook.")
    body += f"""
<section class="section">
  <div class="wrap split wide-left">
    <div>
      <div class="embed">
        <iframe src="{CALENDAR_EMBED}&mode=MONTH" title="Google Calendar: Рідна Школа, місяць" loading="lazy" style="min-height:640px"></iframe>
        <div class="embed-note">{t("Якщо календар не відображається,", "If the calendar does not load,")} <a href="https://calendar.google.com/calendar/u/0/embed?src={CALENDAR_ID}" rel="noopener">{t("відкрийте його в Google Calendar", "open it in Google Calendar")}</a>. {t("Додати до свого календаря:", "Add to your own calendar:")} <a href="https://calendar.google.com/calendar/ical/{CALENDAR_ID}/public/basic.ics" rel="noopener">iCal</a>.</div>
      </div>
    </div>
    <div>
      <figure class="doc">
        <img src="assets/img/calendar-2026-27.png" alt="Шкільний календар Рідної Школи на 2026–27 рік (оновлений 19 вересня 2026)" width="723" height="848">
        <figcaption>{t("Календар на 2026–27 рік, оновлено 19 вересня 2026.", "2026–27 calendar, updated September 19, 2026.")} <a href="{UPLOADS}2026/09/Календар-оновлений-9-19-2026.png" rel="noopener">{t("Відкрити у повному розмірі", "Open full size")}</a></figcaption>
      </figure>
      <div class="panel" style="margin-top:1.25rem">
        <h3>{t("Шкільний рік", "The school year")}</h3>
        <p class="small lang-uk">Згідно з вимогами Шкільної Ради при УККА, шкільний рік складається з 33 днів навчання. Він починається в першу суботу після американського Дня Праці та закінчується в першу чи другу суботу червня.</p>
        <p class="small lang-en">Per the Ukrainian Education Council (UCCA), the school year has 33 school days. It begins on the first Saturday after Labor Day and ends on the first or second Saturday in June.</p>
      </div>
    </div>
  </div>
</section>
"""
    return body


# ---------------------------------------------------------------- exams
SUBJECT_EN = {"ГЕОГРАФІЯ": "Geography", "ІСТОРІЯ": "History", "КУЛЬТУРА": "Culture", "ЛІТЕРАТУРА": "Literature", "МОВА": "Language"}
SUBJECT_UK = {"ГЕОГРАФІЯ": "Географія", "ІСТОРІЯ": "Історія", "КУЛЬТУРА": "Культура", "ЛІТЕРАТУРА": "Література", "МОВА": "Мова"}
SUBJECT_ORDER = ["МОВА", "ЛІТЕРАТУРА", "ІСТОРІЯ", "ГЕОГРАФІЯ", "КУЛЬТУРА"]


def exams_page():
    years = sorted(exams, reverse=True)
    latest = years[0]
    featured = "".join(
        f'<a href="{esc(exams[latest][s])}" rel="noopener">{t(SUBJECT_UK[s], SUBJECT_EN[s])}<small>{latest}</small></a>'
        for s in SUBJECT_ORDER if s in exams[latest]
    )
    rows = []
    for i, y in enumerate(years[1:]):
        links = "".join(
            f'<a href="{esc(exams[y][s])}" rel="noopener">{t(SUBJECT_UK[s], SUBJECT_EN[s])}</a>'
            for s in SUBJECT_ORDER if s in exams[y]
        )
        rows.append(f'<details class="exam-year"{" open" if i < 2 else ""}><summary>{t("Матура " + y, "Matura " + y)}</summary><div class="exam-links">{links}</div></details>')
    body = page_head("Матура", "Final exams", "Матура / письмові іспити", "Matura / written final exams",
                     "Архів письмових матуральних іспитів з мови, літератури, історії, географії та культури для підготовки випускників.",
                     "An archive of written matura exams in language, literature, history, geography and culture, for graduating students to practise with.")
    body += f"""
<section class="section">
  <div class="wrap">
    <h2>{t("Іспити " + latest, latest + " exams")}</h2>
    <div class="exam-featured">{featured}</div>
    <h2>{t("Попередні роки", "Previous years")}</h2>
    {"".join(rows)}
    <p class="small muted" style="margin-top:1.5rem">{t("Матуральні вимоги Шкільної Ради:", "Matura requirements from the Ukrainian Education Council:")} <a href="http://ridnashkola.org/final_exams/" rel="noopener">ridnashkola.org/final_exams</a></p>
  </div>
</section>
"""
    return body


# ---------------------------------------------------------------- lessons
LITERATURE = [
    ("Енеїда", "Іван Котляревський", "https://www.youtube.com/watch?v=wsIiVU6bmHw"),
    ("Лісова пісня", "Леся Українка", "https://www.youtube.com/watch?v=ZK8ub77Y5HI"),
    ("Гайдамаки", "Тарас Шевченко", "https://www.youtube.com/watch?v=oRNkz9RNt5Q"),
    ("Катерина", "Тарас Шевченко", "https://www.youtube.com/watch?v=68o7MvOsCD0"),
    ("Чорна рада", "Пантелеймон Куліш", "https://www.youtube.com/watch?v=dN6PUIH9Hqo"),
    ("Тигролови", "Іван Багряний", "https://www.youtube.com/watch?v=mnFR8w93_RI"),
    ("Інститутка", "Марко Вовчок", "https://www.youtube.com/watch?v=9l8ZGtCWbLw"),
    ("Маруся Чурай", "Ліна Костенко", "https://www.youtube.com/watch?v=3hjQAJXDVvo"),
    ("Слово о полку Ігоревім", "невідомий автор", "https://www.youtube.com/watch?v=rCmfVcEqlR4"),
]


def grouped(items, default_group):
    groups = {}
    order = []
    for it in items:
        g = it["group"] or default_group
        if g not in groups:
            groups[g] = []
            order.append(g)
        groups[g].append(it)
    return [(g, groups[g]) for g in order]


def lesson_list(items):
    items = [it for it in items if "dropbox.com" not in it["u"]]  # linked once at the top of the section
    return '<ul class="lesson-list">' + "".join(
        f'<li><a href="{esc(it["u"])}" rel="noopener">{esc(it["t"])}</a></li>' for it in items
    ) + "</ul>"


def lessons_page():
    culture_groups = grouped(lessons["culture"], "Культура")
    history_groups = grouped(lessons["history"], "Історія")
    culture_html = "".join(f'<div class="lesson-group"><h3>{esc(g)}</h3>{lesson_list(items)}</div>' for g, items in culture_groups)
    history_html = "".join(f'<div class="lesson-group"><h3>{esc(g)}</h3>{lesson_list(items)}</div>' for g, items in history_groups)
    lit = '<ul class="lesson-list">' + "".join(
        f'<li>{ICONS["play"]} <a href="{esc(u)}" rel="noopener">{esc(title)}</a> <span class="muted">· {esc(author)}</span></li>'
        for title, author, u in LITERATURE
    ) + "</ul>"
    body = page_head("Навчальні матеріали", "Resources", "Лекції та матеріали", "Lessons and materials",
                     "Лекції з культури та історії України у форматі PDF, а також аудіокниги з української літератури.",
                     "Culture and history lectures as PDFs, plus audiobooks of Ukrainian literature.")
    body += f"""
<section class="section">
  <div class="wrap">
    <div class="quick-grid" style="margin-bottom:2.5rem">
      <a class="quick" href="#culture"><span class=\"tile\">{ICONS['book']}</span><span><strong>{t("Культура", "Culture")}</strong><span class="desc">{t("Лекції для 8–11 класів", "Lectures for grades 8–11")}</span></span></a>
      <a class="quick" href="#history"><span class=\"tile\">{ICONS['book']}</span><span><strong>{t("Історія", "History")}</strong><span class="desc">{t("Лекції для 7–8 класів", "Lectures for grades 7–8")}</span></span></a>
      <a class="quick" href="#literature"><span class=\"tile\">{ICONS['play']}</span><span><strong>{t("Література", "Literature")}</strong><span class="desc">{t("Аудіокниги шкільної програми", "Audiobooks from the curriculum")}</span></span></a>
      <a class="quick" href="exams.html"><span class=\"tile\">{ICONS['award']}</span><span><strong>{t("Матура", "Final exams")}</strong><span class="desc">{t("Письмові іспити 2007–2025", "Written exams 2007–2025")}</span></span></a>
    </div>
    <h2 id="culture">{t("Лекції: культура", "Lessons: culture")}</h2>
    <p class="small muted">{t("Ці лекції також доступні у форматі PowerPoint:", "These lectures are also available as PowerPoint files:")} <a href="https://www.dropbox.com/sh/0bujc2vksqqsp7e/AACJj03YHC5Cn3kVMV0WDNgSa?dl=0" rel="noopener">Dropbox</a></p>
    <div class="lesson-cols">{culture_html}</div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2 id="history">{t("Лекції: історія", "Lessons: history")}</h2>
    <div class="lesson-cols">{history_html}</div>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <h2 id="literature">{t("Література: аудіокниги", "Literature: audiobooks")}</h2>
    <p class="small muted">{t("Твори шкільної програми у виконанні читців, на YouTube.", "Curriculum texts read aloud, on YouTube.")}</p>
    <div class="lesson-cols">{lit}</div>
  </div>
</section>
"""
    return body


# ---------------------------------------------------------------- downloads
def downloads_page():
    body = page_head("Ресурси", "Resources", "Корисні ресурси", "Useful resources",
                     "Бібліотеки, словники та ігри для вивчення української мови, зібрані нашими вчителями.",
                     "Libraries, dictionaries and games for learning Ukrainian, collected by our teachers.")
    items = [
        ("http://www.encyclopediaofukraine.com/default.asp", "Internet Encyclopedia of Ukraine", "Енциклопедія України в Інтернеті (англійською).", "Reference encyclopedia of Ukraine (in English)."),
        ("http://incognita.day.kiev.ua/101-prychyna-liubyty-ukrainu", "«101 причина любити Україну» · газета «День»", "Матеріали про історію, культуру, визначних людей та літературу.", "Articles on history, culture, notable people and literature."),
        ("https://sites.google.com/site/openbookclassic/home/ukraienska-literatura", "Українська література і лектури", "Українська та світова література українською для Kindle, Nook, телефонів і планшетів, безкоштовно.", "Ukrainian and world literature in Ukrainian for Kindle, Nook, phones and tablets, free."),
        ("http://diasporiana.org.ua/", "Diasporiana", "Українська діаспорна література, лектури та часописи у форматі PDF.", "Ukrainian émigré literature, required reading and periodicals as PDFs."),
        ("http://elib.nlu.org.ua/view.html?&id=8673", "Правописний словник Голоскевича (1929)", "Класичний український орфографічний словник.", "The classic Ukrainian orthographic dictionary."),
        ("http://uketeacher.webs.com/grammarhramatyka.htm", "Resources for Ukrainian language teachers", "Граматика та матеріали для вчителів.", "Grammar and materials for teachers."),
        ("http://www.samouchka.com.ua/ukr/", "Самоучка", "Інтерактивні ігри для молодших учнів.", "Interactive games for younger learners."),
        ("http://abetka.ukrlife.org/", "Абетка", "Дитяча сторінка з віршами, казками та іграми.", "Children's page with poems, fairy tales and games."),
        ("https://www.shkilnarada.org/", "Шкільна Рада УККА", "Ukrainian Education Council: програми, вимоги, матура.", "Ukrainian Education Council: curricula, requirements, matura."),
    ]
    lis = "".join(file_item(u, esc(title), uk, en, icon="link") for u, title, uk, en in items)
    body += f"""
<section class="section">
  <div class="wrap">
    <ul class="file-list" style="max-width:52rem">{lis}</ul>
  </div>
</section>
"""
    return body


# ---------------------------------------------------------------- handbook
def handbook_page():
    raw = (BUILD / "handbook.txt").read_text(encoding="utf-8").splitlines()
    lines = [l.strip() for l in raw if l.strip()]
    # drop the page title and the approval line fragments (re-stated below)
    start = next(i for i, l in enumerate(lines) if l.startswith("І. "))
    lines = lines[start:]
    # merge fragments that were split by inline formatting on the old site
    HEADINGS = ("Безпека", "Правила поведінки учнів та наслідки їх порушень")

    def is_heading(l):
        return bool(re.match(r"^(І|ІІ|ІІІ|IV|V)\. ", l)) or l in HEADINGS

    merged = []
    in_list = False
    for l in lines:
        if merged and not is_heading(l) and not is_heading(merged[-1]) and not in_list and (
            l[:1].islower() or l[:1] in ",.;:)»" or not re.search(r"[.!?:;»)]$", merged[-1])
        ):
            merged[-1] = (merged[-1] + " " + l).replace("  ", " ")
            continue
        merged.append(l)
        if l.endswith("заборонено:"):
            in_list = True
        elif in_list and l.endswith(".") and len(l) > 120:
            in_list = False
    sections = []  # (id, title, [blocks])
    cur = None
    for l in merged:
        m = re.match(r"^(І|ІІ|ІІІ|IV|V)\. (.+)$", l)
        if m or l in ("Безпека", "Правила поведінки учнів та наслідки їх порушень"):
            title = m.group(2) if m else l
            cur = (f"s{len(sections) + 1}", title, [])
            sections.append(cur)
            continue
        if l.startswith("З « Правилами") or l.startswith("____") or l.startswith("Підпис"):
            continue
        cur[2].append(l)
    out = []
    toc = []
    for sid, title, blocks in sections:
        toc.append(f'<li><a href="#{sid}">{esc(title)}</a></li>')
        parts = []
        i = 0
        while i < len(blocks):
            b = blocks[i]
            if b.endswith("заборонено:"):
                items = []
                i += 1
                while i < len(blocks) and not re.search(r"[.!?]$", blocks[i]) and len(blocks[i]) < 160:
                    items.append(blocks[i]); i += 1
                parts.append(f"<p>{esc(b)}</p><ul>" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>")
                continue
            parts.append(f"<p>{esc(b)}</p>")
            i += 1
        out.append(f'<h2 id="{sid}">{esc(title)}</h2>' + "".join(parts))
    body = page_head("Правильник", "Handbook", "Шкільний правильник", "Student handbook",
                     "Правила учнів Школи Українознавства Товариства «Рідна Школа». Оновлені та затверджені на педагогічних зборах 31 серпня 2026 року.",
                     "Rules for students of the School of Ukrainian Language and Culture, updated and approved by the faculty on August 31, 2026.")
    body += f"""
<section class="section">
  <div class="wrap split toc-right">
    <article class="handbook measure">
      <p class="lang-en muted">The handbook is published in Ukrainian. Parents and students sign a form confirming they have read it and will follow it, and return the form with registration.</p>
      {"".join(out)}
      <div class="notice" style="margin-top:2rem">{ICONS['info']}<div>
        <span class="lang-uk">Батьки та учень підписують форму ознайомлення з правилами і здають її разом із реєстрацією.</span>
        <span class="lang-en">Parents and the student sign the acknowledgement form and submit it with registration.</span>
        <a href="{UPLOADS}2011/09/Правильник-для-шкільногрхіву.pdf" rel="noopener">{t("Завантажити форму (PDF)", "Download the form (PDF)")}</a>
      </div></div>
    </article>
    <aside class="toc">
      <div class="panel">
        <h3>{t("Зміст", "Contents")}</h3>
        <ol>{"".join(toc)}</ol>
        <p class="small muted" style="margin:1rem 0 0">{t("Word-версія:", "Word version:")} <a href="{UPLOADS}2026/09/Правила-учнів-2026-2027.docx" rel="noopener">{t("Правила учнів 2026–2027", "Student rules 2026–2027")}</a></p>
      </div>
    </aside>
  </div>
</section>
"""
    return body


# ---------------------------------------------------------------- contact
def contact_page():
    body = page_head("Контакт", "Contact", "Зв’яжіться з нами", "Get in touch",
                     "Шкільне бюро працює щосуботи під час навчання. Найшвидше нас можна знайти на Facebook або електронною поштою.",
                     "The school office is open on Saturdays during classes. Facebook and email are the fastest ways to reach us.")
    body += f"""
<section class="section">
  <div class="wrap split even">
    <div>
      <span class="eyebrow">{t("Наша школа", "Our school")}</span>
      <h2 style="margin-top:.75rem">{t("Завітайте до нас у Воррен", "Visit us in Warren")}</h2>
      <p class="lead lang-uk">Ми навчаємося щосуботи під час шкільного року у Воррені, штат Мічиган, неподалік Детройта. Зв’яжіться з нами, щоб дізнатися про реєстрацію, допомогу з оплатою чи вільні місця в класах.</p>
      <p class="lead lang-en">We meet every Saturday of the school year in Warren, Michigan, just north of Detroit. Get in touch about registration, tuition help or open places in a class.</p>
      <div class="contact-list">
        <div class="contact-row"><span class="tile">{ICONS['mail']}</span><div><div class="k">{t("Електронна пошта", "Email")}</div><div class="v"><a id="email-text" href="mailto:{EMAIL}">{EMAIL}</a><button class="copy-btn" type="button" data-copy="{EMAIL}" data-done="✓" aria-controls="email-text">{t("Копіювати", "Copy")}</button></div></div></div>
        <div class="contact-row"><span class="tile tile-gold">{ICONS['facebook']}</span><div><div class="k">Facebook</div><div class="v"><a href="{FACEBOOK}" rel="noopener">{t("Школа Українознавства «Рідна Школа» м. Детройт", "Ridna Shkola Detroit")}</a></div><div class="small muted">{t("Оголошення про відміну занять з’являються тут першими.", "Closure announcements are posted here first.")}</div></div></div>
        <div class="contact-row"><span class="tile tile-emerald">{ICONS['clock']}</span><div><div class="k">{t("Коли", "When")}</div><div class="v">{t("Щосуботи, 9:15 – 13:15", "Saturdays, 9:15 am – 1:15 pm")}</div><div class="small muted">{t("Приміщення відкрите з 9:00.", "Doors open at 9:00 am.")}</div></div></div>
        <div class="contact-row"><span class="tile tile-rose">{ICONS['pin']}</span><div><div class="k">{t("Де", "Where")}</div><div class="v">{t("Воррен, Мічиган", "Warren, Michigan")}</div><div class="small muted">{t("За довідками звертайтесь до шкільного бюро.", "For questions, visit the school office.")}</div></div></div>
      </div>
    </div>
    <figure class="doc">
      <img src="assets/img/teachers.jpg" alt="Педагогічний колектив Рідної Школи м. Детройту" width="1024" height="819" loading="lazy">
      <figcaption>{t("Педагогічний колектив Школи Українознавства «Рідна Школа» м. Детройту. Контакти вчителів батьки отримують на початку навчального року.", "The faculty of Ridna Shkola in Detroit. Parents receive teachers' contact details at the start of the school year.")}</figcaption>
    </figure>
  </div>
</section>
"""
    return body


# ---------------------------------------------------------------- build
PAGES = [
    ("index.html", "Головна", "Home", "Школа Українознавства Товариства «Рідна Школа» в Детройті: суботня школа української мови, літератури, історії та культури.", home),
    ("about.html", "Про школу", "About", "Про Школу Українознавства «Рідна Школа» м. Детройту: 75 років навчання української мови та культури.", about),
    ("parents.html", "Для батьків", "For parents", "Форми, підручники, шкільне приладдя та правила для батьків учнів Рідної Школи.", parents),
    ("registration.html", "Реєстрація та оплата", "Registration and payments", "Реєстрація учнів Рідної Школи на 2026–27 навчальний рік та інформація про оплату.", registration),
    ("homework.html", "Домашні завдання", "Homework", "Щотижневі домашні завдання Рідної Школи для кожного класу, триместр 1, 2026–27.", homework_page),
    ("calendar.html", "Календар", "Calendar", "Шкільний календар Рідної Школи на 2026–27 рік.", calendar_page),
    ("exams.html", "Матура", "Final exams", "Архів письмових матуральних іспитів Рідної Школи, 2007–2025.", exams_page),
    ("lessons.html", "Лекції та матеріали", "Lessons and materials", "Лекції з культури та історії України і аудіокниги з літератури.", lessons_page),
    ("downloads.html", "Корисні ресурси", "Useful resources", "Бібліотеки, словники та ігри для вивчення української мови.", downloads_page),
    ("handbook.html", "Шкільний правильник", "Student handbook", "Правила учнів Школи Українознавства «Рідна Школа», затверджені 31 серпня 2026 року.", handbook_page),
    ("contact.html", "Контакт", "Contact", "Як зв’язатися з Рідною Школою в Детройті.", contact_page),
]


def main():
    (ROOT / "assets" / "img" / "favicon.svg").write_text(FAVICON_SVG, encoding="utf-8")
    artifact_dir = None
    if "--artifact" in sys.argv:
        artifact_dir = pathlib.Path(sys.argv[sys.argv.index("--artifact") + 1])
        artifact_dir.mkdir(parents=True, exist_ok=True)
    for slug, uk, en, desc, fn in PAGES:
        doc = layout(slug, uk, en, desc, fn())
        (ROOT / slug).write_text(doc, encoding="utf-8")
        print("wrote", slug, len(doc) // 1024, "KB")
        if artifact_dir:
            if slug == "index.html":
                # Artifact hosts wrap the page in their own skeleton: keep only head links + body content.
                head_bits = re.findall(r'<link rel="stylesheet"[^>]*>', doc)
                inner = re.search(r"<body>(.*)</body>", doc, flags=re.S).group(1)
                art = (f"<title>{esc(uk)} — {SITE_NAME}</title>\n"
                       '<meta name="claude:viewport-fit-sides" content="cover">\n'
                       + "\n".join(head_bits) + "\n" + inner)
                (artifact_dir / "index.html").write_text(art, encoding="utf-8")
            else:
                (artifact_dir / slug).write_text(doc, encoding="utf-8")


if __name__ == "__main__":
    main()
