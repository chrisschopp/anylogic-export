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
