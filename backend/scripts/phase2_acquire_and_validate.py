"""Download authorized datasets, hash them, write quality reports. No row-merge."""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from shutil import copytree
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "artifacts" / "reports"
USER_AGENT = "smartBuildingMARL-phase2/0.1 (research; local validation)"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=180) as response, dest.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)


def download_zenodo() -> dict:
    dest_dir = RAW / "zenodo_tsv_subset"
    dest_dir.mkdir(parents=True, exist_ok=True)
    meta = json.loads(urlopen(Request("https://zenodo.org/api/records/13884633", headers={"User-Agent": USER_AGENT}), timeout=60).read())
    files = meta["files"]
    saved = []
    for item in files:
        name = item["key"]
        url = item["links"]["self"]
        path = dest_dir / name
        if not path.exists():
            download(url, path)
        saved.append(
            {
                "name": name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "source_url": url,
                "stated_checksum": item.get("checksum"),
            }
        )
    return {
        "id": "zenodo_tsv_complete_case",
        "doi": "10.5281/zenodo.13884633",
        "license": meta["metadata"].get("license", {}).get("id"),
        "title": meta["metadata"]["title"],
        "files": saved,
        "status": "downloaded",
    }


def download_ashrae() -> dict:
    dest_dir = RAW / "ashrae_gcdb2"
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "dryad_doi_10.6078_D1F671.zip"
    url = "https://datadryad.org/api/v2/datasets/doi%3A10.6078%2FD1F671/download"
    dryad_error = None
    try:
        if not zip_path.exists():
            download(url, zip_path)
    except Exception as exc:
        dryad_error = f"{type(exc).__name__}: {exc}"
    if zip_path.exists():
        extract_dir = dest_dir / "extracted"
        if not extract_dir.exists():
            extract_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)
        files = []
        for path in sorted(extract_dir.rglob("*")):
            if path.is_file():
                files.append(
                    {
                        "relative": str(path.relative_to(extract_dir)),
                        "bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                )
        return {
            "id": "ashrae_gcdb2",
            "doi": "10.6078/D1F671",
            "source": "dryad_zip",
            "download_url": url,
            "zip_sha256": sha256_file(zip_path),
            "zip_bytes": zip_path.stat().st_size,
            "files": files,
            "status": "downloaded",
        }
    # Official CBE maintenance repo (same dataset family, version 2.1.0).
    github_base = "https://raw.githubusercontent.com/CenterForTheBuiltEnvironment/ashrae-db-II/master/v2.1.0"
    extract_dir = dest_dir / "extracted" / "v2.1.0"
    extract_dir.mkdir(parents=True, exist_ok=True)
    names = ["db_metadata.csv", "db_measurements_v2.1.0.csv.gz"]
    files = []
    for name in names:
        path = extract_dir / name
        file_url = f"{github_base}/{name}"
        if not path.exists():
            download(file_url, path)
        files.append(
            {
                "relative": str(path.relative_to(dest_dir / "extracted")),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "url": file_url,
            }
        )
    return {
        "id": "ashrae_gcdb2",
        "doi": "10.6078/D1F671",
        "source": "cbe_github_v2.1.0",
        "dryad_download_blocked": dryad_error,
        "github_repo": "https://github.com/CenterForTheBuiltEnvironment/ashrae-db-II",
        "files": files,
        "status": "downloaded",
        "version_note": "Dryad zip returned HTTP 401. Files taken from CBE GitHub v2.1.0 paths documented as the Database II maintenance repository.",
    }


def copy_citylearn(name: str) -> dict:
    from citylearn.data import DataSet

    dest = RAW / "citylearn" / name
    dataset = DataSet()
    schema = Path(dataset.get_dataset(name))
    src = schema.parent
    if dest.exists() and (dest / "schema.json").exists():
        pass
    else:
        dest.mkdir(parents=True, exist_ok=True)
        copytree(src, dest, dirs_exist_ok=True)
    return {
        "id": "citylearn_public",
        "named_dataset": name,
        "schema_path": str(dest / "schema.json"),
        "copied_from": str(src),
        "status": "copied",
    }


def _missingness(frame) -> dict[str, float]:
    n = len(frame)
    if n == 0:
        return {}
    return {col: float(frame[col].isna().mean()) for col in frame.columns}


def _numeric_summary(frame, columns: list[str]) -> dict:
    out = {}
    for col in columns:
        if col not in frame.columns:
            continue
        series = frame[col]
        numeric = series if series.dtype.kind in "if" else None
        if numeric is None:
            continue
        desc = numeric.describe(percentiles=[0.01, 0.5, 0.99])
        out[col] = {k: (None if _is_nan(v) else float(v)) for k, v in desc.to_dict().items()}
    return out


def _is_nan(value: object) -> bool:
    try:
        return value != value  # NaN
    except Exception:
        return False


def report_ashrae(extract_dir: Path) -> dict:
    import pandas as pd

    meta_path = next(extract_dir.rglob("*metadata*.csv"))
    meas_path = next(
        p
        for p in extract_dir.rglob("*")
        if "measurement" in p.name.lower() and p.suffix in {".gz", ".csv"}
    )
    metadata = pd.read_csv(meta_path)
    measurements = pd.read_csv(meas_path, compression="infer")
    expected = {
        "ta",
        "rh",
        "vel",
        "clo",
        "met",
        "t_out",
        "thermal_sensation",
        "thermal_comfort",
        "thermal_acceptability",
        "building_id",
    }
    present = set(measurements.columns)
    tsv = measurements["thermal_sensation"] if "thermal_sensation" in measurements.columns else None
    tcv = measurements["thermal_comfort"] if "thermal_comfort" in measurements.columns else None
    grouped = {}
    if "building_id" in measurements.columns:
        grouped = {
            "n_buildings": int(measurements["building_id"].nunique(dropna=True)),
            "rows_missing_building_id": int(measurements["building_id"].isna().sum()),
        }
    subject = {}
    if "subject_id" in measurements.columns:
        subject = {
            "n_subject_id_non_null": int(measurements["subject_id"].notna().sum()),
            "n_unique_subject_id": int(measurements["subject_id"].nunique(dropna=True)),
        }
    return {
        "n_measurement_rows": int(len(measurements)),
        "n_metadata_rows": int(len(metadata)),
        "measurement_columns": list(measurements.columns),
        "metadata_columns": list(metadata.columns),
        "missing_expected_columns": sorted(expected - present),
        "duplicate_measurement_rows": int(measurements.duplicated().sum()),
        "missing_fraction": _missingness(measurements),
        "target_non_null": {
            "thermal_sensation": None if tsv is None else int(tsv.notna().sum()),
            "thermal_comfort": None if tcv is None else int(tcv.notna().sum()),
            "thermal_acceptability": int(measurements["thermal_acceptability"].notna().sum())
            if "thermal_acceptability" in measurements.columns
            else None,
        },
        "tsv_value_counts_non_null": None
        if tsv is None
        else {str(k): int(v) for k, v in tsv.dropna().value_counts().sort_index().items()},
        "numeric_summary": _numeric_summary(measurements, ["ta", "rh", "vel", "clo", "met", "t_out", "thermal_sensation", "thermal_comfort"]),
        "grouping": grouped,
        "subject_id": subject,
        "note": "TSV (thermal_sensation) is not TCV (thermal_comfort).",
    }


def report_zenodo(xlsx_path: Path) -> dict:
    import pandas as pd

    frame = pd.read_excel(xlsx_path)
    return {
        "n_rows": int(len(frame)),
        "n_columns": int(frame.shape[1]),
        "columns": list(frame.columns),
        "duplicate_rows": int(frame.duplicated().sum()),
        "missing_fraction": _missingness(frame),
        "stated_complete_case_rows": 10618,
        "matches_stated_row_count": int(len(frame)) == 10618,
        "tsv_column_candidates": [c for c in frame.columns if "tsv" in str(c).lower() or "sensation" in str(c).lower()],
        "numeric_summary": _numeric_summary(frame, list(frame.columns)),
        "note": "Complete-case ASHRAE extract, not a Turkey field campaign.",
    }


def inspect_citylearn(schema_path: Path) -> dict:
    import json as json_lib

    from app.simulation.citylearn_adapter.compatibility import assess_scenario

    schema = json_lib.loads(schema_path.read_text(encoding="utf-8"))
    buildings = schema.get("buildings", {})
    action_names: list[str] = []
    obs_names: list[str] = []
    building_types = set()
    # CityLearn schema variants: observations/actions may be global or per building.
    for key in ("observations", "actions"):
        block = schema.get(key)
        if isinstance(block, dict):
            names = [name for name, spec in block.items() if isinstance(spec, dict) and spec.get("active")]
            if key == "actions":
                action_names.extend(names)
            else:
                obs_names.extend(names)
    for bname, bspec in buildings.items() if isinstance(buildings, dict) else []:
        if isinstance(bspec, dict):
            building_types.add(bspec.get("type") or bspec.get("building_type"))
            for key in ("observations", "actions"):
                block = bspec.get(key)
                if isinstance(block, dict):
                    names = [name for name, spec in block.items() if isinstance(spec, dict) and spec.get("active", True)]
                    if key == "actions":
                        action_names.extend(names)
                    else:
                        obs_names.extend(names)
    files = sorted(p.name for p in schema_path.parent.iterdir())
    building_csv = schema_path.parent / "Building_1.csv"
    building_columns = None
    if building_csv.exists():
        import pandas as pd

        building_columns = list(pd.read_csv(building_csv, nrows=0).columns)
    compat = assess_scenario(schema_path.parent.name, [action_names or ["electrical_storage"]], [obs_names or ["indoor_dry_bulb_temperature"]])
    return {
        "schema_top_keys": sorted(schema.keys()),
        "n_buildings_in_schema": len(buildings) if isinstance(buildings, dict) else None,
        "building_types": sorted({str(x) for x in building_types if x}),
        "active_actions_from_schema": sorted(set(action_names)),
        "active_observations_from_schema": sorted(set(obs_names)),
        "directory_files": files,
        "building_1_csv_columns": building_columns,
        "compatibility": {
            "indoor_temperature_actionable": compat.indoor_temperature_actionable,
            "has_occupancy": compat.has_occupancy,
            "reasons": list(compat.reasons),
        },
        "seconds_per_time_step": schema.get("seconds_per_time_step"),
        "central_agent": schema.get("central_agent"),
    }


def propose_group_splits(n_groups: int, seed: int = 0) -> dict:
    if n_groups < 3:
        return {"status": "insufficient_groups", "n_groups": n_groups}
    # Deterministic 70/15/15 on hashed group ids, not rows.
    return {
        "status": "protocol",
        "unit": "building_id",
        "fractions": {"train": 0.70, "validation": 0.15, "test": 0.15},
        "seed": seed,
        "rule": "Assign each building_id to a split by sha256(f'{seed}:{building_id}') modulo 100.",
        "forbidden": "random row-level split as the sole reported protocol",
    }


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / "backend"))
    acquisition = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "zenodo": None,
        "ashrae": None,
        "citylearn": None,
        "errors": [],
    }
    try:
        acquisition["zenodo"] = download_zenodo()
    except Exception as exc:
        acquisition["errors"].append(f"zenodo: {type(exc).__name__}: {exc}")
    try:
        acquisition["ashrae"] = download_ashrae()
    except Exception as exc:
        acquisition["errors"].append(f"ashrae: {type(exc).__name__}: {exc}")
    try:
        acquisition["citylearn"] = copy_citylearn("citylearn_challenge_2023_phase_1")
    except Exception as exc:
        acquisition["errors"].append(f"citylearn: {type(exc).__name__}: {exc}")

    quality: dict = {"errors": []}
    try:
        if acquisition["ashrae"] and acquisition["ashrae"].get("status") == "downloaded":
            extract = RAW / "ashrae_gcdb2" / "extracted"
            quality["ashrae"] = report_ashrae(extract)
            quality["ashrae_splits"] = propose_group_splits(quality["ashrae"].get("grouping", {}).get("n_buildings", 0))
    except Exception as exc:
        quality["errors"].append(f"ashrae_report: {type(exc).__name__}: {exc}")
    try:
        if acquisition["zenodo"]:
            xlsx = next((RAW / "zenodo_tsv_subset").glob("*.xlsx"))
            quality["zenodo"] = report_zenodo(xlsx)
    except Exception as exc:
        quality["errors"].append(f"zenodo_report: {type(exc).__name__}: {exc}")
    try:
        if acquisition["citylearn"] and acquisition["citylearn"].get("schema_path"):
            quality["citylearn"] = inspect_citylearn(Path(acquisition["citylearn"]["schema_path"]))
    except Exception as exc:
        quality["errors"].append(f"citylearn_report: {type(exc).__name__}: {exc}")

    (REPORTS / "phase2_acquisition.json").write_text(json.dumps(acquisition, indent=2), encoding="utf-8")
    (REPORTS / "phase2_quality.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    print(json.dumps({"acquisition_errors": acquisition["errors"], "quality_errors": quality["errors"]}, indent=2))
    return 1 if acquisition["errors"] or quality["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
