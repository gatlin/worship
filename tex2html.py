#!/usr/bin/env python3
"""Convert a worship .tex file to semantic HTML."""

import html
import re
import sys
from pathlib import Path

# \Melody{...} ABC notation is pulled out of the body *before* the global
# text passes (dashes, italics, indent post-pass) so none of them can mangle
# it, then re-emitted at the very end.  Sentinels survive every other step.
_MEL_SENTINEL = "@@WORSHIP_MEL_{n}@@"


def _balanced_brace(text: str, open_idx: int) -> int:
    """Given the index of an opening '{', return the index just past its
    matching close brace.  A backslash escapes the following character so an
    ABC body that contains a literal '}' (staves) does not end the macro
    early.  Returns -1 if unbalanced."""
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def _extract_melodies(body: str):
    """Replace every \\Melody{ABC} with a sentinel; return (body, [abc...]).

    ABC notation often spans many lines and legitimately contains '}' for
    staves, so a naive [^}]* regex cannot find its end.  We locate the macro,
    then brace-balance to find the true close.
    """
    melos: list[str] = []
    out: list[str] = []
    i = 0
    needle = "\\Melody{"
    while True:
        j = body.find(needle, i)
        if j == -1:
            out.append(body[i:])
            break
        out.append(body[i:j])
        open_idx = j + len(needle) - 1          # the opening '{'
        end = _balanced_brace(body, open_idx)
        if end == -1:
            raise ValueError("\\Melody{ is not brace-balanced (missing '}')")
        melos.append(body[open_idx + 1 : end - 1])
        out.append(_MEL_SENTINEL.format(n=len(melos) - 1))
        i = end
    return "".join(out), melos


def _emit_melody(abc: str, idx: int) -> str:
    """HTML for one \\Melody.  The raw ABC is kept as hidden-but-kept source
    (visible fallback if ABC.js is absent or parsing fails, so a bad line is
    always readable rather than a blank gap); the rendered SVG replaces it in
    place once ABC.js succeeds."""
    esc = html.escape(abc)
    out_id = f"melout_{idx}"
    return (
        f'\n<div class="melody">\n'
        f'<pre class="melody-abc" data-out="{out_id}">\n{esc}\n</pre>\n'
        f'<div id="{out_id}" class="abcjs"></div>\n'
        f'</div>\n'
    )


_MEL_SCRIPT = """

<script>
(function () {
  document.documentElement.classList.add('js');
  if (typeof ABCJS === 'undefined') { return; }   // offline / not loaded: source stays visible
  document.querySelectorAll('.melody-abc').forEach(function (src) {
    var out = document.getElementById(src.getAttribute('data-out'));
    if (!out) { return; }
    try {
      // ABC.js: `responsive: true` sets a sane intrinsic width and lets the
      // SVG scale to its container via viewBox.  Do NOT pass `scale` (it is
      // treated as a literal transform multiplier and will blow the staff
      // up by N-fold) or `staffwidth` unless you specifically want to cap it.
      ABCJS.renderAbc(out, src.textContent, {}, { responsive: true });
      var m = src.closest('.melody');
      if (m) { m.classList.add('rendered'); }
    } catch (e) {
      /* leave the readable ABC source on screen */
    }
  });
})();
</script>
"""


def _restore_melodies(body: str, melos: list[str]) -> str:
    if not melos:
        return body
    for idx, abc in enumerate(melos):
        body = body.replace(_MEL_SENTINEL.format(n=idx), _emit_melody(abc, idx))
    # One render script per page.  (convert() runs once per page, before
    # wrap_html, so nothing else has injected it yet.)
    body = body.rstrip() + "\n" + _MEL_SCRIPT
    return body


def extract_body(tex: str) -> str:
    """Extract content between \\begin{document} and \\end{document}."""
    m = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', tex, re.DOTALL)
    if not m:
        raise ValueError("No \\begin{document}...\\end{document} found")
    return m.group(1)


def convert(body: str) -> str:
    """Apply all macro substitutions and return HTML body."""

    # \Melody holds raw ABC, which the text passes below would corrupt
    # (the \textit{} pass would treat a staff as a macro, dashes become
    # em-dashes, etc.).  Pull it out first; restore after we're done.
    body, melos = _extract_melodies(body)

    # --- Strip LaTeX comment lines (lines whose first non-ws char is %) ---
    body = '\n'.join(
        line for line in body.split('\n')
        if not line.lstrip().startswith('%')
    )

    # --- Environments (wrap content) ---
    body = re.sub(
        r'\\begin\{Litany\}(.*?)\\end\{Litany\}',
        r'<div class="litany">\1</div>',
        body, flags=re.DOTALL,
    )
    body = re.sub(
        r'\\begin\{Psalm\}\{([^}]*)\}(.*?)\\end\{Psalm\}',
        r'<div class="psalm"><p class="psalm-ref">\1</p>\2</div>',
        body, flags=re.DOTALL,
    )

    # --- \Indent: replace with a sentinel, resolve in post-pass ---
    body = body.replace('\\Indent', '\x00INDENT\x00')

    # --- Single-argument macros ---
    body = re.sub(r'\\OrderTitle\{([^}]*)\}', r'<h1>\1</h1>\n<div class="title-rule"></div>', body)
    body = re.sub(r'\\OrderSubtitle\{([^}]*)\}', r'<p class="subtitle">\1</p>', body)
    body = re.sub(r'\\Rubric\{([^}]*)\}', r'<p class="rubric">\1</p>', body)
    body = re.sub(r'\\Act\{([^}]*)\}', r'<h2>\1</h2>', body)
    body = re.sub(r'\\L\{([^}]*)\}', r'<p class="leader">\1</p>', body)
    body = re.sub(r'\\P\{([^}]*)\}', r'<p class="people"><strong>\1</strong></p>', body)
    body = re.sub(r'\\Reading\{([^}]*)\}', r'<p class="reading"><em>\1</em></p>', body)
    body = re.sub(r'\\V\{([^}]*)\}', r'<p class="verse">\1</p>', body)
    body = re.sub(r'\\Resp\{([^}]*)\}', r'<p class="response"><strong>\1</strong></p>', body)
    body = re.sub(r'\\rub\{([^}]*)\}', r'<span class="rubric-inline"><em>\1</em></span>', body)

    # --- No-argument macros ---
    body = body.replace('\\Silence', '<p class="silence"><em>Silence</em></p>')
    body = body.replace('\\Amen', '<p class="people"><strong>Amen.</strong></p>')
    body = body.replace('\\pt', '<span class="half-line">*</span>')

    # --- Hymn (4 args) ---
    def _hymn_repl(m: re.Match) -> str:
        title, ref, note, info = m.group(1), m.group(2), m.group(3), m.group(4)
        line1 = f'<div class="hymn-line"><em>{title}</em><span class="ref">{ref}</span></div>'
        if note or info:
            line2 = (f'<div class="hymn-line">'
                     f'<span class="hymn-note">{note}</span>'
                     f'<span class="hymn-note">{info}</span></div>')
        else:
            line2 = ''
        return f'<div class="hymn">{line1}{line2}</div>'

    body = re.sub(
        r'\\Hymn\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}\{([^}]*)\}',
        _hymn_repl,
        body,
    )

    # --- Standard LaTeX formatting ---
    body = re.sub(r'\\textit\{([^}]*)\}', r'<em>\1</em>', body)
    body = re.sub(r'\\textbf\{([^}]*)\}', r'<strong>\1</strong>', body)
    body = re.sub(r'\\emph\{([^}]*)\}', r'<em>\1</em>', body)

    # --- Dashes: -- → em-dash ---
    body = body.replace('--', '\u2014')

    # --- Resolve \Indent sentinels: add class="indent" to next block element ---
    lines = body.split('\n')
    result: list[str] = []
    indent_next = False
    for line in lines:
        if '\x00INDENT\x00' in line:
            indent_next = True
            line = line.replace('\x00INDENT\x00', '').strip()
            if not line:
                continue
        if indent_next and line.lstrip().startswith('<'):
            if 'class="' in line:
                line = line.replace('class="', 'class="indent ', 1)
            else:
                line = line.replace('<', '<class="indent" ', 1)
            indent_next = False
        result.append(line)
    body = '\n'.join(result)

    # --- Tidy: collapse 3+ blank lines to 2 ---
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    return _restore_melodies(body, melos)


def wrap_html(body: str, title: str = "Worship") -> str:
    """Wrap the body in a full HTML document."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="style.css">
<script src="abcjs-basic-min.js"></script>
</head>
<body>
{body}
</body>
</html>
'''


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: tex2html.py <input.tex> [output.html]", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.with_suffix('.html')

    tex = input_path.read_text(encoding='utf-8')
    body = extract_body(tex)
    html_body = convert(body)

    # Derive <title> from the first <h1> if present
    title_match = re.search(r'<h1>(.*?)</h1>', html_body)
    title = title_match.group(1) if title_match else input_path.stem

    output_path.write_text(wrap_html(html_body, title), encoding='utf-8')
    print(f"Wrote {output_path}")


if __name__ == '__main__':
    main()
