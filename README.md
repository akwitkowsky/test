# Рідна Школа · Детройт — website (2026 redesign)

A modern, static, bilingual (Ukrainian first, English toggle) website for the
School of Ukrainian Language and Culture of the Ridna Shkola Society in Detroit,
replacing the WordPress "aquablock" theme site at ukrainianschooldetroit.org.

No framework, no build dependencies beyond Python 3. The pages are plain HTML +
one CSS file + one small JS file, so they can be hosted anywhere (GitHub Pages,
Netlify, the current host's `public_html`, …).

## Pages

| File | Content |
|---|---|
| `index.html` | Hero, quick links, latest news, about blurb, Saturday timetable, Google Calendar agenda, donate |
| `about.html` | Welcome text from the administration, facts, teachers photo |
| `parents.html` | Registration documents, textbook list, school supplies list |
| `registration.html` | Embedded Google Form, paper form, tuition help |
| `homework.html` | Weekly homework PDFs per class, with a week picker (trimester 1, 2026–27) |
| `calendar.html` | Google Calendar (month view), 2026–27 calendar image |
| `exams.html` | Written matura exams 2007–2025 by year and subject |
| `lessons.html` | Culture and history lecture PDFs, literature audiobooks |
| `downloads.html` | External learning resources |
| `handbook.html` | Full student handbook (Правила учнів), with table of contents |
| `contact.html` | Email, Facebook, hours, faculty photo |

## Editing content

Run the generator after any change:

```sh
python3 build/build.py
```

* **Page copy, navigation, timetable, links** → `build/build.py` (each page is a
  small Python function returning HTML; `t("укр", "eng")` emits a bilingual span).
* **News** → `data/news.json` (title, date, local image, link). Put flyer images in
  `assets/img/news/`. The home page shows the six newest entries.
* **Homework** → `data/homework.json` (`weeks[]` → `rows[]` → `links[]`). New
  weeks go at the top. Trimester 2/3 can reuse the same shape.
* **Exams** → `data/exams.json` (`{"2025": {"МОВА": url, …}}`).
* **Lectures** → `data/lessons.json`; literature audiobooks are a list in `build/build.py`.
* **Handbook** → `build/handbook.txt` (plain text; roman-numeral headings start sections).
* **Styles** → `assets/css/style.css` (design tokens at the top; dark mode included).
* **Behaviour** → `assets/js/main.js` (language toggle, mobile menu, week tabs, copy button).

## Migration notes

* PDF/DOCX links still point at the existing WordPress uploads
  (`ukrainianschooldetroit.org/wp-content/uploads/…`). Keep that host alive or
  move the files and update the URLs in `data/*.json` and `build/build.py`.
* News cards link to the original posts on the old site for now.
* The Google Calendar, Google Form and PayPal button reuse the school's existing
  IDs (set at the top of `build/build.py`).
* A street address is deliberately not shown; add it in `contact_page()` and the
  hero card once confirmed.
