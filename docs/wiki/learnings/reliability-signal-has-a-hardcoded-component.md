---
type: Learning
title: Reliability signal has a hardcoded component
description: The `reliability` domain publishes a per-stat trust signal, but not all of its
tags: [reliability, calibration, gotcha, limitation]
timestamp: "2026-07-29T17:22:43.126Z"
---

# Reliability signal has a hardcoded component

The `reliability` domain publishes a per-stat trust signal, but not all of its
components are actually measured. Reading the source (`pitchkit/reliability/`)
reveals two honest limitations that affect how the composite scores should be
interpreted:

- **`homography_conf` is hardcoded to `1.0`** — it does NOT reflect how good the
  pitch calibration actually was. So a run with a shaky/failed `H` still reports
  full confidence on the calibration axis.
- **`tracking_stability` is a proxy**, not a true tracker-quality metric — it's
  derived from tracking output heuristics rather than a ground-truth comparison.

The genuinely measured components are `ball_coverage`, `interpolation_ratio`,
and the composites built from them.

**Why it matters:** Anyone building on PREDA/pitchkit stats or debugging
"why is reliability X?" must know the calibration axis of the reliability score
is currently a constant, not a real signal. Documented (as of the refreshed
README) in `pitchkit/reliability/README.md` under Quality & limitations.
