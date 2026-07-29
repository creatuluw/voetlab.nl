"""F6 — docs manifest test: FEATURES.md lists every feature .py and the HTML site exists."""
from pathlib import Path

from pitchkit.docs.build_docs import collect, main

PROJECT = Path(__file__).resolve().parents[3]  # .../pitchkit


def _feature_files():
    pkg = PROJECT / "pitchkit"
    out = []
    for folder in ["core", "detection", "tracking", "calibration", "events", "stats",
                   "tactics", "reliability", "viz", "pipeline"]:
        d = pkg / folder
        if d.is_dir():
            out += [p.name for p in d.glob("*.py") if p.name != "__init__.py"]
    return out


def test_manifest_and_site_in_sync():
    main()  # regenerate
    manifest = (PROJECT / "FEATURES.md").read_text(encoding="utf-8")
    for fname in _feature_files():
        assert fname in manifest, f"{fname} missing from FEATURES.md"
    assert (PROJECT / "docs" / "site" / "index.html").exists()
    # every collected feature has a docstring summary (no empty cards)
    for r in collect():
        assert r["summary"] and r["summary"] != "(no docstring)", f"{r['path']} has no docstring"
