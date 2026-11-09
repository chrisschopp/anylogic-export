import pytest
import subprocess
import shutil
from anylogic_export import export
from pathlib import Path

TEST_MODEL = "DistributionCenter"
EXPERIMENTS = "CustomExperiment", "Simulation"


@pytest.mark.local
@pytest.mark.parametrize(
    "path_to_model",
    [
        f"d:/repos/anylogic-export/{TEST_MODEL}/{TEST_MODEL}.alpx",
        f"{TEST_MODEL}/{TEST_MODEL}.alpx",
    ],
)
def test_good_path(path_to_model: str, tmp_path: Path) -> None:
    export.model_path(path_to_model)


@pytest.mark.local
@pytest.mark.parametrize("path_to_model", ["c:/does/not/exist.alpx"])
def test_bad_path(path_to_model: str, tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        export.model_path(path_to_model)


@pytest.mark.local
@pytest.mark.parametrize("anylogic_dir", [export.default_path_to_anylogic()])
def test_good_anylogic_path(anylogic_dir: str) -> None:
    export.validated_anylogic_dir(anylogic_dir)


@pytest.mark.local
@pytest.mark.parametrize(
    "anylogic_dir", [export.default_path_to_anylogic() / "extra_dir"]
)
def test_bad_anylogic_path(anylogic_dir: str) -> None:
    with pytest.raises(ValueError):
        export.validated_anylogic_dir(anylogic_dir)


@pytest.mark.local
@pytest.mark.slow
def test_export() -> None:
    """Test export after ensuring there are no exported experiment directories.

    This makes sure it works the first time `export` is run.
    """
    for experiment in EXPERIMENTS:
        shutil.rmtree(f"{TEST_MODEL}_{experiment}")
    subprocess.run(
        ["python", "./anylogic_export/export.py", "-v", "export"],
        shell=True,
    )


def test_load_config(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.anylogic-export]\n'
        'experiments = ["A", "B"]\n'
        'anylogic-dir = "/opt/AnyLogic"\n'
        '[tool.anylogic-export.export]\n'
        'experiments = "C"\n'
    )
    sub = tmp_path / "sub"
    sub.mkdir()
    cfg = export.load_config(sub)  # found in a parent directory
    assert cfg["init"] == {"experiments": "A,B", "anylogic_dir": "/opt/AnyLogic"}
    assert cfg["export"]["experiments"] == "C"  # command table wins


def test_config_used_as_default(tmp_path: Path, monkeypatch) -> None:
    from typer.testing import CliRunner

    (tmp_path / "pyproject.toml").write_text(
        '[tool.anylogic-export]\nexperiments = ["A", "B"]\n'
    )
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(export.app, ["init-config", "Model", "--help"])
    assert result.exit_code == 0
    runner.invoke(export.app, ["init-config", "Model"])
    assert "--experiments=A,B" in (tmp_path / ".pre-commit-config.yaml").read_text()
