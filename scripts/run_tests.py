from __future__ import annotations

import argparse
import importlib.util
import inspect
import sys
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path) -> ModuleType:
    module_name = f"fallback_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load test module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def discover_test_files(paths: list[Path]) -> list[Path]:
    discovered: list[Path] = []
    for path in paths:
        if path.is_file() and path.name.startswith("test_") and path.suffix == ".py":
            discovered.append(path)
        elif path.is_dir():
            discovered.extend(sorted(path.rglob("test_*.py")))
    return sorted(set(discovered))


def discover_test_functions(module: ModuleType) -> list[Callable[..., object]]:
    tests: list[Callable[..., object]] = []
    for name in dir(module):
        value = getattr(module, name)
        if name.startswith("test_") and callable(value):
            tests.append(value)
    return sorted(tests, key=lambda fn: fn.__name__)


def build_kwargs(function: Callable[..., object], temp_root: Path) -> tuple[dict[str, object], list[str]]:
    kwargs: dict[str, object] = {}
    unsupported: list[str] = []
    signature = inspect.signature(function)
    for name, parameter in signature.parameters.items():
        if parameter.default is not inspect.Parameter.empty:
            continue
        if name == "tmp_path":
            kwargs[name] = temp_root / function.__name__
            Path(kwargs[name]).mkdir(parents=True, exist_ok=True)
        else:
            unsupported.append(name)
    return kwargs, unsupported


def run_tests(paths: list[Path]) -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    files = discover_test_files(paths)
    if not files:
        print("no test files discovered")
        return 1

    passed = 0
    failed = 0
    skipped = 0

    with TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        for file_path in files:
            try:
                module = load_module(file_path)
            except Exception:
                failed += 1
                print(f"LOAD FAIL {file_path}")
                traceback.print_exc()
                continue

            for test in discover_test_functions(module):
                kwargs, unsupported = build_kwargs(test, temp_root)
                test_id = f"{file_path.relative_to(ROOT)}::{test.__name__}"
                if unsupported:
                    skipped += 1
                    print(f"SKIP {test_id} unsupported fixtures={','.join(unsupported)}")
                    continue
                try:
                    test(**kwargs)
                except Exception:
                    failed += 1
                    print(f"FAIL {test_id}")
                    traceback.print_exc()
                else:
                    passed += 1
                    print(f"PASS {test_id}")

    print("")
    print(f"summary: passed={passed} failed={failed} skipped={skipped}")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="KODEKS fallback standard-library test runner")
    parser.add_argument("paths", nargs="*", default=["tests"], help="Test files or directories")
    args = parser.parse_args()
    paths = [Path(path).resolve() for path in args.paths]
    return run_tests(paths)


if __name__ == "__main__":
    raise SystemExit(main())
