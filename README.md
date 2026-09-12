# Timothy A. Myers — academic website

Three-page Quarto website prepared for https://tamyers87.github.io.

## Edit

- `index.qmd`: home page, research themes, selected findings, and recognition.
- `cv.qmd`: academic appointments, education, selected recognition, and contact details.
- `publications.json`: reviewed publication metadata. Edit this to update the full list, then run `python3 scripts/build_publications.py` and `python3 scripts/build_exports.py`.
- `styles.scss`: typography, colors, spacing, and mobile layout.
- `assets/timothy-myers-square.png`: square homepage portrait derived from the author-supplied May 2026 photograph; the original is retained as `assets/timothy-myers.jpg`.
- `files/`: public CV and bibliography downloads.

## Preview and check

Install Quarto from https://quarto.org/docs/get-started/.

```sh
python3 scripts/build_publications.py
quarto render
python3 scripts/check_site.py
quarto preview
```

The publication builders use only Python's standard library. No Python packages are needed. The generated website is in `dist/`.

## Automatic publication checks

The `Check for new publications` GitHub Action runs on the first day of each month and can also be started manually. It reads DOI works from the public ORCID record `0000-0003-0582-4554`, obtains standard citation metadata through DOI content negotiation, and opens a pull request when it finds a new work. Merging that reviewed pull request publishes the update. Existing curated records are never rewritten automatically. Keep the ORCID works list current so the check can discover new publications.

## Publish to GitHub Pages

Create a public repository named `tamyers87.github.io` in the `tamyers87` account, and push this source folder to its `main` branch. Under Settings → Pages → Build and deployment, select **GitHub Actions**. The supplied workflow renders and checks the site before publishing. The first workflow can be started manually from Actions if needed after Pages is enabled.

No custom domain, paid service, tracking, or contact-form backend is required. Source content is public when pushed to a public repository.

## Content and image sources

- Academic biography and publications: the author's October 2025 CV, verified publication metadata, and updates supplied September 10, 2026.
- Current title **Associate Research Scientist** and February 2026 appointment dates follow the author's instructions.
- Ph.D. committee service for **Akarshna Ayer, Hampton University**, supplied by the author.
- New portrait: `PXL_20260521_171041940.jpg`, supplied by the author for this website.
- Scientific figure: Myers et al. (2021), Figure 5, *Nature Climate Change* 11, 501–507, https://doi.org/10.1038/s41558-021-01039-0. Extracted from the author-supplied paper, preserving the axes and legend. Figure compares baseline and updated multiple-lines-of-evidence climate-sensitivity distributions; it is not a raw observational time series.
- Anniversary recognition: “Early-career researchers reflect on influential papers,” *Nature Climate Change* (April 10, 2026), https://www.nature.com/articles/s41558-026-02605-0. The site describes inclusion in the 15th-anniversary retrospective, not a formal award or quantitative ranking.
- 2021 selected finding: https://doi.org/10.1038/s41558-021-01039-0.
- 2023 selected finding: https://doi.org/10.1175/jcli-d-22-0862.1.
- 2018 selected finding: https://doi.org/10.1029/2018gl078242.

The downloadable full CV is the eight-page LaTeX version updated September 12, 2026. It includes the anniversary recognition and the audited lists of invited, contributed oral, and poster presentations.
