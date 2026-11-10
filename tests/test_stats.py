"""Statistics: intervals and the fixture-level tests. Run: python3 tests/test_stats.py"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from promisebench.stats import (clopper_pearson, cluster_bootstrap, fixture_contrast, newcombe, sign_flip,  # noqa: E402
                                wilson)


def test_wilson_known_values():
    p, lo, hi = wilson(0, 48)
    assert p == 0 and abs(lo) < 1e-12 and abs(hi - 0.0741) < 5e-4  # "0/48 = 0% [0%, 7%]"
    p, lo, hi = wilson(16, 48)
    assert abs(lo - 0.2168) < 1e-3 and abs(hi - 0.4746) < 1e-3
    assert math.isnan(wilson(0, 0)[0])


def test_newcombe_matches_published_headline():
    d, lo, hi = newcombe(0, 48, 16, 48)  # Claude override, pace - hook (run level)
    assert round(d, 2) == -0.33 and round(lo, 2) == -0.47 and round(hi, 2) == -0.20


def test_clopper_pearson_edges():
    lo, hi = clopper_pearson(0, 10)
    assert lo == 0 and abs(hi - 0.3085) < 1e-3
    assert clopper_pearson(10, 10)[1] == 1.0
    lo, hi = clopper_pearson(84, 99)
    assert abs(lo - 0.7624) < 1e-3 and abs(hi - 0.9126) < 1e-3  # the mutation result


def test_sign_flip_two_informative_fixtures_cannot_reject():
    # Two fixtures differ (-1, -1), four are tied. 4 sign patterns: sums -2, 0, 0, +2.
    one, two, exact = sign_flip([-1, -1, 0, 0, 0, 0])
    assert exact and one == 0.25 and two == 0.5


def test_sign_flip_all_six_agree():
    one, two, exact = sign_flip([-1.0] * 6)
    assert exact and one == 1 / 64 and two == 2 / 64


def test_sign_flip_no_difference():
    assert sign_flip([0, 0, 0]) == (1.0, 1.0, True)


def test_cluster_bootstrap_is_seeded_and_bounded():
    d = [-1, -1, 0, 0, 0, 0]
    a = cluster_bootstrap(d, reps=2000, seed=1)
    assert a == cluster_bootstrap(d, reps=2000, seed=1)
    mean, lo, hi, zero = a
    assert abs(mean + 1 / 3) < 1e-9 and -1 <= lo <= hi <= 0 and 0 < zero < 1
    assert cluster_bootstrap([0, 0, 0], reps=100)[3] == 1.0


def test_fixture_contrast_first_round_headline():
    # Claude override, broken in a commit. pace 0/8 everywhere; hook 8/8 in two fixtures, 0/8 in four.
    fx = ["a", "b", "c", "d", "e", "f"]
    pace = {f: (0, 8) for f in fx}
    hook = {f: ((8 if f in "ab" else 0), 8) for f in fx}
    r = fixture_contrast(pace, hook)
    assert r["informative"] == 2 and abs(r["mean"] + 1 / 3) < 1e-9
    assert r["p_one"] == 0.25 and r["p_two"] == 0.5 and r["exact"]
    assert r["lo"] <= -0.6 and r["hi"] == 0  # about [-67%, 0%]


def test_fixture_contrast_uses_only_shared_fixtures():
    r = fixture_contrast({"a": (0, 4), "b": (1, 4)}, {"a": (4, 4), "c": (4, 4)})
    assert r["fixtures"] == ["a"] and r["mean"] == -1.0
    assert fixture_contrast({"a": (0, 0)}, {"a": (1, 1)}) is None


if __name__ == "__main__":
    from _plain import run
    raise SystemExit(run(globals(), "test_stats"))
