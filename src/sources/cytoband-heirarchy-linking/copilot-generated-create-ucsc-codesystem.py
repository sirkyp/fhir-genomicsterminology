#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build an assembly-agnostic FHIR R4 CodeSystem for human cytogenetic bands (ISCN),
with part-of containment and prev/next sibling relationships at all levels.
Optionally cross-link p <-> q across the centromere at subband/band/region levels.

Input : UCSC cytoBand table (TSV) — columns: chrom, chromStart, chromEnd, name, gieStain
         Only 'chrom' and 'name' are used; coordinates and stains are ignored.
Output: CodeSystem JSON (no coordinates, no stains)

Python: 3.7+

Author: M365 Copilot
"""

import argparse
import csv
import json
import re
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ------------- FHIR helpers -------------

def new_node(code: str, display: Optional[str] = None) -> OrderedDict:
    """Create a CodeSystem.concept node."""
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
    key = "value" + vtype[0].upper() + vtype[1:]
    node.setdefault("property", []).append({"code": code, key: value})

def add_kind(node: dict, value: str):
    """Tag node with a 'kind' code property."""
    add_prop(node, "kind", "code", value)

def child_index(node: dict) -> Dict[str, dict]:
    """Index child concepts by code for fast ensure/get."""
    return {c["code"]: c for c in node.get("concept", [])}

# ------------- Hierarchy constructors -------------

BAND_RE = re.compile(r"^(?P<arm>[pq])(?P<digits>\d{2})(?:\.(?P<sub>\d{1,2}))?$")

def ensure_chrom(top_index: Dict[str, dict], cs: dict, chrom_code: str) -> dict:
    if chrom_code not in top_index:
        node = new_node(chrom_code, "Chromosome " + chrom_code)
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

# ------------- Indexing & linking -------------

def index_nodes(n: dict, code_to_node: Dict[str, dict]):
    """Flatten a concept tree into a code -> node index."""
    code_to_node[n["code"]] = n
    for c in n.get("concept", []):
        index_nodes(c, code_to_node)

def link_seq(codes: List[str], code_to_node: Dict[str, dict], cs_url: str):
    """
    Assign prev/next Coding properties within a sequence of codes.
    Overwrites prev/next for the nodes in the sequence (preserves other properties).
    """
    for i, code in enumerate(codes):
        node = code_to_node.get(code)
        if not node:
            continue
        # Remove previous prev/next to avoid duplicate stacking
        node["property"] = [p for p in node.get("property", []) if p.get("code") not in ("prev", "next")]
        if i > 0:
            prev_code = codes[i - 1]
            add_prop(node, "prev", "Coding", {"system": cs_url, "code": prev_code, "display": prev_code})
        if i < len(codes) - 1:
            next_code = codes[i + 1]
            add_prop(node, "next", "Coding", {"system": cs_url, "code": next_code, "display": next_code})

def has_prop(node: dict, prop_code: str) -> bool:
    return any(p.get("code") == prop_code for p in node.get("property", []))

def add_single_link(node: dict, side: str, target_code: str, cs_url: str):
    """Add a single prev/next link if not already present (preserve intra-arm adjacency)."""
    if not has_prop(node, side):
        add_prop(node, side, "Coding", {"system": cs_url, "code": target_code, "display": target_code})

def karyotype_order_present(code_to_node: Dict[str, dict]) -> List[str]:
    """Return top-level chromosome order: 1..22, X, Y (only those present)."""
    order = [str(i) for i in range(1, 23) if str(i) in code_to_node]
    if "X" in code_to_node:
        order.append("X")
    if "Y" in code_to_node:
        order.append("Y")
    return order

# ------------- Centromere cross-link helpers -------------

def flatten_bands_for_arm(
    order_regions: Dict[Tuple[str, str], List[str]],
    order_bands: Dict[Tuple[str, str, str], List[str]],
    c: str, arm: str
) -> List[str]:
    """Return all band codes in genomic order for the given arm (e.g., ['1p36','1p35',...])."""
    bands: List[str] = []
    for region_code in order_regions.get((c, arm), []):
        region_d = region_code[-1]  # region digit (single)
        bands.extend(order_bands.get((c, arm, region_d), []))
    return bands

def flatten_subbands_for_arm(
    order_regions: Dict[Tuple[str, str], List[str]],
    order_bands: Dict[Tuple[str, str, str], List[str]],
    order_subbands: Dict[Tuple[str, str, str], List[str]],
    c: str, arm: str
) -> List[str]:
    """Return all subband codes in genomic order for the given arm (e.g., ['1p36.33','1p36.32',...])."""
    subbands: List[str] = []
    for region_code in order_regions.get((c, arm), []):
        region_d = region_code[-1]
        for band_code in order_bands.get((c, arm, region_d), []):
            band_digits = band_code[-2:]  # region+band digits
            subbands.extend(order_subbands.get((c, arm, band_digits), []))
    return subbands

def find_endpoints_for_level(
    level: str,
    code_to_node: Dict[str, dict],
    order_regions: Dict[Tuple[str, str], List[str]],
    order_bands: Dict[Tuple[str, str, str], List[str]],
    order_subbands: Dict[Tuple[str, str, str], List[str]],
    c: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    For chromosome c, find (last_of_p, first_of_q) codes at the requested level.
    level in {'subband','band','region'}
    """
    # both arms must exist
    if f"{c}p" not in code_to_node or f"{c}q" not in code_to_node:
        return None, None

    if level == "region":
        p_regions = order_regions.get((c, "p"), [])
        q_regions = order_regions.get((c, "q"), [])
        return (p_regions[-1] if p_regions else None, q_regions[0] if q_regions else None)

    if level == "band":
        p_bands = flatten_bands_for_arm(order_regions, order_bands, c, "p")
        q_bands = flatten_bands_for_arm(order_regions, order_bands, c, "q")
        return (p_bands[-1] if p_bands else None, q_bands[0] if q_bands else None)

    # level == "subband"
    p_subs = flatten_subbands_for_arm(order_regions, order_bands, order_subbands, c, "p")
    q_subs = flatten_subbands_for_arm(order_regions, order_bands, order_subbands, c, "q")
    return (p_subs[-1] if p_subs else None, q_subs[0] if q_subs else None)

def cross_link_centromere(
    cs_url: str,
    code_to_node: Dict[str, dict],
    chromosomes: List[str],
    order_regions: Dict[Tuple[str, str], List[str]],
    order_bands: Dict[Tuple[str, str, str], List[str]],
    order_subbands: Dict[Tuple[str, str, str], List[str]],
    levels: List[str]
):
    """
    Add prev/next links across the centromere per chromosome for the specified levels.
    Only add a link if the side is not already set, preserving intra-arm adjacency.
    """
    for c in chromosomes:
        for level in levels:
            left, right = find_endpoints_for_level(
                level, code_to_node, order_regions, order_bands, order_subbands, c
            )
            if not left or not right:
                continue
            left_node = code_to_node.get(left)
            right_node = code_to_node.get(right)
            if not left_node or not right_node:
                continue
            # last p -> next = first q; first q -> prev = last p
            add_single_link(left_node, "next", right, cs_url)
            add_single_link(right_node, "prev", left, cs_url)

# ------------- Build function -------------

def build_codesystem(
    input_path: Path,
    output_path: Path,
    url: str,
    version: str,
    name: str,
    title: str,
    include_mito: bool = False,
    link_across_centromere: bool = False,
    centromere_levels: str = "subband"
) -> dict:
    """
    Construct the CodeSystem from a UCSC cytoBand TSV file (name-based only).
    """
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

    # Order trackers (preserve file order, which is typically genomic)
    order_arms = defaultdict(list)        # chrom -> [chromp, chromq]
    order_regions = defaultdict(list)     # (chrom, arm) -> [region codes]
    order_bands = defaultdict(list)       # (chrom, arm, regionDigit) -> [band codes]
    order_subbands = defaultdict(list)    # (chrom, arm, bandDigits) -> [subband codes]

    kept = 0
    skipped = 0

    # Read TSV (robust to tabs)
    with input_path.open("r", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        for row in reader:
            if not row or len(row) < 4:
                continue
            if row[0].startswith(("track", "browser", "#")):
                continue

            chrom = row[0].strip()
            name = row[3].strip() if len(row) >= 4 else ""

            # Normalize chromosome code (strip 'chr'), skip mitochondrion by default
            c = chrom[3:] if chrom.startswith("chr") else chrom
            if c == "M" and not include_mito:
                skipped += 1
                continue

            m = BAND_RE.match(name)
            if not m:
                # Rows lacking a valid cytoband name (e.g., many alt/random/unplaced) can't be placed
                skipped += 1
                continue

            arm = m.group("arm")              # 'p' or 'q'
            digits = m.group("digits")        # two digits: region, band
            region_d, band_d = digits[0], digits[1]
            sub = m.group("sub")              # optional sub-band digits

            # Build hierarchy
            chrom_node = ensure_chrom(top_index, cs, c)
            arm_node   = ensure_arm(chrom_node, c, arm)
            region     = ensure_region(arm_node, c, arm, region_d)
            band       = ensure_band(region, c, arm, region_d, band_d)

            # If decimal sub-band exists, create leaf under band
            if sub is not None:
                full_code = f"{c}{name}"      # e.g., '1p36.33'
                leaf = new_node(full_code, full_code)
                add_kind(leaf, "subband")
                band["concept"].append(leaf)

            # Track order (first-seen)
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

    # Link chromosomes in karyotype order 1..22, X, Y
    chrom_order = karyotype_order_present(code_to_node)
    link_seq(chrom_order, code_to_node, url)

    # Link arms, regions, bands, subbands within their parents
    for c, arms in order_arms.items():
        link_seq(arms, code_to_node, url)

    for (c, arm), regions in order_regions.items():
        link_seq(regions, code_to_node, url)

    for (c, arm, region_d), bands in order_bands.items():
        link_seq(bands, code_to_node, url)

    for (c, arm, band_digits), subs in order_subbands.items():
        link_seq(subs, code_to_node, url)

    # Optional: cross-link p <-> q across the centromere
    if link_across_centromere:
        if centromere_levels == "all":
            levels = ["subband", "band", "region"]
        else:
            levels = [centromere_levels]
        cross_link_centromere(
            url, code_to_node, chrom_order,
            order_regions, order_bands, order_subbands,
            levels
        )

    # Reorder top-level chromosomes for readability
    cs["concept"] = [code_to_node[k] for k in chrom_order]

    # Write out
    output_path.write_text(json.dumps(cs, indent=2))
    print("SUMMARY:")
    print(json.dumps({
        "kept_banded_rows": kept,
        "skipped_nonbanded_rows": skipped,
        "chromosomes_included": chrom_order,
        "centromere_cross_linking": link_across_centromere,
        "centromere_levels": centromere_levels
    }, indent=2))
    print("WROTE:", str(output_path))
    return cs

# ------------- CLI -------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Generate an assembly-agnostic FHIR R4 CodeSystem for human cytogenetic bands with prev/next links and optional centromere cross-linking."
    )
    ap.add_argument("--input", "-i", required=True, type=Path, help="UCSC cytoBand file (TSV).")
    ap.add_argument("--output", "-o", required=True, type=Path, help="Output CodeSystem JSON path.")
    ap.add_argument("--url", "-u", default="http://example.org/fhir/CodeSystem/human-cytoband-agnostic",
                    help="Canonical URL for the CodeSystem.")
    ap.add_argument("--version", "-v", default="1.2.0", help="CodeSystem.version.")
    ap.add_argument("--name", default="HumanCytogeneticBandsAssemblyAgnostic", help="CodeSystem.name")
    ap.add_argument("--title", default="Human Cytogenetic Bands (Assembly-agnostic with prev/next)",
                    help="CodeSystem.title")
    ap.add_argument("--include-mito", action="store_true",
                    help="Include mitochondrial (chrM). Default: exclude (no bands in ISCN).")
    ap.add_argument("--link-across-centromere", action="store_true",
                    help="Add prev/next links across the centromere (p↔q).")
    ap.add_argument("--centromere-levels",
                    choices=["subband", "band", "region", "all"],
                    default="subband",
                    help="Level(s) to cross-link across the centromere (default: subband).")
    return ap.parse_args()

def main():
    args = parse_args()
    build_codesystem(
        input_path=args.input,
        output_path=args.output,
        url=args.url,
        version=args.version,
        name=args.name,
        title=args.title,
        include_mito=args.include_mito,
        link_across_centromere=args.link_across_centromere,
        centromere_levels=args.centromere_levels
    )

if __name__ == "__main__":
    main()
