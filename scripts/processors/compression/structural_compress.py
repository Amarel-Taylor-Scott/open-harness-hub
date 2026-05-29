#!/usr/bin/env python3
"""Backs `processor/structural-compress` (process_kind ``compress.structural``).

Repomix / Tree-sitter-style **structural compression**: strip the *bodies* of
functions and methods while KEEPING the structure that a model needs to reason
about a codebase — ``import`` lines, ``class`` / ``def`` (and JS/TS
``function`` / arrow / method) **signatures**, decorators, and (optionally)
the leading docstring of each definition. Bodies collapse to a single elision
marker. On code this yields large, structure-lossless token reductions
(Repomix reports ~70% on real codebases); on prose / unknown text the
compressor **degrades gracefully** and returns the content essentially
unchanged rather than mangling it.

This is the *structural* flavor of the CEaaS "Compressed" tier; it pairs with
the *learned* flavor (LLMLingua-style). See
``docs/strategy/context-enrichment-service.md``.

Runtime contract (matches the manifest + the runtime-routing doc
``docs/architecture/component-execution-and-runtime-routing.md``):

  * ``process_kind = compress.structural`` — CPU pool, deterministic.
  * **deterministic**: same input → byte-identical output. No clocks, no RNG,
    no environment reads, no network, no filesystem writes.
  * **idempotent**: ``run(run(x).compressed)`` is a fixed point for code
    (already-stripped bodies stay stripped) — see the self-test.
  * **side_effects = none**: pure function of its arguments.
  * **on_error = raise**: invalid arguments raise ``TypeError`` /
    ``ValueError``; we never silently swallow.
  * **streaming = false**: whole-content in, whole-content out.

Pure-Python stdlib only (``re`` + ``ast`` for the Python path — ``ast`` is the
correct, well-tested structural parser for Python, far more robust than a
regex; the JS/TS path is a pragmatic brace+indentation heuristic since there
is no stdlib JS parser). No third-party deps, no tree-sitter.

Token proxy (stated explicitly, because the manifest emits token counts):
  Token count is a **deterministic whitespace + punctuation tokenizer** — we
  split on runs of word characters vs. individual non-space punctuation marks
  (see ``count_tokens``). It is a *proxy* for a real BPE tokenizer, chosen
  because it is dependency-free and stable across runs; the ``ratio`` it
  produces tracks real tokenizer savings closely enough to report a tier
  delta, but it is NOT a billing-grade BPE count.

Public API:
    from scripts.processors.compression.structural_compress import run
    out = run(content="...source...", language=None, keep_docstrings=True)
    # -> {"compressed": str, "tokens_in": int, "tokens_out": int,
    #     "ratio": float, "language": str, "definitions_stripped": int}

CLI / self-test:
    python3 scripts/processors/compression/structural_compress.py
    python3 -m scripts.processors.compression.structural_compress
"""
from __future__ import annotations

import ast
import re
from typing import Any

# ── Configuration constants (single source of truth; No-Magic-Values) ────────

#: Marker that replaces an elided function / method body. One line, language
#: agnostic, and crucially **not** itself a definition — so re-running the
#: compressor is a fixed point (idempotent).
BODY_ELISION_MARKER = "..."

#: Languages we structurally compress. Anything else degrades gracefully
#: (returned unchanged). Kept as one set so callers / tests read it, never a
#: parallel literal.
PYTHON_LANG = "python"
JS_TS_LANG = "javascript"  # covers .js/.jsx/.ts/.tsx — same brace heuristic
PLAINTEXT_LANG = "text"
SUPPORTED_CODE_LANGS = frozenset({PYTHON_LANG, JS_TS_LANG})

#: File-extension → language, used only when the caller passes a ``filename``
#: hint. (No filesystem access — purely the string suffix.)
_EXT_TO_LANG = {
    ".py": PYTHON_LANG,
    ".pyi": PYTHON_LANG,
    ".js": JS_TS_LANG,
    ".jsx": JS_TS_LANG,
    ".ts": JS_TS_LANG,
    ".tsx": JS_TS_LANG,
    ".mjs": JS_TS_LANG,
    ".cjs": JS_TS_LANG,
}

#: Token regex: a "token" is either a maximal run of word characters
#: (``\w+`` — letters, digits, underscore) OR a single non-whitespace,
#: non-word character (punctuation/operator). Whitespace is never a token.
#: Deterministic and dependency-free — this is the declared token PROXY.
_TOKEN_RE = re.compile(r"\w+|[^\w\s]")

# ── Token proxy ──────────────────────────────────────────────────────────────


def count_tokens(text: str) -> int:
    """Deterministic proxy token count (whitespace + punctuation split).

    NOT a BPE count — see module docstring. Stable across runs and platforms.
    """
    if not text:
        return 0
    return len(_TOKEN_RE.findall(text))


# ── Language detection ────────────────────────────────────────────────────────


def detect_language(content: str, *, language: str | None, filename: str | None) -> str:
    """Resolve the language to use.

    Priority: explicit ``language`` arg → ``filename`` extension → a light
    content sniff → ``PLAINTEXT_LANG``. Normalizes common aliases
    (``py``/``ts``/``tsx``/…) onto our two code buckets.
    """
    if language:
        norm = language.strip().lower()
        aliases = {
            "py": PYTHON_LANG,
            "python3": PYTHON_LANG,
            "python": PYTHON_LANG,
            "js": JS_TS_LANG,
            "jsx": JS_TS_LANG,
            "ts": JS_TS_LANG,
            "tsx": JS_TS_LANG,
            "javascript": JS_TS_LANG,
            "typescript": JS_TS_LANG,
            "node": JS_TS_LANG,
            "text": PLAINTEXT_LANG,
            "txt": PLAINTEXT_LANG,
            "plaintext": PLAINTEXT_LANG,
        }
        if norm in aliases:
            return aliases[norm]
        # Unknown explicit language → honor caller's intent: don't pretend to
        # parse it; treat as plaintext so we degrade gracefully.
        return PLAINTEXT_LANG

    if filename:
        lower = filename.lower()
        for ext, lang in _EXT_TO_LANG.items():
            if lower.endswith(ext):
                return lang

    # Content sniff (cheap, deterministic). Prefer Python if it parses as
    # Python AND shows Python-shaped defs; otherwise look for JS/TS markers.
    head = content.lstrip()
    looks_python = bool(
        re.search(r"^\s*(def|class)\s+\w+", content, re.MULTILINE)
        or head.startswith("#!") and "python" in head.splitlines()[0].lower()
    )
    if looks_python and _parses_as_python(content):
        return PYTHON_LANG
    looks_js = bool(
        re.search(r"\bfunction\b|=>|\bexport\b|\bconst\b\s+\w+\s*=", content)
        and "{" in content
    )
    if looks_js:
        return JS_TS_LANG
    if looks_python:  # Python-shaped but didn't fully parse (e.g. a fragment)
        return PYTHON_LANG
    return PLAINTEXT_LANG


def _parses_as_python(content: str) -> bool:
    try:
        ast.parse(content)
        return True
    except (SyntaxError, ValueError):
        return False


# ── Python structural compression (AST-driven) ───────────────────────────────


def _python_indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" \t"))]


def compress_python(content: str, *, keep_docstrings: bool) -> tuple[str, int]:
    """Strip Python function/method bodies via the stdlib ``ast``.

    Keeps: imports, ``class`` headers, decorators, full ``def`` / ``async def``
    signature lines (including multi-line signatures), and — when
    ``keep_docstrings`` — each function's leading docstring. Each stripped body
    is replaced by the elision marker at the body's indentation.

    Returns ``(compressed_source, definitions_stripped)``. Raises
    ``SyntaxError`` if the content is not valid Python (the manifest's
    ``on_error = raise`` contract — the caller chose ``language=python``).
    """
    tree = ast.parse(content)
    lines = content.splitlines(keepends=True)

    # Collect (body_start_line, body_end_line, indent, keep_docstring_node)
    # for every function/method. We operate on 1-based inclusive line ranges
    # from the AST and edit from the bottom up so earlier line numbers stay
    # valid.
    edits: list[tuple[int, int, str, ast.stmt | None]] = []

    func_types = (ast.FunctionDef, ast.AsyncFunctionDef)
    for node in ast.walk(tree):
        if not isinstance(node, func_types):
            continue
        body = node.body
        if not body:
            continue

        first_stmt = body[0]
        last_stmt = body[-1]

        # Already-elided body → no-op (keeps the compressor a fixed point /
        # idempotent: re-running produces byte-identical output AND reports
        # zero bodies stripped). A body counts as elided when, after an
        # optional leading docstring, the remainder is exactly a single ``...``
        # (the marker, which parses to an ``Ellipsis`` expression statement).
        remainder = body[1:] if _is_docstring(first_stmt) else body
        if len(remainder) == 1 and _is_ellipsis(remainder[0]):
            continue

        # Indentation of the body = indentation of the first body statement's
        # source line. ``col_offset`` is a byte/char column; rebuild from the
        # actual line so tabs are preserved.
        first_line_idx = first_stmt.lineno - 1
        body_indent = _python_indent(lines[first_line_idx])

        keep_node: ast.stmt | None = None
        if keep_docstrings and _is_docstring(first_stmt):
            keep_node = first_stmt

        # Decide the inclusive 1-based range of *body* lines to replace.
        if keep_node is not None:
            # Keep the docstring; strip everything after it (if anything).
            if len(body) == 1:
                # Body is only a docstring → nothing to strip; leave as is.
                continue
            strip_start = body[1].lineno
        else:
            strip_start = first_stmt.lineno
        strip_end = _stmt_end_line(last_stmt)

        if strip_start > strip_end:
            continue
        edits.append((strip_start, strip_end, body_indent, keep_node))

    # Drop edits fully contained within another (NESTED functions): stripping the
    # OUTERMOST body already elides everything nested inside it, so inner edits are
    # redundant — and, applied to the mutating buffer below (sorted by start), an
    # inner edit shrinks the list and leaves the outer edit's end index stale, which
    # the bounds guard then silently skips → a partially-stripped, NON-IDEMPOTENT
    # result. Keeping only outermost ranges makes run() a true fixed point (the
    # manifest's idempotent=true). Sibling (non-overlapping) bodies are all kept.
    edits = [e for e in edits
             if not any(o is not e and o[0] <= e[0] and e[1] <= o[1] for o in edits)]

    if not edits:
        return content, 0

    # Apply edits bottom-up. Replace the [strip_start, strip_end] line block
    # with a single marker line at the body indent.
    edits.sort(key=lambda e: e[0], reverse=True)
    out_lines = list(lines)
    stripped = 0
    for strip_start, strip_end, indent, _keep in edits:
        s_idx = strip_start - 1
        e_idx = strip_end - 1
        if s_idx < 0 or e_idx >= len(out_lines) or s_idx > e_idx:
            continue
        # Preserve the trailing newline shape of the block being replaced.
        had_trailing_nl = out_lines[e_idx].endswith("\n") or e_idx < len(out_lines) - 1
        replacement = f"{indent}{BODY_ELISION_MARKER}" + ("\n" if had_trailing_nl else "")
        out_lines[s_idx : e_idx + 1] = [replacement]
        stripped += 1

    return "".join(out_lines), stripped


def _is_docstring(stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


def _is_ellipsis(stmt: ast.stmt) -> bool:
    """True for a bare ``...`` statement (the elision marker once parsed)."""
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and stmt.value.value is Ellipsis
    )


def _stmt_end_line(stmt: ast.stmt) -> int:
    """Last source line of a statement (handles nested funcs / multi-line)."""
    end = getattr(stmt, "end_lineno", None)
    if end is not None:
        return int(end)
    # Fallback for ancient ASTs without end_lineno: walk children.
    max_line = stmt.lineno
    for child in ast.walk(stmt):
        max_line = max(max_line, getattr(child, "lineno", max_line))
    return max_line


# ── JS / TS structural compression (parser-lite, brace + paren aware) ─────────
#
# No stdlib JS parser exists, so this is a *pragmatic* scanner — but it is NOT a
# single mega-regex. The failure mode of the naive regex is a default-valued
# parameter like ``function f(opts = {})`` whose ``{}`` gets mistaken for the
# body. To avoid that we: (1) regex-match only the *head* (keyword + name) up to
# the parameter ``(``; (2) **paren-match** the parameter list (so ``{}`` defaults
# are consumed); (3) skip an optional TS return-type / arrow ``=>``; (4) the
# next ``{`` is then the *true* body brace, which we brace-match and elide.
# Everything string/template/comment aware. Anything we cannot confidently match
# is left untouched — degrade gracefully, never corrupt.

# Head of a function/method/arrow, anchored at a line start. Stops right before
# the parameter list (or, for paren-less arrows, captures the single identifier
# param). We intentionally require a line-start anchor so we don't strip an
# inline callback's body mid-expression and desync the structure.
_JS_HEAD_RE = re.compile(
    r"""
    (?P<lead>(?:^|\n)[ \t]*)                       # line start + indentation
    (?P<sig>
        (?:export\s+)?(?:default\s+)?(?:async\s+)?     # function declaration
            function\s*\*?\s*[A-Za-z_$][\w$]*\s*       #   function name
      | (?:export\s+)?(?:default\s+)?(?:async\s+)?     # anonymous function expr
            function\s*\*?\s*
      | (?:export\s+)?(?:const|let|var)\s+              # const f = (…) => / x =>
            [A-Za-z_$][\w$]*\s*(?::[^\n=;]+)?=\s*(?:async\s+)?
      | (?:public|private|protected|static|readonly|abstract|async|get|set|\s)*?
            [A-Za-z_$][\w$]*\s*                        # class method name
    )
    (?P<after>\(|[A-Za-z_$][\w$]*\s*=>)               # param '(' OR ident-arrow
    """,
    re.VERBOSE,
)


def compress_js_ts(content: str) -> tuple[str, int]:
    """Strip JS/TS function/method/arrow bodies, keeping signatures + braces.

    See the section comment above for the head→params→body algorithm. Returns
    ``(compressed_source, definitions_stripped)``.
    """
    out: list[str] = []
    n = len(content)
    stripped = 0
    pos = 0   # last index flushed into ``out``
    scan = 0  # where to resume searching

    while True:
        m = _JS_HEAD_RE.search(content, scan)
        if not m:
            break

        brace_open = _find_js_body_brace(content, m)
        if brace_open is None:
            scan = m.end()  # not actually a function body here → keep scanning
            continue
        body_end = _match_brace(content, brace_open)
        if body_end is None:
            scan = brace_open + 1
            continue

        # Only strip non-trivial bodies; an empty / already-elided body stays
        # as-is so re-runs are a fixed point (idempotent).
        inner = content[brace_open + 1 : body_end].strip()
        if inner == "" or inner == BODY_ELISION_MARKER:
            scan = body_end + 1
            continue

        out.append(content[pos : brace_open + 1])   # up to & incl. opening '{'
        out.append(f" {BODY_ELISION_MARKER} ")
        pos = body_end                              # keep the closing '}'
        scan = body_end + 1
        stripped += 1

    out.append(content[pos:n])
    return "".join(out), stripped


def _find_js_body_brace(content: str, m: "re.Match[str]") -> int | None:
    """Given a head match, return the index of the body's opening ``{`` (or None).

    Handles the three head shapes:
      * ``…(``  — paren-match the parameter list (consuming ``{}`` defaults),
        then skip a TS return type / arrow, then expect ``{``.
      * ``ident =>`` — paren-less arrow; the body ``{`` follows the ``=>``.
    """
    after = m.group("after")
    n = len(content)

    if after == "(":
        # ``m.end()`` sits just past the '('. Paren-match from that '('.
        open_paren = m.end() - 1
        close_paren = _match_paren(content, open_paren)
        if close_paren is None:
            return None
        j = close_paren + 1
        # Skip optional TS return type ``: Foo<Bar>`` and an arrow ``=>`` and
        # whitespace/comments, until the body brace.
        j = _skip_to_js_body(content, j)
        if j is not None and j < n and content[j] == "{":
            return j
        return None

    # Paren-less arrow: ``x =>``. ``m.end()`` is just past ``=>``.
    j = _skip_ws_and_comments(content, m.end())
    if j < n and content[j] == "{":
        return j
    return None


def _skip_to_js_body(content: str, j: int) -> int | None:
    """From just after a param ``)``, skip a return-type annotation and ``=>``
    (in any order, both optional) plus whitespace/comments, landing on the body
    ``{`` if there is one. Returns the index of ``{`` or None."""
    n = len(content)
    saw_arrow = False
    while True:
        j = _skip_ws_and_comments(content, j)
        if j >= n:
            return None
        c = content[j]
        if c == "{":
            return j
        if c == "=" and j + 1 < n and content[j + 1] == ">":
            if saw_arrow:
                return None
            saw_arrow = True
            j += 2
            continue
        if c == ":":
            # TS return type: consume until we hit '{', '=>', or a statement end.
            j += 1
            j = _skip_js_type(content, j)
            continue
        # Anything else here means this wasn't a function body (e.g. a call
        # ``foo()(`` or a declaration ``const x = bar();``). Bail out.
        return None


def _skip_js_type(content: str, j: int) -> int:
    """Skip a TS type annotation: advance past balanced ``<>``/``()``/``[]`` and
    plain type tokens until the next top-level ``{`` (body), ``=>`` or ``;``."""
    n = len(content)
    depth_angle = depth_paren = depth_brack = 0
    while j < n:
        c = content[j]
        if c in "'\"`":
            j = _skip_string(content, j, c)
            continue
        if c == "<":
            depth_angle += 1
        elif c == ">":
            if depth_angle > 0:
                depth_angle -= 1
            elif j + 1 < n and content[j + 1] == "{":
                # ``=>`` boundary handled by caller; a lone '>' ending a type.
                return j
        elif c == "(":
            depth_paren += 1
        elif c == ")":
            if depth_paren > 0:
                depth_paren -= 1
        elif c == "[":
            depth_brack += 1
        elif c == "]":
            if depth_brack > 0:
                depth_brack -= 1
        elif depth_angle == depth_paren == depth_brack == 0:
            if c == "{" or c == ";":
                return j
            if c == "=" and j + 1 < n and content[j + 1] == ">":
                return j
        j += 1
    return j


def _skip_ws_and_comments(s: str, i: int) -> int:
    """Advance past spaces/tabs/newlines and ``//`` / ``/* */`` comments."""
    n = len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c == "/" and i + 1 < n and s[i + 1] == "/":
            nl = s.find("\n", i + 2)
            i = n if nl == -1 else nl
            continue
        if c == "/" and i + 1 < n and s[i + 1] == "*":
            end = s.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        break
    return i


def _match_paren(s: str, open_idx: int) -> int | None:
    """Return index of the ``)`` matching the ``(`` at ``open_idx``.

    String / template / comment / nested-bracket aware (so ``{}`` defaults and
    nested ``()``/``[]`` inside the parameter list are consumed). Returns None
    if unbalanced."""
    depth = 0
    i = open_idx
    n = len(s)
    while i < n:
        c = s[i]
        if c == "/" and i + 1 < n and s[i + 1] == "/":
            nl = s.find("\n", i + 2)
            i = n if nl == -1 else nl
            continue
        if c == "/" and i + 1 < n and s[i + 1] == "*":
            end = s.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        if c in ("'", '"', "`"):
            i = _skip_string(s, i, c)
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _match_brace(s: str, open_idx: int) -> int | None:
    """Return index of the ``}`` matching the ``{`` at ``open_idx``.

    String / template-literal / comment aware so braces inside them don't
    count. Returns ``None`` if unbalanced. Pure scan, deterministic.
    """
    depth = 0
    i = open_idx
    n = len(s)
    while i < n:
        c = s[i]
        # Line comment
        if c == "/" and i + 1 < n and s[i + 1] == "/":
            nl = s.find("\n", i + 2)
            i = n if nl == -1 else nl
            continue
        # Block comment
        if c == "/" and i + 1 < n and s[i + 1] == "*":
            end = s.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        # Strings & template literals
        if c in ("'", '"', "`"):
            i = _skip_string(s, i, c)
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def _skip_string(s: str, start: int, quote: str) -> int:
    """Return the index just past the closing quote of a string starting at
    ``start`` (which holds the opening ``quote``). Handles backslash escapes;
    for template literals, also skips ``${...}`` interpolations brace-aware."""
    i = start + 1
    n = len(s)
    while i < n:
        c = s[i]
        if c == "\\":
            i += 2
            continue
        if quote == "`" and c == "$" and i + 1 < n and s[i + 1] == "{":
            # Template interpolation: brace-match it so its braces are ignored.
            close = _match_brace(s, i + 1)
            i = n if close is None else close + 1
            continue
        if c == quote:
            return i + 1
        i += 1
    return n


# ── Public entrypoint ─────────────────────────────────────────────────────────


def run(
    content: str,
    *,
    language: str | None = None,
    filename: str | None = None,
    keep_docstrings: bool = True,
) -> dict[str, Any]:
    """Structurally compress ``content`` (strip bodies, keep signatures).

    Args:
      content: the source text to compress. Required, must be ``str``.
      language: optional explicit language hint (``"python"``, ``"ts"``,
        ``"js"``, ``"text"``, …). When omitted, detected from ``filename``
        then content.
      filename: optional filename whose extension hints the language. Used as
        a string only — no filesystem access.
      keep_docstrings: when ``True`` (default) Python definitions keep their
        leading docstring; the rest of the body is elided.

    Returns a dict matching the manifest's ``compressed`` output:
      ``compressed`` (str), ``tokens_in`` (int), ``tokens_out`` (int),
      ``ratio`` (float in ``[0, 1]`` — fraction of *proxy* tokens removed),
      plus ``language`` (the language actually used) and
      ``definitions_stripped`` (count of bodies elided) for observability.

    Deterministic, no side effects. Raises ``TypeError`` on non-str input and
    re-raises ``SyntaxError`` if ``language='python'`` is forced on text that
    is not valid Python (the manifest's ``on_error = raise`` contract).
    """
    if not isinstance(content, str):
        raise TypeError(f"content must be str, got {type(content).__name__}")
    if language is not None and not isinstance(language, str):
        raise TypeError(f"language must be str or None, got {type(language).__name__}")

    tokens_in = count_tokens(content)
    lang = detect_language(content, language=language, filename=filename)

    if lang == PYTHON_LANG:
        compressed, stripped = compress_python(content, keep_docstrings=keep_docstrings)
    elif lang == JS_TS_LANG:
        compressed, stripped = compress_js_ts(content)
    else:
        # Graceful degradation: unknown / prose text is returned unchanged.
        compressed, stripped = content, 0

    tokens_out = count_tokens(compressed)
    ratio = 0.0 if tokens_in == 0 else round(1.0 - (tokens_out / tokens_in), 6)

    return {
        "compressed": compressed,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "ratio": ratio,
        "language": lang,
        "definitions_stripped": stripped,
    }


# ── Self-test (proves the logic on a real example) ────────────────────────────

# Real-shaped sample: substantive bodies (the case structural compression is
# *for* — real function bodies dwarf their signatures, which is why stripping
# them yields the large reductions Repomix reports). Exercises module docstring,
# imports, a decorator, a multi-line signature, nested function, and methods.
_PY_SAMPLE = '''\
"""Module docstring should survive (it is not a function body)."""
import os
import sys
from typing import Any


DEFAULT_RETRIES = 3


@decorator(arg=1)
def fetch(url: str, *, retries: int = DEFAULT_RETRIES) -> bytes:
    """Fetch a URL and return its bytes."""
    payload = b""
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            payload = _do_get(url)
            if not payload:
                raise OSError("empty response from server")
            break
        except OSError as exc:
            last_error = exc
            backoff = min(2 ** attempt, 30)
            _sleep(backoff)
            if attempt == retries - 1:
                raise
    if last_error is not None and not payload:
        raise last_error
    return payload


class Client:
    """A small client."""

    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self._session = None
        self._cache: dict[str, Any] = {}
        self._headers = {"accept": "application/json"}
        self._closed = False

    async def get_json(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # multi-line signature above must be kept verbatim
        if self._closed:
            raise RuntimeError("client is closed")
        key = path + repr(sorted((params or {}).items()))
        if key in self._cache:
            return self._cache[key]
        url = self.base + path
        if params:
            url = url + "?" + _encode_params(params)
        raw = fetch(url)
        parsed = _parse(raw)
        self._cache[key] = parsed
        return parsed
'''

_JS_SAMPLE = """\
import { thing } from "./mod";

export const CONST = 42;

export async function loadUser(id, opts = {}) {
  const url = `/users/${id}?x={notabrace}`;  // template + fake brace
  const headers = { accept: "application/json", ...opts.headers };
  const res = await fetch(url, { headers });
  if (!res.ok) { throw new Error(`bad status ${res.status}`); }
  const data = await res.json();
  return { id, ...data, fetchedAt: Date.now() };
}

class Repo {
  constructor(db) {
    this.db = db;
    this.cache = new Map();
    this.hits = 0;
  }

  find(id) {
    if (this.cache.has(id)) {
      this.hits += 1;
      return this.cache.get(id);
    }
    const row = this.db.query("select * from t where id = ?", id);
    this.cache.set(id, row);
    return row;
  }
}

const add = (a, b) => {
  const sum = a + b;
  if (Number.isNaN(sum)) {
    throw new TypeError("add expects numbers");
  }
  return sum;
};
"""


def _selftest() -> None:
    # ---- Python path -------------------------------------------------------
    out = run(_PY_SAMPLE, language="python")
    comp = out["compressed"]

    # Output must still be valid Python (structure-lossless).
    ast.parse(comp), "compressed Python must still parse"

    # Signatures + structure survive.
    for needle in (
        "import os",
        "from typing import Any",
        "DEFAULT_RETRIES = 3",
        "@decorator(arg=1)",
        "def fetch(url: str, *, retries: int = DEFAULT_RETRIES) -> bytes:",
        "class Client:",
        "def __init__(self, base: str) -> None:",
        "async def get_json(",          # multi-line signature head
        "params: dict[str, Any] | None = None,",  # multi-line signature body
        ") -> dict[str, Any]:",
        '"""Module docstring should survive (it is not a function body)."""',
        '"""Fetch a URL and return its bytes."""',  # kept docstring
        '"""A small client."""',
    ):
        assert needle in comp, f"signature/structure lost: {needle!r}"

    # Bodies are gone.
    for body_token in (
        "payload = _do_get(url)",
        "for attempt in range(retries)",
        "self._session = None",
        "raw = fetch(url)",
        "return _parse(raw)",
    ):
        assert body_token not in comp, f"body not stripped: {body_token!r}"

    assert out["definitions_stripped"] >= 3, out["definitions_stripped"]
    assert BODY_ELISION_MARKER in comp
    assert 0.0 <= out["ratio"] <= 1.0
    assert out["ratio"] > 0.3, f"expected >30% reduction, got {out['ratio']:.3f}"
    assert out["tokens_out"] < out["tokens_in"]

    # Idempotent: compressing the compressed code is a fixed point.
    out2 = run(comp, language="python")
    assert out2["compressed"] == comp, "Python compression is not idempotent"
    assert out2["definitions_stripped"] == 0

    # Idempotent on NESTED functions too (regression guard: a nested/inner def must
    # not leave the OUTER body partially stripped — stripping the outermost body
    # already elides everything inside it, so run(run(x)) == run(x)).
    _NESTED = (
        "def memoize(fn):\n"
        "    cache = {}\n"
        "    def wrapper(*a):\n"
        "        if a not in cache:\n"
        "            cache[a] = fn(*a)\n"
        "        return cache[a]\n"
        "    return wrapper\n"
    )
    _n1 = run(_NESTED, language="python")["compressed"]
    assert run(_n1, language="python")["compressed"] == _n1, "nested-function compression is not idempotent"
    ast.parse(_n1)  # still valid Python

    # Deterministic: same input → identical output.
    assert run(_PY_SAMPLE, language="python")["compressed"] == comp

    # keep_docstrings=False removes the docstrings too (more aggressive).
    out_nodoc = run(_PY_SAMPLE, language="python", keep_docstrings=False)
    assert '"""Fetch a URL and return its bytes."""' not in out_nodoc["compressed"]
    assert "def fetch(url: str, *, retries: int = DEFAULT_RETRIES) -> bytes:" in out_nodoc["compressed"]
    assert out_nodoc["ratio"] >= out["ratio"]  # at least as much removed

    # ---- JS / TS path ------------------------------------------------------
    js = run(_JS_SAMPLE, language="ts")
    jc = js["compressed"]
    for needle in (
        'import { thing } from "./mod";',
        "export const CONST = 42;",
        "export async function loadUser(id, opts = {}) {",
        "class Repo {",
        "constructor(db) {",
        "find(id) {",
        "const add = (a, b) => {",
    ):
        assert needle in jc, f"JS signature/structure lost: {needle!r}"
    for body_token in (
        "const res = await fetch(url, { headers })",
        "const data = await res.json()",
        'this.db.query("select * from t where id = ?", id)',
        "this.hits += 1;",
        "const sum = a + b;",
    ):
        assert body_token not in jc, f"JS body not stripped: {body_token!r}"
    # The fake brace inside the template string must NOT have broken matching:
    # loadUser's body is stripped but the class after it is intact.
    assert jc.index("export async function loadUser") < jc.index("class Repo")
    assert js["definitions_stripped"] >= 4, js["definitions_stripped"]
    assert js["ratio"] > 0.3, f"JS expected >30% reduction, got {js['ratio']:.3f}"
    # Braces stay balanced (structure-lossless).
    assert jc.count("{") == jc.count("}"), "JS brace balance broken"
    # Idempotent on JS too.
    assert run(jc, language="ts")["compressed"] == jc, "JS compression not idempotent"

    # ---- Graceful degradation on prose ------------------------------------
    prose = "This is a paragraph of plain English. It has no code structure at all.\n"
    pr = run(prose)
    assert pr["compressed"] == prose, "prose must pass through unchanged"
    assert pr["language"] == PLAINTEXT_LANG
    assert pr["ratio"] == 0.0
    assert pr["definitions_stripped"] == 0

    # ---- Edge cases --------------------------------------------------------
    empty = run("")
    assert empty["compressed"] == "" and empty["ratio"] == 0.0
    assert empty["tokens_in"] == 0 and empty["tokens_out"] == 0

    # Forcing python on invalid python raises (on_error=raise contract).
    raised = False
    try:
        run("def broken(:\n", language="python")
    except SyntaxError:
        raised = True
    assert raised, "forced-python on invalid source must raise SyntaxError"

    # Non-str input raises TypeError.
    raised = False
    try:
        run(123)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, "non-str content must raise TypeError"

    # Auto-detection (no language hint) finds Python and compresses it.
    auto = run(_PY_SAMPLE)
    assert auto["language"] == PYTHON_LANG
    assert auto["compressed"] == comp

    print(
        "PASS — structural_compress: "
        f"py ratio={out['ratio']:.2f} ({out['tokens_in']}→{out['tokens_out']} tok, "
        f"{out['definitions_stripped']} bodies), "
        f"js ratio={js['ratio']:.2f} ({js['tokens_in']}→{js['tokens_out']} tok, "
        f"{js['definitions_stripped']} bodies), "
        "idempotent + deterministic + graceful-degrade verified"
    )


if __name__ == "__main__":
    _selftest()
