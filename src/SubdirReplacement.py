from dataclasses import dataclass


@dataclass
class SubdirReplacement:
    subdir_rel: str
    replacement: str
