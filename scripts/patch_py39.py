#!/usr/bin/env python3
"""Backport EddySeek to Python 3.9 (the Klipper host python on BTT CB1/SV08).

Only touches the few 3.10-only constructs it uses:
  dataclass(slots=True) / dataclass(kw_only=True), zip(strict=True), typing.TypeAlias
Idempotent. Usage:  python3 patch_py39.py ~/EddySeek/src/eddy_seek
"""
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "~/EddySeek/src/eddy_seek").expanduser()
if not root.is_dir():
    sys.exit("not a directory: %s" % root)

subs = [
    (re.compile(r",\s*slots=True"), ""),
    (re.compile(r"slots=True,\s*"), ""),
    (re.compile(r"@dataclass\(kw_only=True\)"), "@dataclass"),
    (re.compile(r",\s*strict=True"), ""),
    (re.compile(r"(from typing import [^\n]*?),\s*TypeAlias"), r"\1"),
    (re.compile(r"\b(\w+): TypeAlias ="), r"\1 ="),
]
def union_alias(text):
    """Module-level `Name = (A | B | C)` (evaluated at runtime) -> typing.Union."""
    def fix(m):
        parts = [p.strip() for p in m.group(2).split("|")]
        return "%s = Union[%s]" % (m.group(1), ", ".join(parts))
    new = re.sub(r"^(\w+) = \(\s*([\w\s|]+?)\s*\)$", fix, text, flags=re.M | re.S)
    if new != text and not re.search(r"^from typing import [^\n]*\bUnion\b", new, re.M):
        new = re.sub(r"^from typing import ", "from typing import Union, ", new, count=1, flags=re.M)
    return new


def optional_alias(text):
    """Module-level `Alias = tuple[..., list[float] | None]` -> Optional[...]."""
    pat = re.compile(r"^(\w+ = .*?)(\b\w+\[[^\[\]]*\]) \| None", re.M)
    new = pat.sub(r"\1Optional[\2]", text)
    if new != text and not re.search(r"^from typing import [^\n]*\bOptional\b", new, re.M):
        if re.search(r"^from typing import ", new, re.M):
            new = re.sub(r"^from typing import ", "from typing import Optional, ", new, count=1, flags=re.M)
        else:
            new = re.sub(r"^(from __future__ import annotations\n)", r"\1\nfrom typing import Optional\n", new, count=1, flags=re.M)
    return new


changed = 0
for path in sorted(root.rglob("*.py")):
    text = path.read_text()
    new = text
    for pattern, repl in subs:
        new = pattern.sub(repl, new)
    new = union_alias(new)
    new = optional_alias(new)
    if new != text:
        path.write_text(new)
        changed += 1
        print("patched", path.relative_to(root))
print("done: %d file(s) changed" % changed)
