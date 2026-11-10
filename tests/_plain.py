"""Run the test_* functions of a test module without pytest: python3 tests/test_x.py"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def run(namespace, name):
    failed = 0
    tests = [(k, v) for k, v in sorted(namespace.items()) if k.startswith("test_") and callable(v)]
    for k, fn in tests:
        try:
            fn()
        except Exception:
            failed += 1
            print(f"FAIL {k}")
            traceback.print_exc()
    print(f"{name}: {len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0
