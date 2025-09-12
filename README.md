
# MPG Reveal.js Theme (Quarto)

A reusable **Quarto + reveal.js** slide template matching the Max Planck (MPG) look: branded title & section slides, teal headings on content slides, an accent bar before headings, footer & logo, and sensible defaults for projectors/fullscreen.

---

## Features

- **Single-source**: write one `.qmd` per deck; Quarto renders HTML slides.
- **Branding baked in** via `mpg.scss`:
  - Full-bleed **title** & **section** backgrounds
  - White, all-caps title/section text positioned over the background art
  - Teal (`#006c66`) headings on normal slides + a small vertical accent bar
  - Optional letterboxed fullscreen (no layout shift in fullscreen)
- **Assets-first** workflow: drop images in `assets/` and reference them.
- Ready for **GitHub Pages**.

---

## Prerequisites

- [Quarto](https://quarto.org/) installed (`quarto --version` to check)
- Git + a GitHub account

---

## Repo layout

```
.
├─ _quarto.yml          # reveal.js config & site settings
├─ mpg.scss             # the theme
├─ slides.qmd           # your deck (add more .qmd files for more decks)
└─ assets/              # logos, backgrounds, images (subfolders OK)
   ├─ logo.svg
   ├─ title_bg.png      # 16:9 background for title slide (e.g., 3840×2160)
   └─ section_bg.png    # 16:9 background for section slides
```

---

## Quick start

1) **Use this template** on GitHub (or clone).  
2) **Run locally**:
```bash
quarto preview
```
3) Edit `slides.qmd` and start writing slides.

---

## `_quarto.yml` (defaults used here)

```yaml
project:
  type: website
  resources:
    - assets/**

format:
  revealjs:
    theme: [default, mpg.scss]
    logo: /assets/logo.svg
    slide-number: true
    footer: "Max Planck Institute of Geoanthropology"
    transition: fade
    controls: true
    toc: false
    code-overflow: wrap

    # Canvas + fullscreen behavior
    width: 1920
    height: 1080
    margin: 0.02
    max-scale: 1     # letterbox on large screens (prevents upscaling)
    # min-scale: 0.5 # allow downscaling on small screens

    # If your Quarto honors it, this disables the auto title slide:
    title-slide: false
```

> Tip: keep the `logo` and image paths **root-relative** (start with `/assets/...`) so they work regardless of where the CSS is emitted.

---

## `slides.qmd` skeleton

```markdown
---
title: "Presentation Title"
subtitle: "Optional Subtitle"
author: "Your Name"
date: today
format: revealjs
---

:::{.title-slide
   background-image="/assets/title_bg.png"
   background-size="cover"         # with 16:9 PNGs, 'cover' fits perfectly
   background-position="right top"}
# PRESENTATION TITLE
<p class="subtitle">Your Institute or Affiliation</p>
:::

---

## Introduction

- Point 1
- Point 2
- Point 3

---

## SECTION TITLE {.section-slide
   background-image="/assets/section_bg.png"
   background-size="cover"
   background-position="center"}

---

## Content Slide

Normal content here. Images go like:
![](/assets/talk-2025/figure1.png)
```

> **Important:** Put **section slide** styling on the **heading** line (`## ... {.section-slide ...}`), not inside a fenced div—otherwise you’ll generate an extra blank slide.

---

## Theme notes (`mpg.scss`)

Already configured to:

- Force **white, all-caps** for title/section headings, positioned over the background art.
- Make **normal slide** headings teal (`#006c66`) and add a small **accent bar** before the text.
- Add reasonable padding to content slides.
- Left-align footer and avoid the hamburger menu overlap.

If you need to tweak positions, adjust these rules (percentages) to match your PNG backgrounds:

```scss
/* Title slide text position */
section.title-slide { position: relative; }
section.title-slide h1 { left: 12%; top: 34%; width: 60%; font-size: 2.4rem; color: #fff; text-transform: uppercase; position: absolute; }
section.title-slide .subtitle { left: 12%; top: 48%; width: 60%; font-size: 1.2rem; color: #fff; position: absolute; }

/* Section slide heading position */
section.section-slide { position: relative; }
section.section-slide h2 { left: 13%; top: 28%; width: 60%; font-size: 2.2rem; color: #fff; text-transform: uppercase; position: absolute; }

/* Normal slides: teal headings + accent bar */
.reveal .slides section:not(.title-slide):not(.section-slide) h1,
.reveal .slides section:not(.title-slide):not(.section-slide) h2,
.reveal .slides section:not(.title-slide):not(.section-slide) h3 { color: #006c66; }

.reveal .slides section:not(.title-slide):not(.section-slide) h1::before,
.reveal .slides section:not(.title-slide):not(.section-slide) h2::before,
.reveal .slides section:not(.title-slide):not(.section-slide) h3::before {
  content: ""; display: inline-block; width: 0.25rem; height: 1em; background: #006c66; margin-right: 0.6rem; vertical-align: middle;
}

/* Content slide padding */
.reveal .slides section { padding: 2.5rem 3rem; }
.reveal .slides section.title-slide,
.reveal .slides section.section-slide { padding: 0; }

/* Footer left-aligned and clear of hamburger */
.reveal .footer { text-align: left !important; margin-left: 3rem; }
```

---

## Multiple decks in one repo

- Add more `.qmd` files next to `slides.qmd` (e.g., `talk-2025.qmd`).
- Quarto renders each to its own page:
  - `/slides.html`
  - `/talk-2025.html`

Organize images with subfolders inside `assets/` (e.g., `assets/talk-2025/...`).

---

## Publish to GitHub Pages

### Option A — one command

```bash
quarto publish gh-pages
```

### Option B — GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish Quarto site
on:
  push:
    branches: [ "main" ]
  workflow_dispatch:

jobs:
  build-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: quarto-dev/quarto-actions/setup@v2
      - uses: quarto-dev/quarto-actions/render@v2
        with:
          to: revealjs
      - uses: quarto-dev/quarto-actions/publish@v2
        with:
          target: gh-pages
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Then in GitHub → **Settings → Pages** → Source: **GitHub Actions**.


---

## Troubleshooting

- **Logo/Background 404s**  
  Ensure `_quarto.yml` has:
  ```yaml
  project:
    resources:
      - assets/**
  ```
  Use `/assets/...` paths. Delete `_site/` and re-render.

- **Duplicate or clipped backgrounds**  
  Set backgrounds **only** via QMD slide attributes. Don’t also set them in CSS.

- **Blank slide before a section slide**  
  You used a fenced div and a `##` heading inside it. Put the class on the `##` heading line instead.

- **Title slides shift in fullscreen**  
  Keep 16:9 (`width: 1920`, `height: 1080`), avoid `vh` in CSS, and use `%` offsets relative to the slide.  
  For no scaling on big displays, set `max-scale: 1` for letterboxing.

---

## Reusing this as a template

On GitHub: **Settings → Template repository**.  
Colleagues can click **Use this template** to start a new deck with all branding pre-wired.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.


---

Questions or tweaks? Open an issue or PR.