from pathlib import Path

from app.visuals import AutomataConfig, CellularAutomataEngine


def test_export_gif(tmp_path: Path) -> None:
    engine = CellularAutomataEngine(AutomataConfig(width=16, height=12, cell_size=2, seed_density=0.2, fps=8))
    out = tmp_path / "test.gif"
    gif_path, summary = engine.export_gif(out, steps=4)
    assert Path(gif_path).exists()
    assert summary["generation"] >= 1
    assert 0.0 <= summary["density"] <= 1.0
