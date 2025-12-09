import json
import logging
import platform
import re
import subprocess
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any, Generator

import typer
from typer import Argument, Option
from typing_extensions import Annotated
from watchfiles import watch

app = typer.Typer()

logger = logging.getLogger("export_anylogic_model")
logFormatter = logging.Formatter("[%(levelname)s] %(message)s")
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


def default_path_to_anylogic() -> Path:
    op_sys = platform.system()
    match op_sys:
        case "Windows":
            return Path("C:/Program Files/AnyLogic 8.9 Professional")
        case _:
            return NotImplementedError


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


def validated_anylogic_dir(anylogic_dir: str) -> Path:
    path = Path(anylogic_dir)
    if not path.exists():
        raise ValueError(f"Path to AnyLogic directory {path} does not exist.")
    if not (path / "AnyLogic.exe").exists():
        raise ValueError(
            f"Path to AnyLogic directory {path} does not contain `AnyLogic.exe`."
        )
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


@app.command()
def set_verbosity(
    silent: Annotated[bool, Option("--silent", "-s")] = False,
    verbose: Annotated[bool, Option("--verbose", "-v")] = False,
) -> None:
    """Set the logging level to display more/fewer messages.

    Args:
        A
        silent (bool): Disable all logging except errors. Defaults to False.
        verbose (bool): Enable verbose logging. Defaults to False.
    """
    if silent:
        logger.setLevel(logging.ERROR)
    elif verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


@app.command()
def init(model_name: Annotated[str, Option("--model_name", "-n")] = None) -> None:
    """Initialize the .gitignore file to enable exported models to run in continuous integration.

    Args:
        model_name (str): If multiple AnyLogic models are present in the parent folder, the model to export must be passed manually.\b
        If None, the only model found will be exported. Defaults to None.
    """
    model_paths = [
        f for f in Path(".").rglob("*.alp*") if f.suffix in {".alp", ".alpx"}
    ]
    if len(model_paths) > 1:
        raise ValueError(
            "Model name autodiscovery failed as there are multiple "
            f"AnyLogic models in this directory: {model_paths}"
            "Please specify the model name. Use `--help` for more information."
        )
    elif not model_paths:
        raise ValueError(
            f"No AnyLogic model found in {Path.cwd()}. "
            "To initialize before a model is created, provide a model name. See --help for more info."
        )
    model_name = model_name or model_paths[0].parent
    text = f"""
        # Ignore all model's experiment folders
        {model_name}_*/
        # Except for the shell script...
        {model_name}_*/*_linux.sh
        # That calls the jar file(s)
        {model_name}_*/model[0-9]*.jar
    """
    with open(".gitignore", "a+") as f:
        f.write(dedent(text))


@app.command()
def export(
    path_to_model: str,
    anylogic_dir: Annotated[str, Argument(default_factory=default_path_to_anylogic)],
    experiments: Annotated[list[str], Argument()] = ["CustomExperiment"],
) -> None:
    """Export an AnyLogic model to a standalone executable.

    Args:
        path_to_model (str): Relative path to an AnyLogic model (.alp or .alpx).
        anylogic_dir (Annotated[str  |  None, Option, optional): AnyLogic Professional directory. Defaults to None.

    Raises:
        ValueError: If invalid path to directory containing `AnyLogix.exe`.
    """
    abs_path_to_model = model_path(path_to_model)
    anylogic_dir = validated_anylogic_dir(anylogic_dir)
    export_model(abs_path_to_model, anylogic_dir)
    remove_chrome_refs_when_files_modified(abs_path_to_model, experiments)


if __name__ == "__main__":
    app()
