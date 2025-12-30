import json
import logging
import platform
import re
import subprocess
from functools import partial
from pathlib import Path
from textwrap import dedent
from typing import Any, Generator

import typer
from rich.logging import RichHandler
from typer import Argument, Option
from typing_extensions import Annotated
from watchfiles import Change, DefaultFilter, watch


def set_verbosity(
    silent: Annotated[bool, Option("--silent", "-s")] = False,
    verbose: Annotated[bool, Option("--verbose", "-v")] = False,
) -> None:
    """Set the logging level to display more/fewer messages.

    Args:
        silent (bool): Disable all logging except errors. Defaults to False.
        verbose (bool): Enable verbose logging. Defaults to False.
    """
    if silent:
        if verbose:
            raise typer.BadParameter("Cannot use --silent and --verbose together.")
        logger.setLevel(logging.ERROR)
    elif verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    callback=set_verbosity,
)

logger = logging.getLogger("export_anylogic_model")
FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)


def default_path_to_anylogic() -> Path:
    op_sys = platform.system()
    match op_sys:
        case "Windows":
            return Path("C:/Program Files/AnyLogic 8.9 Professional")
        case _:
            return NotImplementedError


def export_model(path_to_model: str, anylogic_dir: Path) -> None:
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
        raise typer.Exit(1)


def get_experiment_dirs(model_dir: Path, cli_exp: tuple[str]) -> list[Path]:
    """Validate that the experiments exist and get their directories.

    Args:
        model_dir (Path): The directory containing the AnyLogic model.
        cli_exp (tuple[str]): Experiments passed to the export CLI.
            E.g. `("CustomExperiment", "Simulation")`

    Raises:
        ValueError: If the experiments passed to the CLI do not exist for the model.

    Returns:
        list[Path]: The validated experiment directories.
    """
    discovered_exp: list[Path] = list(_discover_experiments(model_dir))
    if validated_exp := [
        dir_ for dir_ in discovered_exp if str(dir_.name).endswith(cli_exp)
    ]:
        return validated_exp
    elif not discovered_exp:
        return [model_dir / f"{model_dir.name}_{exp}" for exp in cli_exp]
    else:
        logger.warning(
            f"Experiments: `{cli_exp}` not found. If these experiments do not exist, "
            "you may need to pass your experiment name explicitly. "
            "See --help for more details."
        )


def _discover_experiments(model_dir: Path) -> Generator[Path, Any, None]:
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
    return (
        experiment_dir.parent.parent
        / experiment_dir.name
        / f"{model_path.name}_linux.sh"
    )


class LinuxScriptFilter(DefaultFilter):
    """Only watch for changes to Linux scripts in the exported experiment directories."""

    def __call__(self, change: Change, path: str, experiments: tuple[str]) -> bool:
        return (
            super().__call__(change, path)
            and path.endswith(".sh")
            and any(_ in path for _ in experiments)
        )


def remove_chrome_refs_when_files_modified(
    abs_path_to_model: Path, experiments: str
) -> None:
    """Remove the line that `chmod`s the chrome directory from the Linux scripts
    created during export. This line will cause an error since `chrome/` is gitignored.

    Args:
        abs_path_to_model (Path): Absolute path to the model being exported.
        experiments (str): Comma-separated experiments to run in continuous integration.
            E.g. `--experiments CustomExperiment,Simulation`
    """
    model_dir: Path = abs_path_to_model.parent
    cli_exp: list[str] = tuple(experiments.split(","))
    experiment_dirs: list[Path] = get_experiment_dirs(model_dir, cli_exp)
    linux_scripts: list[Path] = [
        linux_script_path(model_dir, _) for _ in experiment_dirs
    ]
    chrome_ref_removed: dict[Path, bool] = dict(
        zip(linux_scripts, [False] * len(linux_scripts))
    )
    logger.debug(f"{chrome_ref_removed=}")
    jar_paths: dict[Path, bool] = {}

    logger.debug(f"{experiment_dirs=}")
    logger.debug(
        f"Watching for changes in {json.dumps(linux_scripts, default=lambda _: str(_), indent=4)}"
    )
    for change in watch(
        model_dir.parent,
        watch_filter=partial(LinuxScriptFilter(), experiments=cli_exp),
        rust_timeout=20_000,
    ):
        for _ in change:
            file = Path(_[1])
            if not chrome_ref_removed[file]:
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
            (line for line in f.readlines() if line.startswith("java"))
        )

    pattern_jar_file = r"(?:\b|^)(?:[a-zA-Z0-9_/.-]+/)?model\d*\.jar\b"
    jars = re.findall(pattern_jar_file, java_command)
    experiment_dir = linux_script_path.parent
    return [experiment_dir / _ for _ in jars]


def ignore_deleted(change: Change, path: str) -> bool:
    """Don't detect a change when a watched file is deleted."""
    return change != Change.deleted


def watch_for_jar_changes(jar_paths: dict[Path, bool], model_dir: Path) -> None:
    """Watch the specified jar files and `git add` them when modified.

    Args:
        jar_paths (dict[Path, bool]):
        model_dir (Path):
    """
    logger.debug(
        f"Watching for jar changes...{json.dumps({str(k): v for k, v in jar_paths.items()}, indent=4)}"
    )
    for change in watch(
        *list(jar_paths.keys()), watch_filter=ignore_deleted, rust_timeout=30_000
    ):
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
                raise typer.Exit(0)


def discover_model_path() -> Path:
    """Recursively search the current directory and sub-directories for AnyLogic models.

    If there is only model, returns the path to it. If there is more than one model, an
    error is raised since it is unclear which model should be exported.

    The path to the model to export will need to be provided.

    Raises:
        ValueError: Multiple AnyLogic models found.
        ValueError: No AnyLogic model found.

    Returns:
        Path: The path to the only model (recursively) found in the current directory.
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
    return model_paths[0]


def discover_model_name() -> str:
    return discover_model_path().parent


@app.command()
def init(
    model_name: Annotated[
        str | None, Option("--model_name", "-n", default_factory=discover_model_name)
    ],
    experiments: Annotated[
        str | None, Option("--experiments", "-e")
    ] = "CustomExperiment",
) -> None:
    """Prepare the AnyLogic model for use in a continuous integration pipeline. Executes all commands in the
    `init*` namespace instead of calling each command individually.

    This does the following tailored to a specific AnyLogic model:
    * Creates a `.gitignore`
    * Creates a `.pre-commit-confit.yaml`

    If the directory in which this is executed contains only one AnyLogic model, the
    `model_name` can be automatically determined.

    Args:
        model_name (str | None): If multiple AnyLogic models are present in the parent folder, the model to export must be passed manually.\b
        If None, the only model found will be exported. If passing a model name that contains spaces, wrap it in quotation marks. Defaults to None.
        experiments (str | None): Comma-separated experiments to export from the model.
            E.g. `--experiments CustomExperiment,Simulation`
    """
    init_gitignore(model_name)
    init_config(model_name, experiments)


@app.command()
def init_gitignore(model_name: str) -> None:
    """Initialize the .gitignore file to enable exported models to run in continuous integration.

    Args:
        model_name (str): _description_
    """
    text = f"""
        # Ignore all model's experiment folders
        {model_name}_*/
        # Except for the shell script...
        {model_name}_*/*_linux.sh
        # That calls the jar file(s)
        {model_name}_*/model[0-9]*.jar
    """
    with open(".gitignore", "a+b") as f:
        f.write(bytes(dedent(text), encoding="utf-8"))


@app.command()
def init_config(model_name: str, experiments: str) -> None:
    """Initialize a `.pre-commit-config.yaml` for use with an AnyLogic project.

    The `anylogic-export` hook will only run when a change is made to a file in the
    model folder.

    Args:
        model_name (str): The directory holding the AnyLogic model and its assets.
        experiments (str): Comma-separated experiments to export from the model.
            E.g. `--experiments CustomExperiment,Simulation`
    """
    text = f"""repos:
  - repo: https://github.com/chrisschopp/anylogic-export
    rev: v0.1.0
    hooks:
      - id: anylogic-export
        args: [export, --experiments={experiments}]
        files: {model_name}/*
    """
    with open(".pre-commit-config.yaml", "w") as f:
        f.write(dedent(text))


@app.command()
def export(
    path_to_model: Annotated[
        Path | None,
        Argument(
            help="Path to AnyLogic model; defaults to auto-detected path.",
            default_factory=discover_model_path,
        ),
    ],
    *,
    anylogic_dir: Annotated[
        Path | None,
        Option(
            "--anylogic_dir",
            default_factory=default_path_to_anylogic,
            help="Path to AnyLogic Professional installation; defaults to auto-detected path.",
        ),
    ],
    experiments: Annotated[str, Option("--experiments", "-e")] = "CustomExperiment",
) -> None:
    """Export an AnyLogic model to a standalone executable.

    Args:
        path_to_model (str): Relative path to an AnyLogic model (.alp or .alpx). If the model name contains spaces, wrap it in quotation marks.
        anylogic_dir (Path | None): AnyLogic Professional directory. Defaults to None.
        experiments (list[str]): Comma-separated experiments passed to the export CLI. Defaults to `"CustomExperiment"`.
            E.g. `--experiments CustomExperiment,Simulation`

    Raises:
        ValueError: If invalid path to directory containing `AnyLogix.exe`.
    """
    abs_path_to_model = model_path(path_to_model)
    anylogic_dir = validated_anylogic_dir(anylogic_dir)
    export_model(abs_path_to_model, anylogic_dir)
    remove_chrome_refs_when_files_modified(abs_path_to_model, experiments)


if __name__ == "__main__":
    app()
