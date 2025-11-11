import argparse
import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Generator

from watchfiles import watch

DEFAULT_PATH_TO_ANYLOGIC = "C:/Program Files/AnyLogic 8.9 Professional"

logger = logging.getLogger("export_anylogic_model")
logFormatter = logging.Formatter("[%(levelname)s] %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)


def export_model(path_to_model: str, anylogic_dir: str) -> None:
    path_to_model = model_path(path_to_model)
    for raw_path in (anylogic_dir,):
        path = Path(raw_path)
        if not path.is_absolute():
            raise ValueError(
                f"{raw_path} is not an absolute path."
                "You must provide the absolute path to the .alp/.alpx.\n"
                "On Windows, this begins with the drive, e.g., 'c:/a/b'.\n"
                "On macOS/Linux, this begins with the root '/a/b'"
            )
    subprocess.run(
        ["anylogic", "-e", path_to_model],
        cwd=anylogic_dir,
        shell=True,
    )


def model_path(path_to_model: str) -> Path:
    path = Path(path_to_model)
    if Path(path).suffix not in {".alp", ".alpx"}:
        raise ValueError(f"Path is not to an AnyLogic model file: {path}")
    if not path.exists():
        raise ValueError(f"Path {path} does not exist.")
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def remove_chrome_reference(file_path: Path) -> None:
    """Remove a reference to `chrome` that will fail in the CI environment since
    `chromium/` is ignored by Git. Chrome isn't needed for a headless experiment anyways.

    Args:
        file_path (Path): Path to a `*_linux.sh`
    """
    file_path = Path(file_path)
    with open(file_path, "r") as f:
        lines: list[str] = f.readlines()

    string_found = False
    STR_TO_REMOVE = "chmod +x chromium/chromium-linux64/chrome"
    filtered_lines: list[str] = []
    for line in lines:
        if STR_TO_REMOVE in line:
            string_found = True
        else:
            filtered_lines.append(line)

    if string_found:
        with open(file_path, "w") as f:
            f.writelines(filtered_lines)
        logger.info(f"Chrome reference removed from {file_path.parent.name}.")
    else:
        logger.warning(f"Chrome reference not found in {file_path.parent.name}.")
        sys.exit(1)


def get_args() -> argparse.Namespace:
    """Get the arguments passed at the command line.

    Returns:
        Namespace: Contains the argument names as instance variables.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "abs_path_to_model",
        type=Path,
        help="Absolute path to the .alp/.alpx file",
    )
    parser.add_argument(
        "--anylogic_dir",
        type=Path,
        default=DEFAULT_PATH_TO_ANYLOGIC,
        help="Absolute path to AnyLogic.exe. (default: %(default)s)",
    )
    parser.add_argument(
        "--experiments",
        nargs="*",
        type=str,
        default="Simulation",
        help="Experiments to run in continuous integration. Note: all experiments are exported by AnyLogic.",
    )
    return parser.parse_args()


def experiment_dir(model_dir: Path) -> Generator[Path, Any, None]:
    """Get one or more paths to the model's experiment directories.

    Args:
        model_dir (Path): Path to the directory holding the .alpx file.

    Yields:
        Generator[Path]:
    """
    project_dir: Path = model_dir.parent
    for contents in project_dir.iterdir():
        if contents.is_dir() and str(contents.name).startswith(f"{model_dir.name}_"):
            yield contents


def linux_script_path(model_path: Path, experiment_dir: Path) -> Path:
    """Get the Linux shell script created by AnyLogic during the export."""
    return experiment_dir / f"{model_path.name}_linux.sh"


def remove_chrome_refs_when_files_modified(
    abs_path_to_model: Path, experiments: list[str]
) -> None:
    """Remove the line that `chmod`s the chrome directory from the Linux scripts
    created during export. This line will cause an error since `chrome/` is gitignored.

    Args:
        abs_path_to_model (Path): Absolute path to the model being exported.
        experiments (list[str]): The experiments to run in continuous integration.
    """
    model_dir: Path = abs_path_to_model.parent
    experiment_dirs: list[Path] = [
        _
        for _ in list(experiment_dir(model_dir))
        if str(_.name).endswith(tuple(experiments))
    ]
    linux_scripts: list[Path] = [
        linux_script_path(model_dir, _) for _ in experiment_dirs
    ]
    chrome_ref_removed: dict[Path, bool] = dict(
        zip(linux_scripts, [False] * len(linux_scripts))
    )
    jar_paths: dict[Path, bool] = {}

    logger.debug(f"Watching for changes in {linux_scripts}")
    for change in watch(*linux_scripts):
        for _ in change:
            file = Path(_[1])
            if not chrome_ref_removed[file]:
                logger.debug(f"Modified by AnyLogic export: {file}")
                remove_chrome_reference(file)
                chrome_ref_removed[file] = True
                for jar in get_jar_files(file):
                    if jar not in jar_paths.keys():
                        jar_paths[jar] = False
                if all(chrome_ref_removed.values()):
                    subprocess.run(
                        ["git", "add", *experiment_dirs], cwd=model_dir, shell=True
                    )
                    watch_for_jar_changes(jar_paths, model_dir)


def get_jar_files(linux_script_path: Path) -> list[Path]:
    """Get paths to jar files that will be modified during export.

    Args:
        linux_script_path (Path): Path to exported file like `*_linux.sh`

    Returns:
        list[Path]: Paths to jar files that will be modified.
    """
    with open(linux_script_path, "r") as f:
        java_command: str = next(
            (line for line in f.readlines() if line.startswith("java -cp"))
        )

    pattern_jar_file = r"(?:\b|^)(?:[a-zA-Z0-9_/.-]+/)?model\d*\.jar\b"
    jars = re.findall(pattern_jar_file, java_command)
    experiment_dir = linux_script_path.parent
    return [experiment_dir / _ for _ in jars]


def watch_for_jar_changes(jar_paths: dict[Path, bool], model_dir: Path) -> None:
    """Watch the specified jar files and `git add` them when modified.

    Args:
        jar_paths (dict[Path, bool]):
        model_dir (Path):
    """
    for change in watch(*list(jar_paths.keys())):
        for _ in change:
            file = Path(_[1])
            jar_paths[Path(file)] = True
            subprocess.run(["git", "add", file], cwd=model_dir, shell=True)
            logger.debug(f"Git added {file}")
            logger.debug(
                f"Added by Git: {json.dumps({str(k): v for k, v in jar_paths.items()}, indent=4)}"
            )
            if all(jar_paths.values()):
                logger.info("Git added all jar files.")
                sys.exit(0)


def run() -> None:
    args: argparse.Namespace = get_args()
    export_model(args.abs_path_to_model, args.anylogic_dir)
    remove_chrome_refs_when_files_modified(args.abs_path_to_model, args.experiments)


if __name__ == "__main__":
    run()
