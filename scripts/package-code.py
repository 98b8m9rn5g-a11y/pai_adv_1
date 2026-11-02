"""Package only project source, excluding course PDFs, notebooks, and build output."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
output = root / "output" / "pai-delivery-code.zip"
output.parent.mkdir(exist_ok=True)
entries = [root / name for name in ("README.md", "compose.yaml", ".dockerignore", ".gitignore")]
for folder in ("docker", "simulation", "scripts", "ros2_ws/src"):
    entries.extend((root / folder).rglob("*"))
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(entries):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            archive.write(path, Path("pai-delivery") / path.relative_to(root))
print(output)
