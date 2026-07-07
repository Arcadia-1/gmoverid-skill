#!/usr/bin/env python3
"""Convert a small Sky130 Spectre-style .scs netlist subset to ngspice .spi."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from sky130_common import continuous_model_lib, find_sky130a


_INST_RE = re.compile(r"^(\S+)\s*\(([^)]*)\)\s*(\S+)\s*(.*)$")
_INCLUDE_RE = re.compile(r'^include\s+"([^"]+)"(?:\s+section\s*=\s*(\S+))?.*$', re.IGNORECASE)
_NUM_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?([TGMKkmunpfa])?$")
_SUFFIX = {
    "T": 1e12,
    "G": 1e9,
    "M": 1e6,
    "K": 1e3,
    "k": 1e3,
    "m": 1e-3,
    "u": 1e-6,
    "n": 1e-9,
    "p": 1e-12,
    "f": 1e-15,
    "a": 1e-18,
}
_CONTROL_COMMANDS = {
    "destroy",
    "display",
    "echo",
    "let",
    "linearize",
    "meas",
    "noise",
    "op",
    "plot",
    "print",
    "quit",
    "reset",
    "resume",
    "run",
    "set",
    "setplot",
    "setseed",
    "show",
    "tran",
    "unset",
    "wrdata",
    "write",
}


def spectre_number(value: str) -> float | None:
    match = _NUM_RE.match(value)
    if not match:
        return None
    suffix = match.group(1)
    base = float(value[: -1] if suffix else value)
    return base * (_SUFFIX[suffix] if suffix else 1.0)


def emit_value(value: str) -> str:
    value = value.strip()
    number = spectre_number(value)
    if number is not None:
        return f"{number:g}"
    return value if value.startswith("{") else "{" + value + "}"


def split_statements(text: str) -> list[str]:
    statements: list[str] = []
    pending = ""
    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if line.endswith("\\"):
            pending += line[:-1] + " "
            continue
        statements.append((pending + line).strip())
        pending = ""
    if pending.strip():
        statements.append(pending.strip())
    return statements


def split_params(rest: str) -> dict[str, str]:
    params: dict[str, str] = {}
    for token in rest.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        params[key.lower()] = value
    return params


def convert_source(name: str, nodes: list[str], master: str, params: dict[str, str]) -> str:
    letter = "V" if master == "vsource" else "I"
    pieces = [spice_name(letter, name), *nodes]
    source_type = params.pop("type", "dc").lower()
    dc_value = params.pop("dc", None)
    if dc_value is not None:
        pieces.extend(["DC", emit_value(dc_value)])
    mag = params.pop("mag", None)
    if mag is not None:
        pieces.extend(["AC", emit_value(mag)])
    if source_type == "pulse":
        vals = [
            params.pop("val0", "0"),
            params.pop("val1", "0"),
            params.pop("delay", "0"),
            params.pop("rise", "1p"),
            params.pop("fall", "1p"),
            params.pop("width", "1n"),
            params.pop("period", "2n"),
        ]
        pieces.append("PULSE(" + " ".join(emit_value(v) for v in vals) + ")")
    elif source_type == "sine":
        vals = [
            params.pop("sinedc", "0"),
            params.pop("ampl", "0"),
            params.pop("freq", "1k"),
            params.pop("delay", "0"),
        ]
        pieces.append("SIN(" + " ".join(emit_value(v) for v in vals) + ")")
    elif source_type != "dc":
        raise SystemExit(f"unsupported source type={source_type}")
    if dc_value is None and mag is None and source_type == "dc":
        pieces.extend(["DC", "0"])
    return " ".join(pieces)


def converted_source_name(name: str) -> str:
    return name if name[:1].upper() in {"V", "I"} else f"V{name}"


def spice_name(prefix: str, name: str) -> str:
    return name if name[:1].upper() == prefix.upper() else f"{prefix}{name}"


def convert_statement(
    stmt: str,
    model_lib: Path | None,
    default_corner: str,
    included_model: list[bool],
    current_dir: Path | None = None,
    seen: set[Path] | None = None,
) -> list[str]:
    lower = stmt.lower()
    if lower.startswith("simulator ") or lower.startswith("global "):
        return [f"* skipped Spectre control statement: {stmt}"]
    if lower == "control":
        return [".control"]
    if lower in {"endcontrol", "endc"}:
        return [".endc"]
    if lower.split(None, 1)[0] in _CONTROL_COMMANDS:
        return [stmt]
    if lower.startswith("options "):
        return [".options " + stmt.split(None, 1)[1]]
    if lower.startswith("parameters "):
        body = stmt.split(None, 1)[1]
        return [".param " + " ".join(f"{k}={emit_value(v)}" for k, v in split_params(body).items())]
    if lower.startswith("measure ") or lower.startswith("meas "):
        return [".meas " + stmt.split(None, 1)[1]]
    if lower.startswith("include "):
        match = _INCLUDE_RE.match(stmt)
        if not match:
            raise SystemExit(f"cannot parse include: {stmt}")
        include_path, section = match.groups()
        if "sky130" in include_path.lower() and model_lib is not None:
            included_model[0] = True
            return [f'.lib "{model_lib}" {section or default_corner}']
        target = (current_dir / include_path).resolve() if current_dir is not None else Path(include_path)
        if target.is_file() and target.suffix.lower() == ".scs":
            return [
                f"* begin converted include {include_path}",
                *convert_file_body(target, model_lib, default_corner, included_model, seen or set()),
                f"* end converted include {include_path}",
            ]
        if section:
            return [f'.lib "{include_path}" {section}']
        return [f'.include "{include_path}"']
    if lower.startswith("subckt "):
        return [".subckt " + stmt.split(None, 1)[1]]
    if lower.startswith("ends"):
        parts = stmt.split()
        return [".ends" + (f" {parts[1]}" if len(parts) > 1 else "")]
    if lower.startswith("save "):
        return [".save " + stmt.split(None, 1)[1]]
    if lower.startswith("ic "):
        body = stmt.split(None, 1)[1].strip("()")
        terms = []
        for token in body.split():
            if "=" not in token:
                continue
            node, value = token.split("=", 1)
            terms.append(f"v({node})={emit_value(value)}")
        return [".ic " + " ".join(terms)] if terms else []
    if len(stmt.split()) >= 2 and stmt.split()[1].lower() == "tran":
        params = split_params(stmt)
        step = emit_value(params.get("step", "1p"))
        stop = emit_value(params.get("stop", "1n"))
        maxstep = emit_value(params.get("maxstep", params.get("max_step", params.get("strobeperiod", "1p"))))
        if params.get("uic", "").lower() in {"1", "true", "yes"}:
            return [f".tran {step} {stop} 0 {maxstep} uic"]
        return [f".tran {step} {stop}"]
    if len(stmt.split()) >= 2 and stmt.split()[1].lower() == "dc":
        params = split_params(stmt)
        source = params.get("source")
        if not source:
            raise SystemExit(f"dc statement missing source=: {stmt}")
        start = emit_value(params.get("start", "0"))
        stop = emit_value(params.get("stop", "1"))
        step = emit_value(params.get("step", "0.01"))
        return [f".dc {converted_source_name(source)} {start} {stop} {step}"]
    if len(stmt.split()) >= 2 and stmt.split()[1].lower() == "ac":
        params = split_params(stmt)
        if "dec" in params:
            return [f".ac dec {params['dec']} {emit_value(params.get('start', '1'))} {emit_value(params.get('stop', '1e9'))}"]
        return [f".ac dec 40 {emit_value(params.get('start', '1'))} {emit_value(params.get('stop', '1e9'))}"]
    if len(stmt.split()) >= 2 and stmt.split()[1].lower() == "noise":
        params = split_params(stmt)
        output = params.get("output", "vout")
        source = converted_source_name(params.get("source", "VIN"))
        dec = params.get("dec", "20")
        start = emit_value(params.get("start", "1"))
        stop = emit_value(params.get("stop", "1e6"))
        return [f".noise v({output}) {source} dec {dec} {start} {stop}"]
    if stmt.startswith("."):
        return [stmt]

    match = _INST_RE.match(stmt)
    if not match:
        raise SystemExit(f"unrecognized Spectre-style statement: {stmt}")
    name, node_text, master, rest = match.groups()
    nodes = node_text.split()
    params = split_params(rest)
    if master in {"vsource", "isource"}:
        return [convert_source(name, nodes, master, params)]
    if master == "vcvs":
        if len(nodes) != 4:
            raise SystemExit(f"vcvs {name} needs four nodes")
        return [f"{spice_name('E', name)} {' '.join(nodes)} {emit_value(params.get('gain', '1'))}"]
    if master in {"capacitor", "resistor", "inductor"}:
        letter = {"capacitor": "C", "resistor": "R", "inductor": "L"}[master]
        key = {"capacitor": "c", "resistor": "r", "inductor": "l"}[master]
        if key not in params:
            raise SystemExit(f"{master} {name} missing {key}=")
        return [f"{spice_name(letter, name)} {' '.join(nodes)} {emit_value(params[key])}"]
    param_text = " ".join(f"{k}={emit_value(v)}" for k, v in params.items())
    return [f"{spice_name('X', name)} {' '.join(nodes)} {master} {param_text}".rstrip()]


def convert_file_body(
    path: Path,
    model_lib: Path | None,
    corner: str,
    included_model: list[bool],
    seen: set[Path],
) -> list[str]:
    path = path.resolve()
    if path in seen:
        return [f"* skipped duplicate include {path.name}"]
    seen.add(path)
    lines: list[str] = []
    for stmt in split_statements(path.read_text(encoding="utf-8")):
        lines.extend(convert_statement(stmt, model_lib, corner, included_model, path.parent, seen))
    seen.remove(path)
    return lines


def convert_text(
    text: str,
    model_lib: Path | None,
    corner: str,
    title: str,
    current_dir: Path | None = None,
    *,
    add_model: bool = True,
    add_control: bool = True,
    add_end: bool = True,
) -> str:
    included_model = [False]
    lines = [f"* {title} - converted from Sky130 Spectre-style subset"]
    for stmt in split_statements(text):
        lines.extend(convert_statement(stmt, model_lib, corner, included_model, current_dir, set()))
    if add_model and model_lib is not None and not included_model[0]:
        lines.insert(1, f'.lib "{model_lib}" {corner}')
    if add_control and not any(line.lower().startswith(".control") for line in lines):
        lines.extend([".control", "run", "quit", ".endc"])
    if add_end:
        lines.append(".end")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--pdk-root", help="Path containing sky130A/, or direct path to sky130A/.")
    parser.add_argument("--model-lib", type=Path, help="Direct path to sky130.lib.spice.")
    parser.add_argument("--corner", default="tt")
    parser.add_argument(
        "--fragment",
        action="store_true",
        help="Emit an include-safe netlist fragment: no auto model .lib, no auto .control block, and no final .end.",
    )
    args = parser.parse_args()

    model_lib = args.model_lib
    if model_lib is None:
        model_lib = None if args.fragment else continuous_model_lib(find_sky130a(args.pdk_root))

    out = convert_text(
        args.input.read_text(encoding="utf-8"),
        model_lib,
        args.corner,
        args.input.name,
        args.input.parent,
        add_model=not args.fragment,
        add_control=not args.fragment,
        add_end=not args.fragment,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(out, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
