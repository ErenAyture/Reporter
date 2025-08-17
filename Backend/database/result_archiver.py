# result_archiver.py
# -----------------------------------------------------------------------------
# A tiny utility that zips everything that belongs to one task‑group from
#   outputs/<gid>/**  →  results/<gid>.zip
# and removes the original directory afterwards.
# -----------------------------------------------------------------------------
from __future__ import annotations

from pathlib import Path
import shutil
import zipfile
from typing import Optional

__all__ = ["ResultArchiver"]


class ResultArchiver:
    """Archive helper independent of DB/ORM layers.

    Parameters
    ----------
    outputs_dir : str | Path | None  (default: <project>/outputs)
        Directory where tasks leave their raw artefacts.
    results_dir : str | Path | None  (default: <project>/results)
        Where finished *.zip* archives are collected.
    """

    def __init__(
        self,
        outputs_dir: str | Path | None = None,
        results_dir: str | Path | None = None,
    ) -> None:
        base = Path(__file__).resolve().parent.parent  # …/Backend
        self.outputs_dir: Path = Path(outputs_dir) if outputs_dir else base / "outputs"
        self.results_dir: Path = Path(results_dir) if results_dir else base / "results"

        # ensure target dir exists
        self.results_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------
    # public API
    # ---------------------------------------------------------------------

    def archive_group(self, group_id: int) -> Optional[Path]:
        """Zip *outputs/<gid>/*** → results/<gid>.zip* and delete the source.

        Returns
        -------
        Path | None
            Path to the created archive, or *None* when nothing had to be
            archived (e.g. the outputs/<gid> directory never existed).
        """
        raw_root = self.outputs_dir / str(group_id)
        if not raw_root.exists():
            return None

        tmp_zip = raw_root.with_suffix(".zip.tmp")      # outputs/<gid>.zip.tmp
        final_zip = self.results_dir / f"{group_id}.zip"

        # 1. build archive next to the data (fast, same filesystem)
        with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file in raw_root.rglob("*"):
                if file.is_file():
                    # store path relative to <gid>/... to preserve structure
                    zf.write(file, arcname=file.relative_to(self.outputs_dir))

        # 2. atomically move into the public results directory
        tmp_zip.replace(final_zip)

        # 3. remove the now‑obsolete raw directory
        shutil.rmtree(raw_root, ignore_errors=True)

        return final_zip

    def remove_archive(self, group_id: int) -> bool:
        """
        Delete *results/<gid>.zip* if it exists.

        Returns
        -------
        bool
            True  – file existed and was removed  
            False – nothing to do
        """
        zf = self.results_dir / f"{group_id}.zip"
        try:
            zf.unlink()          # raises FileNotFoundError if absent
            return True
        except FileNotFoundError:
            return False
# -----------------------------------------------------------------------------
# Example usage (remove once it is wired into task_service._recalc_group_status)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    archiver = ResultArchiver()
    created = archiver.archive_group(23)
    print("created«", created, "»" if created else "nothing to do")
