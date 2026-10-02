#!/usr/bin/env python3
"""Convert a worship .tex file to semantic HTML."""

import re
import sys
from pathlib import Path


def extract_body(tex: str) -> str:
    """Extract content between \\begin{document} and \\end{document}."""
    m = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', tex, re.DOTALL)
    if not m:
        raise ValueError("No \\begin{document}...\\end{document} found")
    return m.group(1)


def convert(body: str) -> str:
    """Apply all macro substitutions and return HTML body."""

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
    return body


def wrap_html(body: str, title: str = "Worship") -> str:
    """Wrap the body in a full HTML document."""
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="style.css">
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
