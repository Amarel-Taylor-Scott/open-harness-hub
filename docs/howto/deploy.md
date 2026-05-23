# Deploy the hub

The site is **host-agnostic**. The same `mkdocs build` output deploys
unchanged to any of the following.

## GitHub Pages

`.github/workflows/pages.yml` runs `mkdocs build` and publishes
`site/` to the `gh-pages` branch on every push to `main`.

```yaml
# .github/workflows/pages.yml (already in this repo)
```

Set the repo's Pages source to "GitHub Actions" once, then every push
to `main` deploys.

## Hugging Face Spaces

Two flavors:

- **Static** - push the `site/` build to a Hugging Face Space with
  `sdk: static`. The catalog is read-only. Set up via
  `hf-space/README.md` (already has the HF frontmatter).
- **Gradio** - the same Space directory holds `app.py` which exposes
  the live playground. Set `sdk: gradio` in the README frontmatter.

## Vercel

`vercel.json` runs `mkdocs build` and serves `site/`. Connect the repo
in the Vercel dashboard and pick the default settings; no changes
needed.

## Netlify

`netlify.toml` runs `mkdocs build` and serves `site/`. Connect the
repo; defaults work.

## Cloudflare Pages

Set the build command to `mkdocs build` and the publish directory to
`site/`. The `_headers` and `_redirects` files (if present) are
respected automatically.

## Other Docker hosts

The Gradio playground runs in any Docker host. `hf-space/Dockerfile`
is portable; build and push it anywhere.
