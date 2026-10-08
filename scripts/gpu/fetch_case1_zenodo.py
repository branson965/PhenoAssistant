"""Fetch and validate the official Case 1 Arabidopsis dataset from Zenodo.

Compatible with the Plato login-node Python 3.9 standard library. The script:
- resolves the official Zenodo record via API;
- downloads the archive with a partial-file guard;
- verifies size and the Zenodo checksum when available;
- extracts into a staging directory with path-traversal protection;
- locates the AraCropData directory automatically;
- installs it at data/AraCropData without overwriting an existing dataset;
- validates all 1,248 metadata-referenced images.

No GPU or third-party Python package is required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECORD_API = "https://zenodo.org/api/records/18940282"
ARCHIVE_KEY = "arabidopsis-thaliana-dataset.zip"
EXPECTED_IMAGES = 1248
METADATA = ROOT / "data" / "aracrop_metadata.json"
DOWNLOAD_DIR = ROOT / "data" / "_downloads"
STAGING_DIR = ROOT / "data" / "_staging" / "arabidopsis_case1"
TARGET = ROOT / "data" / "AraCropData"


def _json_url(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "PhenoAssistant-Phase5/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def _hash(path, algorithm):
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_extract(archive, destination):
    destination = destination.resolve()
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        try:
            target.relative_to(destination)
        except ValueError:
            raise RuntimeError(
                "unsafe path in archive: {}".format(member.filename)
            )
    archive.extractall(str(destination))


def _locate_aracrop_root(staging):
    candidates = []
    for plant_one in staging.rglob("Plant_1"):
        if plant_one.is_dir():
            parent = plant_one.parent
            plant_dirs = [
                path for path in parent.iterdir()
                if path.is_dir() and path.name.startswith("Plant_")
            ]
            if plant_dirs:
                candidates.append(parent)

    unique = []
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(candidate)

    if len(unique) != 1:
        raise RuntimeError(
            "expected exactly one AraCropData-like root, found {}: {}".format(
                len(unique),
                [str(path) for path in unique[:10]],
            )
        )
    return unique[0]


def _metadata_paths():
    payload = json.loads(METADATA.read_text(encoding="utf-8"))
    images = payload.get("file_name")
    if not isinstance(images, list):
        raise TypeError("metadata file_name must be a list")
    return [ROOT / str(value).removeprefix("./") for value in images]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--keep-archive",
        action="store_true",
        help="retain the downloaded ZIP after successful validation",
    )
    args = parser.parse_args()

    if not METADATA.is_file():
        raise FileNotFoundError(METADATA)

    expected_paths = _metadata_paths()
    if TARGET.exists():
        missing = [path for path in expected_paths if not path.is_file()]
        if not missing and len(expected_paths) == EXPECTED_IMAGES:
            print(
                json.dumps(
                    {
                        "status": "already_ready",
                        "target": str(TARGET.relative_to(ROOT)),
                        "images": len(expected_paths),
                    },
                    sort_keys=True,
                )
            )
            return
        raise RuntimeError(
            "data/AraCropData already exists but does not satisfy the "
            "Case 1 metadata; refusing to overwrite it."
        )

    record = _json_url(RECORD_API)
    files = record.get("files", [])
    entry = next(
        (item for item in files if item.get("key") == ARCHIVE_KEY),
        None,
    )
    if entry is None:
        raise RuntimeError(
            "official Zenodo record does not contain {}".format(ARCHIVE_KEY)
        )

    url = entry.get("links", {}).get("self")
    if not url:
        raise RuntimeError("Zenodo file entry has no content URL")

    expected_size = int(entry.get("size", 0))
    checksum = str(entry.get("checksum") or "")

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = DOWNLOAD_DIR / ARCHIVE_KEY
    partial_path = archive_path.with_suffix(archive_path.suffix + ".part")

    if not archive_path.is_file():
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "PhenoAssistant-Phase5/1.0"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            with partial_path.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
        partial_path.replace(archive_path)

    actual_size = archive_path.stat().st_size
    if expected_size and actual_size != expected_size:
        raise RuntimeError(
            "download size mismatch: expected {}, got {}".format(
                expected_size, actual_size
            )
        )

    checksum_ok = None
    checksum_algorithm = None
    checksum_expected = None
    checksum_actual = None
    if ":" in checksum:
        checksum_algorithm, checksum_expected = checksum.split(":", 1)
        checksum_actual = _hash(archive_path, checksum_algorithm)
        checksum_ok = checksum_actual.lower() == checksum_expected.lower()
        if not checksum_ok:
            raise RuntimeError(
                "{} checksum mismatch".format(checksum_algorithm)
            )

    if STAGING_DIR.exists():
        shutil.rmtree(str(STAGING_DIR))
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(str(archive_path), "r") as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise RuntimeError(
                "ZIP integrity failure at {}".format(bad_member)
            )
        _safe_extract(archive, STAGING_DIR)

    source = _locate_aracrop_root(STAGING_DIR)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(TARGET))

    missing = [path for path in expected_paths if not path.is_file()]
    if missing:
        raise RuntimeError(
            "dataset extracted but {} metadata-referenced images are "
            "still missing; first five: {}".format(
                len(missing),
                [str(path.relative_to(ROOT)) for path in missing[:5]],
            )
        )

    if len(expected_paths) != EXPECTED_IMAGES:
        raise RuntimeError(
            "metadata expected {} images but contains {}".format(
                EXPECTED_IMAGES, len(expected_paths)
            )
        )

    if not args.keep_archive:
        archive_path.unlink()

    print(
        json.dumps(
            {
                "status": "ready",
                "zenodo_record_id": record.get("id"),
                "archive": ARCHIVE_KEY,
                "archive_size_bytes": actual_size,
                "checksum": {
                    "declared": checksum or None,
                    "algorithm": checksum_algorithm,
                    "expected": checksum_expected,
                    "actual": checksum_actual,
                    "verified": checksum_ok,
                },
                "target": str(TARGET.relative_to(ROOT)),
                "metadata_images": len(expected_paths),
                "existing_images": len(expected_paths),
                "missing_images": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
