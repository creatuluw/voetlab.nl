"""pitchkit — standalone football video-analytics framework.

A self-contained, copyable framework: detection, tracking, pitch calibration,
event detection, physical/tactical stats, and viz. One distinct feature per file,
folder per domain, co-located footage-driven tests.

Conventions (see docs/wiki/rules/pitchkit-framework-conventions-*.md):
  * every feature returns `core.result.Result` (ok / value / error / meta)
  * every event carries frame provenance via `core.provenance`
  * every feature file has a footage-driven test that dumps inspectable artifacts

No repo-specific imports inside this package — copy the folder or `pip install -e`.
"""

__version__ = "0.1.0"

# Top-level convenience API: `import pitchkit; pitchkit.run(video)`.
from pitchkit.pipeline.default import run, run_feature

__all__ = ["run", "run_feature", "__version__"]
