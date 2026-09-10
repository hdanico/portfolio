#!/usr/bin/env python3
"""
Build the deploy copy of the portfolio.

Copies every .html page, favicon.svg, and only the assets actually referenced
by those pages into DST, preserving paths. Nothing from the 592 MB of source
material (case-study originals, .mov, brand decks) is touched.

Re-run this after editing pages in SRC, then commit + push from DST.

    python3 build.py
"""
import os, re, html, urllib.parse, shutil, sys

SRC = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(os.path.dirname(SRC), "portfolio")
DOMAIN = "www.gracedanico.com"

ATTR = re.compile(r'(?:src|href|poster|data-src|srcset)="([^"]+)"')

# Files referenced only from <meta> tags (og:image etc.), not from src/href.
EXTRA = ["About/og-cover.jpg"]

def referenced_assets():
    out = set()
    for f in os.listdir(SRC):
        if not f.endswith(".html"):
            continue
        t = open(os.path.join(SRC, f), encoding="utf-8").read()
        for m in ATTR.finditer(t):
            raw = html.unescape(m.group(1)).strip()
            parts = raw.split(",") if " " in raw and raw.count(" ") and "srcset" in m.group(0) else [raw]
            for part in parts:
                v = part.strip().split(" ")[0]
                if not v or v.startswith(("http://", "https://", "data:", "#", "mailto:", "tel:", "//")):
                    continue
                v = urllib.parse.unquote(v.split("#")[0].split("?")[0])
                if v and not v.endswith(".html"):
                    out.add(v)
    return out

def main():
    if os.path.isdir(DST):
        # wipe everything except the .git dir
        for name in os.listdir(DST):
            if name == ".git":
                continue
            p = os.path.join(DST, name)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    else:
        os.makedirs(DST)

    copied = 0

    # pages + favicon
    for f in os.listdir(SRC):
        if f.endswith(".html") or f == "favicon.svg":
            shutil.copy2(os.path.join(SRC, f), os.path.join(DST, f))
            copied += 1

    # referenced assets
    missing = []
    for rel in sorted(referenced_assets() | set(EXTRA)):
        s = os.path.join(SRC, rel)
        if not os.path.isfile(s):
            missing.append(rel)
            continue
        d = os.path.join(DST, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)
        copied += 1

    # GitHub Pages support files
    open(os.path.join(DST, ".nojekyll"), "w").close()
    open(os.path.join(DST, "CNAME"), "w").write(DOMAIN + "\n")
    open(os.path.join(DST, ".gitignore"), "w").write(".DS_Store\nnode_modules/\n")
    shutil.copy2(os.path.abspath(__file__), os.path.join(DST, "build.py"))
    open(os.path.join(DST, "README.md"), "w").write(
        "# gracedanico.com\n\n"
        "Static portfolio. Deployed via GitHub Pages from the repo root.\n\n"
        "Pages and assets are generated into this repo by `build.py`, which lives\n"
        "with the working files and copies only what the pages reference. Edit the\n"
        "source, re-run `python3 build.py`, then commit and push.\n"
    )

    # strip .DS_Store if any slipped in
    for dp, _, fs in os.walk(DST):
        for f in fs:
            if f == ".DS_Store":
                os.remove(os.path.join(dp, f))

    total = 0
    for dp, dn, fs in os.walk(DST):
        if ".git" in dp.split(os.sep):
            continue
        for f in fs:
            total += os.path.getsize(os.path.join(dp, f))

    print(f"built {DST}")
    print(f"  {copied} files copied, {total/1e6:.1f} MB total")
    if missing:
        print("  !! referenced but missing in source:")
        for m in missing:
            print("     ", m)
        sys.exit(1)

if __name__ == "__main__":
    main()
