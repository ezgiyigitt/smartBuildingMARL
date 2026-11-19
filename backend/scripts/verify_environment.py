"""Print interpreter, optional CityLearn import, and dataset names. Does not download ASHRAE."""

from __future__ import annotations

import json
import sys
from importlib import metadata


def main() -> int:
    report: dict[str, object] = {
        "python": sys.version,
        "executable": sys.executable,
        "python_ok": sys.version_info[:2] == (3, 11),
        "citylearn_installed": False,
        "citylearn_version": None,
        "dataset_names": None,
        "import_error": None,
    }
    try:
        import citylearn
        from citylearn.data import DataSet

        report["citylearn_installed"] = True
        report["citylearn_version"] = getattr(citylearn, "__version__", metadata.version("CityLearn"))
        try:
            names = DataSet().get_dataset_names()
        except AttributeError:
            names = DataSet.get_names()  # type: ignore[attr-defined]
        report["dataset_names"] = names
    except Exception as exc:  # noqa: BLE001 — environment probe
        report["import_error"] = f"{type(exc).__name__}: {exc}"
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["python_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
