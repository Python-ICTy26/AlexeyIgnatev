import os
import pathlib
import typing as tp


def repo_find(workdir: tp.Union[str, pathlib.Path] = ".") -> pathlib.Path:
    try:
        root = os.environ["GIT_DIR"]
    except:
        root = ".git"
    workdir = str(pathlib.Path(workdir) / root).split(root)[0] + os.sep + root
    if not os.path.exists(workdir):
        raise Exception("Not a git repository")
    return pathlib.Path(workdir)


def repo_create(workdir: tp.Union[str, pathlib.Path]) -> pathlib.Path:
    try:
        root = os.environ["GIT_DIR"]
    except:
        root = ".git"
    workdir = pathlib.Path(workdir)
    if workdir.is_file():
        raise Exception(f"{workdir.name} is not a directory")

    os.makedirs(workdir / root / "refs" / "tags")
    os.makedirs(workdir / root / "refs" / "heads")
    os.makedirs(workdir / root / "objects")

    with open(workdir / root / "HEAD", "w") as f:
        f.write("ref: refs/heads/master\n")

    with open(workdir / root / "config", "w") as f:
        f.write(
            "[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n\tlogallrefupdates = false\n")

    with open(workdir / root / "description", "w") as f:
        f.write("Unnamed pyvcs repository.\n")

    return pathlib.Path(workdir / root)
