---
type: Rule
title: Verify FTP-uploaded model weights by byte size before trusting them
description: Guideline
tags: [models, weights, deployment, ftp, devops, voetlab.nl, verification]
timestamp: "2026-07-29T21:30:33.327Z"
---

# Verify FTP-uploaded model weights by byte size before trusting them

## Guideline

After FTP-uploading the `models/*.pt` bundle to `voetlab.nl/models/` (the Apache box at
`92.205.3.167`), **verify every served file matches the local file by `Content-Length` /
byte size** before treating the deploy as good. Do a size-checking pass, not just a 200-OK
probe.

```bash
# verify each served weight matches the local bundle, byte-for-byte
for f in yolov8s.pt martinjolif_ball.pt rajatdave_ball.pt yaku_ball.pt tvcalib_calib_train59.pt; do
  remote=$(curl -sI "https://voetlab.nl/models/$f" | awk -F': ' 'tolower($1)=="content-length"{gsub(/\r/,"",$2);print $2}')
  local_sz=$(stat -c%s "models/$f" 2>/dev/null || stat -f%z "models/$f")
  echo "$f  remote=$remote  local=$local_sz  $([ "$remote" = "$local_sz" ] && echo OK || echo MISMATCH)"
done
```

If a size mismatches, re-upload that one file — a truncated checkpoint will fail at
`torch.load` time (or silently corrupt a run), not at upload time.

## When it applies

Every time the `models/` bundle (see [[learnings/models-folder-is-ftp-deploy-bundle]]) is
re-deployed or refreshed to `voetlab.nl/models/`. Especially the large TVCalib checkpoint
(`tvcalib_calib_train59.pt`, ~488 MB) — the bigger the file, the more likely an FTP transfer
lands short.

## Rationale

Observed first-hand: after FTP'ing the bundle, `tvcalib_calib_train59.pt` served fine (HTTP
200, ~488 MB) but was **~543 KB smaller** than the local copy — a truncated FTP upload. A bare
`curl -I` returning 200 would have looked like success. The smaller ball/detector weights
happened to match exactly, so size verification caught the one bad file. FTP gives no
end-to-end integrity guarantee; a size check is the smallest reliable integrity signal short
of a full checksum (add an md5 compare only if a size match ever proves insufficient).

## Relationships

- [[learnings/models-folder-is-ftp-deploy-bundle]] — the `models/` bundle this rule verifies.
- [[learnings/model-weights-are-hosted-at-voetlab-nl-models]] — the canonical download host being kept correct.
- [[rules/gitignore-large-checkpoints-document-the-download-instead]] — why the binaries are FTP'd instead of committed.
