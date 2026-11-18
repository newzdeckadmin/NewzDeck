"""Safe completed-download flattening for NewzDeck v3.7.33.

Download, repair and unpack stay inside job-specific staging directories.
Only verified, fully completed output is promoted to the configured root when
Extract into a subfolder is disabled. A persist-before-move name plan and an
atomic no-clobber hard link make retries safe after interruptions. The caller
owns the persisted plan and the completion/ownership checks.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable


def flatten_completed_folder(source: Path, root: Path, plan: dict[str, str],
                             save_plan: Callable[[dict[str, str]], None]) -> dict[str, str]:
    """Promote completed payloads to root without overwrites, or fail closed.

    `plan` maps the original job-relative path to the unique final basename.
    The plan is durably saved BEFORE the first link, allowing a restart to
    recognize a link created just before the process was interrupted.
    A failed operation leaves any remaining source data in the staging folder.
    """
    root = Path(root).expanduser().resolve(strict=True)
    source = Path(source).expanduser()
    if source.is_symlink():
        raise ValueError('Refusing to flatten a symlinked completed-download folder')
    source = source.resolve(strict=True)
    if source == root or root not in source.parents or not source.is_dir():
        raise ValueError('Completed source must be a job directory within the Download Folder')
    if not isinstance(plan, dict):
        raise ValueError('Invalid persisted completed-download name plan')
    # Validate every persisted entry, including entries whose source was
    # already removed in a previous pass. No traversal or alternate roots.
    for rel, name in plan.items():
        relpath = Path(rel)
        if (not rel or relpath.is_absolute() or '..' in relpath.parts
                or not name or Path(name).name != name or name in ('.', '..')):
            raise ValueError('Unsafe completed-download name plan')
    files = []
    dirs = []
    for current, children, filenames in os.walk(source, followlinks=False):
        folder = Path(current)
        for name in children:
            child = folder / name
            if child.is_symlink():
                raise ValueError('Refusing to flatten a symlinked archive directory')
            dirs.append(child)
        for name in filenames:
            child = folder / name
            if child.is_symlink() or not child.is_file():
                raise ValueError('Refusing to flatten an unsafe archive entry')
            files.append(child)
    if not files and not plan:
        raise RuntimeError("Completed NZB has no files to finalize")
    reserved = {name.casefold() for name in plan.values()}
    for item in sorted(files, key=lambda entry: entry.relative_to(source).as_posix().casefold()):
        rel = item.relative_to(source).as_posix()
        name = plan.get(rel)
        preferred = item.name
        stem, suffix = Path(preferred).stem, Path(preferred).suffix
        index = 1
        while True:
            if name is None:
                proposed = preferred if index == 1 else f'{stem} ({index}){suffix}'
                if proposed.casefold() in reserved or (root / proposed).exists():
                    index += 1
                    continue
                next_plan = dict(plan)
                next_plan[rel] = proposed
                save_plan(next_plan)  # durable before touching source bytes
                plan.clear()
                plan.update(next_plan)
                reserved.add(proposed.casefold())
                name = proposed
            destination = root / name
            if destination.exists():
                try:
                    if os.path.samefile(item, destination):
                        item.unlink()  # interrupted between atomic link and unlink
                        break
                except OSError:
                    pass
                # Another file already owned the planned basename. Persist a
                # fresh distinct destination, never overwrite or silently skip.
                reserved.discard(name.casefold())
                plan.pop(rel, None)
                name = None
                index += 1
                continue
            try:
                os.link(item, destination)  # atomic, fails if destination exists
            except FileExistsError:
                # An interrupted/concurrent link of this SAME source is not a
                # collision. Finish its unlink instead of creating a duplicate.
                try:
                    if destination.is_file() and os.path.samefile(item, destination):
                        item.unlink()
                        break
                except OSError:
                    pass
                # Another file owns this name; never overwrite it.
                reserved.discard(name.casefold())
                plan.pop(rel, None)
                name = None
                index += 1
                continue
            # NTFS supports hard links. If the destination volume does not,
            # retain the complete job folder instead of risking a partial copy.
            item.unlink()
            break
    # An earlier pass may have unlinked all sources but crashed before cleanup.
    # Every planned final output must still exist before removing the job folder.
    for name in plan.values():
        dest = root / name
        if not dest.is_file() or dest.is_symlink():
            raise RuntimeError('A previously finalized file is missing; staging folder preserved')
    for folder in sorted(dirs, key=lambda value: len(value.parts), reverse=True):
        folder.rmdir()  # fail closed if SAB or another process left any residue
    source.rmdir()
    return dict(plan)
