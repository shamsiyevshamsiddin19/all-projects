# shamsiyev.uz

Personal portfolio website of **Shamsiddin Shamsiyev** — Backend Developer (Python / Django / FastAPI / PostgreSQL / Docker).

Live: https://shamsiyev.uz

## Stack

- Static **HTML / CSS / vanilla JavaScript** (no framework).
- Fonts via Google Fonts, icons via RemixIcon (CDN).
- Movies page pulls data from the TMDB API.
- Contact form is handled by [FormSubmit](https://formsubmit.co).
- Homepage supports EN / RU / UZ (see `assets/js/i18n.js`).

## Build (minification)

`index.html` loads **minified** assets (`*.min.css` / `*.min.js`). The `.js`/`.css`
files under `assets/` are the source of truth — **after editing them, rebuild the
minified files**:

```bash
npm install   # first time only (installs esbuild)
npm run build # regenerates assets/css/main.min.css and assets/js/*.min.js
```

To avoid stale minified files, set the **Cloudflare Pages build command** to
`npm run build` so it rebuilds on every deploy.

## Structure

```
index.html            Home (hero, about, skills, projects, blog, contact)
cv.html / resume.html CV and resume pages
books/movies/sport/travel/ideas.html  Interest pages
assets/css/           Stylesheets
assets/js/            Page scripts (source of truth — edit these directly)
assets/images/        Images
```

## Run locally

```bash
npm start        # serves the folder with `npx serve`
# or simply open index.html in a browser
```

## Deploy

The site is hosted on **Cloudflare Pages**. Pushing to GitHub does **not** update the
live site by itself — a Cloudflare Pages deploy must run.
