
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build an assembly-agnostic FHIR R4 CodeSystem for human cytogenetic bands (ISCN),
with part-of containment and prev/next sibling relationships at all levels.

Input : UCSC cytoBand table (TSV) — columns: chrom, start, end, name, gieStain
Output: CodeSystem JSON (no coordinates, no stains)

Author: M365 Copilot
"""

import argparse
import csv
import json
import re
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Dict, List

# ----------------------------
# Helpers (FHIR structure)
# ----------------------------

def new_node(code: str, display: str | None = None) -> OrderedDict:
    return OrderedDict([
        ("code", code),
        ("display", display or code),
        ("property", []),
        ("concept", [])
    ])

def add_prop(node: dict, code: str, vtype: str, value):
    """
    Add a property to a concept.
    vtype in {'code','Coding','integer','boolean','string','dateTime','decimal'}
    """
    key = f"value{vtype[0].upper()}{vtype[1:]}"
    node.setdefault("property", []).append({"code": code, key: value})

def add_kind(node: dict, value: str):
    add_prop(node, "kind", "code", value)

def child_index(node: dict) -> Dict[str, dict]:
    return {c["code"]: c for c in node.get("concept", [])}

# ----------------------------
# Building the hierarchy
# ----------------------------

BAND_RE = re.compile(r"^(?P<arm>[pq])(?P<digits>\d{2})(?:\.(?P<sub>\d{1,2}))?$")

def ensure_chrom(top_index: Dict[str, dict], cs: dict, chrom_code: str) -> dict:
    if chrom_code not in top_index:
        node = new_node(chrom_code, f"Chromosome {chrom_code}")
        add_kind(node, "chromosome")
        cs["concept"].append(node)
        top_index[chrom_code] = node
    return top_index[chrom_code]

def ensure_arm(chrom_node: dict, chrom_code: str, arm_char: str) -> dict:
    idx = child_index(chrom_node)
    code = f"{chrom_code}{arm_char}"
    if code not in idx:
        arm = new_node(code, code)
        add_kind(arm, "arm")
        chrom_node["concept"].append(arm)
        return arm
    return idx[code]

def ensure_region(arm_node: dict, chrom_code: str, arm_char: str, region_digit: str) -> dict:
    idx = child_index(arm_node)
    code = f"{chrom_code}{arm_char}{region_digit}"
    if code not in idx:
        reg = new_node(code, code)
        add_kind(reg, "region")
        arm_node["concept"].append(reg)
        return reg
    return idx[code]

def ensure_band(region_node: dict, chrom_code: str, arm_char: str, region_digit: str, band_digit: str) -> dict:
    idx = child_index(region_node)
    code = f"{chrom_code}{arm_char}{region_digit}{band_digit}"
    if code not in idx:
        band = new_node(code, code)
        add_kind(band, "band")
        region_node["concept"].append(band)
        return band
    return idx[code]

def index_nodes(n: dict, code_to_node: Dict[str, dict]):
    code_to_node[n["code"]] = n
    for c in n.get("concept", []):
        index_nodes(c, code_to_node)

def link_seq(codes: List[str], code_to_node: Dict[str, dict], cs_url: str):
    """Assign prev/next Coding properties within a sequence of codes."""
    for i, code in enumerate(codes):
        node = code_to_node.get(code)
        if not node:
            continue
        # Remove previous prev/next to avoid duplicates
        node["property"] = [p for p in node.get("property", []) if p["code"] not in ("prev", "next")]
        if i > 0:
            prev_code = codes[i - 1]
            add_prop(node, "prev", "Coding", {"system": cs_url, "code": prev_code, "display": prev_code})
        if i < len(codes) - 1:
            next_code = codes[i + 1]
            add_prop(node, "next", "Coding", {"system": cs_url, "code": next_code, "display": next_code})

def karyotype_order_present(code_to_node: Dict[str, dict]) -> List[str]:
    """Return top-level chromosome order: 1..22, X, Y (only those present)."""
    order = [str(i) for i in range(1, 23) if str(i) in code_to_node]
    if "X" in code_to_node:
        order.append("X")
    if "Y" in code_to_node:
        order.append("Y")
    return order

# ----------------------------
# Main build function
# ----------------------------

def build_codesystem(
    input_path: Path,
    output_path: Path,
    url: str,
    version: str,
    name: str,
    title: str,
    include_mito: bool = False,
) -> dict:
    cs = OrderedDict([
        ("resourceType", "CodeSystem"),
        ("url", url),
        ("version", version),
        ("name", name),
        ("title", title),
        ("status", "active"),
        ("content", "complete"),
        ("caseSensitive", True),
        ("hierarchyMeaning", "part-of"),
        ("property", [
            {"code": "kind", "type": "code"},
            {"code": "prev", "type": "Coding"},
            {"code": "next", "type": "Coding"}
        ]),
        ("concept", [])
    ])

    top_index: Dict[str, dict] = {}
    # Order trackers
    order_arms = defaultdict(list)         # chrom -> [chromp, chromq]
    order_regions = defaultdict(list)      # (chrom, arm) -> [region codes]
    order_bands = defaultdict(list)        # (chrom, arm, regionDigit) -> [band codes]
    order_subbands = defaultdict(list)     # (chrom, arm, bandDigits) -> [full subband codes]

    kept = skipped = 0

    # Read TSV (robust to spaces/tabs)
    with input_path.open("r", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        for row in reader:
            if not row or len(row) < 4:
                continue
            if row[0].startswith(("track", "browser", "#")):
                continue

            chrom, name = row[0].strip(), row[3].strip() if len(row) >= 4 else ""
            # Normalize chromosome code
            c = chrom[3:] if chrom.startswith("chr") else chrom
            if c == "M" and not include_mito:
                skipped += 1
                continue

            m = BAND_RE.match(name)
            if not m:
                # Rows without a valid band name (e.g., alt/random/unplaced) are not in ISCN hierarchy
                skipped += 1
                continue

            arm = m.group("arm")           # 'p' or 'q'
            digits = m.group("digits")     # two digits: region, band
            region_d, band_d = digits[0], digits[1]
            sub = m.group("sub")           # optional decimal digits

            # Build tree
            chrom_node = ensure_chrom(top_index, cs, c)
            arm_node   = ensure_arm(chrom_node, c, arm)
            region     = ensure_region(arm_node, c, arm, region_d)
            band       = ensure_band(region, c, arm, region_d, band_d)

            # Leaf for subband (decimal present)
            if sub is not None:
                full_code = f"{c}{name}"   # e.g., "1p36.33"
                leaf = new_node(full_code, full_code)
                add_kind(leaf, "subband")
                band["concept"].append(leaf)

            # Track encountered order
            ac = f"{c}{arm}"
            if ac not in order_arms[c]:
                order_arms[c].append(ac)

            rc = f"{c}{arm}{region_d}"
            if rc not in order_regions[(c, arm)]:
                order_regions[(c, arm)].append(rc)

            bc = f"{c}{arm}{region_d}{band_d}"
            if bc not in order_bands[(c, arm, region_d)]:
                order_bands[(c, arm, region_d)].append(bc)

            if sub is not None:
                key = (c, arm, f"{region_d}{band_d}")
                sbc = f"{c}{name}"
                if sbc not in order_subbands[key]:
                    order_subbands[key].append(sbc)

            kept += 1

    # Map codes -> nodes
    code_to_node: Dict[str, dict] = {}
    for cnode in cs["concept"]:
        index_nodes(cnode, code_to_node)

    # Link chromosomes (karyotype order)
    chrom_order = karyotype_order_present(code_to_node)
    link_seq(chrom_order, code_to_node, url)

    # Link arms, regions, bands, subbands
    for c, arms in order_arms.items():
        link_seq(arms, code_to_node, url)

    for (c, arm), regions in order_regions.items():
        link_seq(regions, code_to_node, url)

    for (c, arm, region_d), bands in order_bands.items():
        link_seq(bands, code_to_node, url)

    for (c, arm, band_digits), subs in order_subbands.items():
        link_seq(subs, code_to_node, url)

    # Reorder top-level chromosomes as karyotype order for readability
    cs["concept"] = [code_to_node[k] for k in chrom_order]

    # Write out
    output_path.write_text(json.dumps(cs, indent=2))
    print("SUMMARY:")
    print(json.dumps({
        "kept_banded_rows": kept,
        "skipped_nonbanded_rows": skipped,
        "chromosomes_included": chrom_order
    }, indent=2))
    print(f"WROTE: {output_path}")
    return cs

# ----------------------------
# CLI
# ----------------------------

def parse_args():
    ap = argparse.ArgumentParser(
        description="Generate an assembly-agnostic FHIR R4 CodeSystem for human cytogenetic bands with prev/next links."
    )
    ap.add_argument("--input", "-i", required=True, type=Path, help="UCSC cytoBand file (TSV).")
    ap.add_argument("--output", "-o", required=True, type=Path, help="Output CodeSystem JSON path.")
    ap.add_argument("--url", "-u", default="http://example.org/fhir/CodeSystem/human-cytoband-agnostic",
                    help="Canonical URL for the CodeSystem.")
    ap.add_argument("--version", "-v", default="1.1.0", help="CodeSystem version.")
    ap.add_argument("--name", default="HumanCytogeneticBandsAssemblyAgnostic", help="CodeSystem.name")
    ap.add_argument("--title", default="Human Cytogenetic Bands (Assembly-agnostic with prev/next)", help="CodeSystem.title")
    ap.add_argument("--include-mito", action="store_true",
                    help="Include mitochondrial (chrM). Default: exclude (no bands in ISCN).")
    return ap.parse_args()

if __name__ == "__main__":
    args = parse_args()
    build_codesystem(
        input_path=args.input,
        output_path=args.output,
        url=args.url,
        version=args.version,
        name=args.name,
        title=args.title,
        include_mito=args.include_mito
    )
