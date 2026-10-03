# Adding Hymnal Pages with Melody (ABC.js)

This is the state of the worship repo with the `\Melody` macro added. It lets
you author hymnal pages — especially canticles with a sung response line plus
call-and-response text — and render staff notation straight into the HTML that
`make html` already produces.

## What changed

| File | Change |
|------|--------|
| `tex2html.py` | New `\Melody{...}` macro; injects ABC.js `<script>` + a render loop into `wrap_html()` |
| `assets/abcjs-basic-min.js` | Vendored ABC.js v6.7.1 (~500 KB) — no CDN, PWA stays offline |
| `assets/style.css` | `.melody`, `.abcjs`, `.abcjs-src` sizing rules + graceful ABC-as-text fallback |
| `Makefile` | `html`/`docs` auto-include new `.tex` pages and copy `abcjs-basic-min.js` alongside |
| `assets/sw.js` | Bumped cache version to `worship-v2`; ABC.js now cached for offline |
| `canticle.tex` | Starter canticle template (fill in real lyrics/music) |
| `melody-test.tex` | Sanity-check page (excluded from built site by the Makefile) |

## How to add a hymnal page

1. Make a new `.tex` file next to `canticle.tex`, e.g. `umh83.tex`.
2. Use the existing macros:
   - `\Hymn{...}` — tune header (already existed)
   - `\Melody{ ABC NOTATION HERE }` — staff notation. Wrap your ABC in
     single braces. It's balanced-brace parsed, so the `|` and `{}` the ABC
     needs are fine.
   - `\L{...}` / `\P{...}` — leader / people (already existed) — this is what
     does the call-and-response.
3. Run `make html`. Your page appears in `build/`.

## The one ABC.js gotcha

**Use `{ responsive: true }` only.** Do NOT pass `scale:` or `staffwidth:`.
ABC.js v6 interprets `scale` as a literal CSS transform multiplier, not a
percentage — `scale: 10` = 10× zoom, and `max-width:100%` then crushes it to
invisibility. `responsive: true` alone gives a clean SVG that fills the
container and stays at the right ratio.

## Notes

- The ABC in `canticle.tex` and `melody-test.tex` is a **placeholder pattern**
  (a C-major scale, labeled as such), used to prove the pipeline renders a
  real 5-line staff. Replace with the actual UMH setting when you have it.
- Melodies from UMH 83 onward (e.g. UMH 83, Pelquin 6/8) are **copyrighted to
  GIA / the composer**, not public domain. Fine for personal use.
- If you want a plainchant (e.g. UMH 82 *Te Deum* chant), ABC is easy to
  transcribe from any online chant sheet — one voice, no chord stacking.
