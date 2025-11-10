import pytest
from anylogic_export import export
from pathlib import Path


@pytest.mark.parametrize(
    "path_to_model",
    [
        "d:/repos/anylogic-export/DistributionCenter/DistributionCenter.alpx",
        "DistributionCenter/DistributionCenter.alpx",
    ],
)
def test_good_path(path_to_model: str, tmp_path: Path) -> None:
    export.model_path(path_to_model)

