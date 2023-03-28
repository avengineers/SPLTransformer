from pathlib import Path

from transformer import PathSearchAndReplace, SubdirReplacement


def test_replace_path_root():
    replacements = [SubdirReplacement("/", "root")]
    psar = PathSearchAndReplace(replacements)
    assert psar.replace_path(Path("my/path")) == Path("root/my/path")


def test_replace_path_no_match():
    replacements = [
        SubdirReplacement("foo", "bar"),
        SubdirReplacement("baz", "qux"),
    ]
    psar = PathSearchAndReplace(replacements)
    my_path = Path("/path/to/file.txt")
    assert psar.replace_path(my_path) == my_path


def test_replace_path_single_match():
    replacements = [
        SubdirReplacement("foo", "bar"),
        SubdirReplacement("baz", "qux"),
    ]
    psar = PathSearchAndReplace(replacements)
    assert psar.replace_path(Path("path/to/foo/file.txt")) == Path(
        "path/to/bar/file.txt"
    )


def test_replace_path_multiple_matches():
    replacements = [
        SubdirReplacement("foo", "bar"),
        SubdirReplacement("baz", "qux"),
    ]
    psar = PathSearchAndReplace(replacements)
    my_path = Path("path/to/baz/quux/foo/file.txt")
    assert psar.replace_path(my_path) == Path("path/to/baz/quux/bar/file.txt")
