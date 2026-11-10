"""Statistics, standard library only.

Run level:     Wilson intervals for proportions, Newcombe's hybrid score interval for a difference.
Fixture level: cluster bootstrap and exact sign-flip test of a per-fixture difference (the fixture is the unit,
               because runs inside one fixture and arm are nearly always identical).
Mutation:      Clopper-Pearson intervals.
"""
import itertools
import math
import random

Z = 1.959963984540054


def wilson(k, n):
    if n == 0:
        return (float("nan"), 0.0, 1.0)
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def newcombe(k1, n1, k2, n2):
    """Difference p1 - p2 with Newcombe's hybrid score interval."""
    p1, l1, u1 = wilson(k1, n1)
    p2, l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return (d, d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def fmt(k, n):
    p, lo, hi = wilson(k, n)
    return f"{k}/{n} = {p:.0%} [{lo:.0%}, {hi:.0%}]" if n else "–"


def cluster_bootstrap(diffs, reps=10000, seed=0):
    """Resample the per-fixture differences with replacement.
    Returns (mean, lo, hi, share of resamples whose mean is exactly 0)."""
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(rng.choice(diffs) for _ in range(n)) / n for _ in range(reps))
    lo, hi = means[int(0.025 * reps)], means[min(reps - 1, int(0.975 * reps))]
    zero = sum(abs(m) < 1e-12 for m in means) / reps
    return sum(diffs) / n, lo, hi, zero


def sign_flip(diffs, max_exact=20, mc_reps=100000, seed=0):
    """Sign-flip permutation test of mean(diffs) = 0: under the null the arm labels are exchangeable within a
    fixture, so each fixture's difference may change sign. Returns (one_sided_p, two_sided_p, exact).
    One-sided means: as extreme as observed, in the observed direction."""
    nz = [d for d in diffs if abs(d) > 1e-12]
    obs = sum(nz)
    if not nz:
        return 1.0, 1.0, True
    one = two = total = 0
    if len(nz) <= max_exact:
        sums = (sum(s * d for s, d in zip(signs, nz)) for signs in itertools.product((1, -1), repeat=len(nz)))
        exact = True
    else:
        rng = random.Random(seed)
        sums = (sum(rng.choice((1, -1)) * d for d in nz) for _ in range(mc_reps))
        exact = False
    direction = 1 if obs > 0 else -1
    for s in sums:
        total += 1
        one += s * direction >= abs(obs) - 1e-12
        two += abs(s) >= abs(obs) - 1e-12
    return one / total, two / total, exact


def fixture_contrast(cells_x, cells_y, reps=10000, seed=0):
    """cells_x, cells_y: {fixture: (k, n)} for two arms. Uses fixtures present (n > 0) in both.
    The per-fixture difference is rate_x - rate_y."""
    fx = sorted(f for f in cells_x if cells_x[f][1] and cells_y.get(f, (0, 0))[1])
    if not fx:
        return None
    diffs = [cells_x[f][0] / cells_x[f][1] - cells_y[f][0] / cells_y[f][1] for f in fx]
    mean, lo, hi, zero = cluster_bootstrap(diffs, reps, seed)
    p1, p2, exact = sign_flip(diffs)
    return {"fixtures": fx, "diffs": diffs, "mean": mean, "lo": lo, "hi": hi, "p_zero": zero,
            "informative": sum(abs(d) > 1e-12 for d in diffs), "p_one": p1, "p_two": p2, "exact": exact}


def beta_ppf(p, a, b, lo=0.0, hi=1.0):
    """Inverse regularized incomplete beta by bisection."""
    def cdf(x):  # regularized incomplete beta via continued fraction (Numerical Recipes betacf)
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)

        def cf(a, b, x):
            qab, qap, qam, c, d = a + b, a + 1, a - 1, 1.0, 1 - (a + b) * x / (a + 1)
            d = 1 / (d if abs(d) > 1e-300 else 1e-300)
            h = d
            for m in range(1, 300):
                m2 = 2 * m
                aa = m * (b - m) * x / ((qam + m2) * (a + m2))
                d = 1 + aa * d
                d = 1 / (d if abs(d) > 1e-300 else 1e-300)
                c = 1 + aa / c if abs(1 + aa / c) > 1e-300 else 1e-300
                h *= d * c
                aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
                d = 1 + aa * d
                d = 1 / (d if abs(d) > 1e-300 else 1e-300)
                c = 1 + aa / c if abs(1 + aa / c) > 1e-300 else 1e-300
                de = d * c
                h *= de
                if abs(de - 1) < 1e-12:
                    break
            return h
        if x < (a + 1) / (a + b + 2):
            return math.exp(lbeta) * cf(a, b, x) / a
        return 1 - math.exp(lbeta) * cf(b, a, 1 - x) / b
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(mid) < p else (lo, mid)
    return (lo + hi) / 2


def clopper_pearson(k, n, alpha=0.05):
    if n == 0:
        return (0.0, 1.0)
    lo = 0.0 if k == 0 else beta_ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta_ppf(1 - alpha / 2, k + 1, n - k)
    return (lo, hi)


def audits_needed(eps, alpha=0.05):
    """Commits to audit, all clean, to certify an escape rate <= eps at confidence 1 - alpha (zero-failure bound)."""
    return math.ceil(math.log(alpha) / math.log(1 - eps))
