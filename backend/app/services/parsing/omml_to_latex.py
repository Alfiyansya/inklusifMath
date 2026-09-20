"""
OMML (Office Math Markup Language) to LaTeX converter.

Converts Microsoft Word's internal XML math representation (OMML) to LaTeX.
OMML is stored inside .docx files as <m:oMath> elements in the main document XML.

Supported constructs:
  - Fractions (m:f)
  - Superscript (m:sSup), Subscript (m:sSub), Sub+Superscript (m:sSubSup)
  - Radicals (m:rad) — square root and nth root
  - Delimiters (m:d) — parentheses, brackets, absolute value
  - n-ary operators (m:nary) — summation, integral, product
  - Matrices (m:m)
  - Math runs (m:r / m:t) — plain text and symbols
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

# XML namespace map used by OMML
_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _tag(local: str) -> str:
    """Return fully-qualified OMML tag name."""
    return f"{{{_NS}}}{local}"


# Map of Unicode math symbols → LaTeX commands
_SYMBOL_MAP: dict[str, str] = {
    # Greek letters
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta",
    "ε": r"\epsilon", "ζ": r"\zeta", "η": r"\eta", "θ": r"\theta",
    "ι": r"\iota", "κ": r"\kappa", "λ": r"\lambda", "μ": r"\mu",
    "ν": r"\nu", "ξ": r"\xi", "π": r"\pi", "ρ": r"\rho",
    "σ": r"\sigma", "τ": r"\tau", "υ": r"\upsilon", "φ": r"\phi",
    "χ": r"\chi", "ψ": r"\psi", "ω": r"\omega",
    "Γ": r"\Gamma", "Δ": r"\Delta", "Θ": r"\Theta", "Λ": r"\Lambda",
    "Ξ": r"\Xi", "Π": r"\Pi", "Σ": r"\Sigma", "Υ": r"\Upsilon",
    "Φ": r"\Phi", "Ψ": r"\Psi", "Ω": r"\Omega",
    # Operators
    "×": r"\times", "÷": r"\div", "±": r"\pm", "∓": r"\mp",
    "·": r"\cdot", "∘": r"\circ",
    # Relations
    "≠": r"\neq", "≤": r"\leq", "≥": r"\geq", "≈": r"\approx",
    "≡": r"\equiv", "∈": r"\in", "∉": r"\notin", "⊂": r"\subset",
    "⊃": r"\supset", "⊆": r"\subseteq", "⊇": r"\supseteq",
    # Arrows
    "→": r"\to", "←": r"\leftarrow", "↔": r"\leftrightarrow",
    "⇒": r"\Rightarrow", "⇐": r"\Leftarrow", "⇔": r"\Leftrightarrow",
    # Set / logic
    "∪": r"\cup", "∩": r"\cap", "∅": r"\emptyset",
    "∀": r"\forall", "∃": r"\exists", "¬": r"\neg",
    "∧": r"\wedge", "∨": r"\vee",
    # Misc
    "∞": r"\infty", "√": r"\sqrt", "∑": r"\sum", "∏": r"\prod",
    "∫": r"\int", "∂": r"\partial", "∇": r"\nabla",
    "…": r"\ldots", "⋯": r"\cdots",
    # n-ary char map (used by m:nary)
    "∑": r"\sum", "∏": r"\prod", "∫": r"\int",
    "∬": r"\iint", "∭": r"\iiint", "∮": r"\oint",
    # Absolute value bars
    "|": r"|",
}

# n-ary operator characters → LaTeX commands
_NARY_MAP: dict[str, str] = {
    "∑": r"\sum", "∏": r"\prod",
    "∫": r"\int", "∬": r"\iint", "∭": r"\iiint", "∮": r"\oint",
    "⋃": r"\bigcup", "⋂": r"\bigcap",
    "⊕": r"\bigoplus", "⊗": r"\bigotimes",
}


def _get_text(elem: ET.Element, tag: str) -> str | None:
    """Return text content of first matching child tag, or None."""
    child = elem.find(f".//{_tag(tag)}")
    return child.text if child is not None else None


def _convert_node(node: ET.Element) -> str:
    """Recursively convert a single OMML node to LaTeX string."""
    tag = node.tag

    # ── Math run — plain text ──
    if tag == _tag("r"):
        return _convert_run(node)

    # ── Fraction ──
    if tag == _tag("f"):
        num = node.find(_tag("num"))
        den = node.find(_tag("den"))
        num_str = _convert_children(num) if num is not None else ""
        den_str = _convert_children(den) if den is not None else ""
        return rf"\frac{{{num_str}}}{{{den_str}}}"

    # ── Superscript ──
    if tag == _tag("sSup"):
        base = node.find(_tag("e"))
        sup = node.find(_tag("sup"))
        base_str = _convert_children(base) if base is not None else ""
        sup_str = _convert_children(sup) if sup is not None else ""
        return rf"{_wrap(base_str)}^{{{sup_str}}}"

    # ── Subscript ──
    if tag == _tag("sSub"):
        base = node.find(_tag("e"))
        sub = node.find(_tag("sub"))
        base_str = _convert_children(base) if base is not None else ""
        sub_str = _convert_children(sub) if sub is not None else ""
        return rf"{_wrap(base_str)}_{{{sub_str}}}"

    # ── Subscript + Superscript ──
    if tag == _tag("sSubSup"):
        base = node.find(_tag("e"))
        sub = node.find(_tag("sub"))
        sup = node.find(_tag("sup"))
        base_str = _convert_children(base) if base is not None else ""
        sub_str = _convert_children(sub) if sub is not None else ""
        sup_str = _convert_children(sup) if sup is not None else ""
        return rf"{_wrap(base_str)}_{{{sub_str}}}^{{{sup_str}}}"

    # ── Radical (square root / nth root) ──
    if tag == _tag("rad"):
        deg = node.find(_tag("deg"))
        base = node.find(_tag("e"))
        base_str = _convert_children(base) if base is not None else ""
        # Check if degree is empty (meaning plain square root)
        deg_hide = node.find(f".//{_tag('radPr')}/{_tag('degHide')}")
        if deg_hide is not None and deg_hide.get(_tag("val"), "1") == "1":
            return rf"\sqrt{{{base_str}}}"
        deg_str = _convert_children(deg) if deg is not None else ""
        if deg_str.strip() in ("", "2"):
            return rf"\sqrt{{{base_str}}}"
        return rf"\sqrt[{deg_str}]{{{base_str}}}"

    # ── Delimiter (parentheses, brackets, absolute value bars) ──
    if tag == _tag("d"):
        dpr = node.find(_tag("dPr"))
        beg_chr = ""
        end_chr = ""
        if dpr is not None:
            beg_elem = dpr.find(_tag("begChr"))
            end_elem = dpr.find(_tag("endChr"))
            beg_chr = beg_elem.get(_tag("val"), "(") if beg_elem is not None else "("
            end_chr = end_elem.get(_tag("val"), ")") if end_elem is not None else ")"

        # Collect elements inside delimiter
        contents = []
        for child in node:
            if child.tag == _tag("e"):
                contents.append(_convert_children(child))
        inner = ", ".join(contents)

        # Map delimiter chars to LaTeX
        beg_latex = _delim_char(beg_chr, opening=True)
        end_latex = _delim_char(end_chr, opening=False)
        return rf"\left{beg_latex}{inner}\right{end_latex}"

    # ── n-ary operator (sum, integral, product) ──
    if tag == _tag("nary"):
        nary_pr = node.find(_tag("naryPr"))
        chr_elem = nary_pr.find(_tag("chr")) if nary_pr is not None else None
        operator_char = chr_elem.get(_tag("val"), "∑") if chr_elem is not None else "∑"
        operator = _NARY_MAP.get(operator_char, r"\sum")

        sub = node.find(_tag("sub"))
        sup = node.find(_tag("sup"))
        e = node.find(_tag("e"))
        sub_str = f"_{{{_convert_children(sub)}}}" if sub is not None else ""
        sup_str = f"^{{{_convert_children(sup)}}}" if sup is not None else ""
        e_str = _convert_children(e) if e is not None else ""
        return rf"{operator}{sub_str}{sup_str} {e_str}"

    # ── Equation array / aligned equations ──
    if tag == _tag("eqArr"):
        rows = []
        for row in node.findall(_tag("e")):
            rows.append(_convert_children(row))
        inner = r" \\ ".join(rows)
        return rf"\begin{{aligned}}{inner}\end{{aligned}}"

    # ── Matrix ──
    if tag == _tag("m"):
        rows_latex = []
        for mr in node.findall(_tag("mr")):
            cells = [_convert_children(cell) for cell in mr.findall(_tag("e"))]
            rows_latex.append(" & ".join(cells))
        inner = r" \\ ".join(rows_latex)
        return rf"\begin{{matrix}}{inner}\end{{matrix}}"

    # ── Group character (overbrace, underbrace, etc.) ──
    if tag == _tag("groupChr"):
        e = node.find(_tag("e"))
        e_str = _convert_children(e) if e is not None else ""
        pr = node.find(_tag("groupChrPr"))
        chr_elem = pr.find(_tag("chr")) if pr is not None else None
        chr_val = chr_elem.get(_tag("val"), "") if chr_elem is not None else ""
        if chr_val == "⏞":
            return rf"\overbrace{{{e_str}}}"
        if chr_val == "⏟":
            return rf"\underbrace{{{e_str}}}"
        return e_str

    # ── Box (boxed expression) ──
    if tag == _tag("box"):
        e = node.find(_tag("e"))
        e_str = _convert_children(e) if e is not None else ""
        return rf"\boxed{{{e_str}}}"

    # ── Limit lower / upper ──
    if tag == _tag("limLow"):
        e = node.find(_tag("e"))
        lim = node.find(_tag("lim"))
        e_str = _convert_children(e) if e is not None else ""
        lim_str = _convert_children(lim) if lim is not None else ""
        return rf"{e_str}_{{{lim_str}}}"

    if tag == _tag("limUpp"):
        e = node.find(_tag("e"))
        lim = node.find(_tag("lim"))
        e_str = _convert_children(e) if e is not None else ""
        lim_str = _convert_children(lim) if lim is not None else ""
        return rf"{e_str}^{{{lim_str}}}"

    # ── Phantom / accent ──
    if tag == _tag("acc"):
        e = node.find(_tag("e"))
        e_str = _convert_children(e) if e is not None else ""
        pr = node.find(_tag("accPr"))
        chr_elem = pr.find(_tag("chr")) if pr is not None else None
        chr_val = chr_elem.get(_tag("val"), "̂") if chr_elem is not None else "̂"
        accent_map = {
            "̂": r"\hat", "̄": r"\bar", "̃": r"\tilde",
            "⃗": r"\vec", "̈": r"\ddot", "̇": r"\dot",
        }
        cmd = accent_map.get(chr_val, r"\hat")
        return rf"{cmd}{{{e_str}}}"

    # ── Fallback: recurse into children ──
    return _convert_children(node)


def _convert_run(run: ET.Element) -> str:
    """Convert an m:r (math run) element to LaTeX text."""
    text_elem = run.find(_tag("t"))
    if text_elem is None:
        return ""
    text = text_elem.text or ""
    # Map individual characters
    result = ""
    for ch in text:
        result += _SYMBOL_MAP.get(ch, ch)
    return result


def _convert_children(parent: ET.Element | None) -> str:
    """Convert all children of an element and concatenate."""
    if parent is None:
        return ""
    parts = []
    for child in parent:
        parts.append(_convert_node(child))
    return "".join(parts)


def _wrap(expr: str) -> str:
    """Wrap a base expression in braces if it has more than one character."""
    if len(expr) <= 1:
        return expr
    return f"{{{expr}}}"


def _delim_char(ch: str, opening: bool) -> str:
    """Map a delimiter character to its LaTeX \\left / \\right argument."""
    map_open = {"(": "(", "[": "[", "{": r"\{", "|": "|", "‖": r"\|"}
    map_close = {")": ")", "]": "]", "}": r"\}", "|": "|", "‖": r"\|"}
    if opening:
        return map_open.get(ch, ch) if ch else "."
    return map_close.get(ch, ch) if ch else "."


def omml_element_to_latex(omml_elem: ET.Element) -> str:
    """
    Convert a single <m:oMath> element tree to a LaTeX string.

    Args:
        omml_elem: An xml.etree.ElementTree.Element representing <m:oMath>.

    Returns:
        A LaTeX string, e.g. r"\\frac{a}{b}".
    """
    return _convert_children(omml_elem).strip()


def omml_xml_to_latex(xml_string: str) -> str:
    """
    Parse an OMML XML string and convert to LaTeX.

    Args:
        xml_string: Raw XML string of an <m:oMath> element.

    Returns:
        LaTeX string.
    """
    try:
        elem = ET.fromstring(xml_string)
        return omml_element_to_latex(elem)
    except ET.ParseError:
        return ""
