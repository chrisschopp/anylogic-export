import pytest
from anylogic_export import export
from pathlib import Path


@pytest.mark.local
@pytest.mark.parametrize(
    "path_to_model",
    [
        "d:/repos/anylogic-export/DistributionCenter/DistributionCenter.alpx",
        "DistributionCenter/DistributionCenter.alpx",
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
