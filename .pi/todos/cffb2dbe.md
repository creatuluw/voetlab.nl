{
  "id": "cffb2dbe",
  "title": "Rename package dir pitchkit/ → voetlab/ + botsort yaml",
  "tags": [],
  "status": "done",
  "created_at": "2026-07-29T17:27:11.196Z"
}

git mv pitchkit voetlab; git mv voetlab/tracking/pitchkit_botsort.yaml voetlab/tracking/voetlab_botsort.yaml. Update any sys.path / conftest referencing the dir.
