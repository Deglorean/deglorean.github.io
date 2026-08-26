# Might Help

**Made because it might help.**

GitHub Pages-ready static website for:

**https://mighthelp.com.au**

## GitHub Pages settings

- Source: **Deploy from a branch**
- Branch: **main**
- Folder: **/docs**
- Custom domain: **mighthelp.com.au**

`docs/` is the complete public site.

`docs/.nojekyll` disables Jekyll processing because the website is already
built as static HTML/CSS/JavaScript.

`docs/CNAME` contains the intended domain, but the custom domain must also be
set under **Repository → Settings → Pages**.

## Local files

- `editor/` — offline editor
- `source/site-data.json` — site content/configuration
- `source/build_site.py` — local builder
- `backups/` — optional local backups

## Search files

The public site includes:

- canonical URLs
- structured data
- Open Graph metadata
- `robots.txt`
- `sitemap.xml`
- custom `404.html`

After launch, verify the domain in GitHub and Google Search Console and submit:

`https://mighthelp.com.au/sitemap.xml`

## Line endings

The repository includes `.gitattributes` to keep website and source text files
stored as LF on every platform. This prevents Windows Git settings from causing
line-ending-only changes while leaving binary files untouched.
