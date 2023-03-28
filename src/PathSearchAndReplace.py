from pathlib import Path
from typing import List
from SubdirReplacement import SubdirReplacement


class PathSearchAndReplace:
    def __init__(self, replacements: List[SubdirReplacement]):
        self.replacements = replacements

    def replace_path(self, path: Path) -> Path:
        for replacement in self.replacements:
            if replacement.subdir_rel == "/":
                return Path(replacement.replacement).joinpath(path)
            if replacement.subdir_rel in path.parts:
                path_parts = list(path.parts)
                for i, part in enumerate(path_parts):
                    if part == replacement.subdir_rel:
                        path_parts[i] = replacement.replacement
                        break  # stop after the first replacement
                return Path(*path_parts)
        return path
