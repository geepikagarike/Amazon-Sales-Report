from __future__ import annotations

from pathlib import Path

from src.mongo_integration import prepare_powerbi_exports


def main() -> None:
    exports = prepare_powerbi_exports(Path(__file__).resolve().parents[1] / "data" / "powerbi")
    for name, path in exports.items():
        print(f"Prepared {name}: {path}")


if __name__ == "__main__":
    main()
