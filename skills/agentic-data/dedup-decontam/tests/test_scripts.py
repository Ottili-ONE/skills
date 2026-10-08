"""Tests for dedup-decontam scripts. Offline, deterministic."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from minhash_lsh import (  # noqa: E402
    bands_for,
    jaccard,
    lsh_candidates,
    minhash,
    shingles,
)
import ngram_decontam  # noqa: E402
import plant_test  # noqa: E402


def test_shingles_basic():
    s = shingles("hello world", 5)
    assert "hello" in s
    assert "ello " in s
    assert len(s) == 7  # len("hello world")=11 -> 11-5+1


def test_shingles_short():
    assert shingles("ab", 5) == {"ab"}
    assert shingles("", 5) == set()


def test_minhash_deterministic():
    a = minhash(shingles("the quick brown fox", 5), 64, 1)
    b = minhash(shingles("the quick brown fox", 5), 64, 1)
    assert a == b
    assert len(a) == 64


def test_minhash_rejects_small_k():
    with pytest.raises(ValueError):
        minhash(shingles("abcde", 5), 16, 1)


def test_jaccard_identical():
    s = shingles("hello world hello", 5)
    assert jaccard(s, s) == 1.0


def test_jaccard_disjoint():
    a = shingles("aaaaa", 3)
    b = shingles("bbbbb", 3)
    assert jaccard(a, b) == 0.0


def test_bands_for_targets():
    # k=128 must split into b*r
    for target in (0.5, 0.67, 0.8, 0.85, 0.94):
        b, r = bands_for(128, target)
        assert b * r == 128
        t = (1.0 / b) ** (1.0 / r)
        assert 0.0 < t <= 1.0


def test_lsh_finds_identical(tmp_path):
    d = tmp_path
    (d / "a.txt").write_text("the quick brown fox jumps over the lazy dog")
    (d / "b.txt").write_text("the quick brown fox jumps over the lazy dog")
    (d / "c.txt").write_text("machine learning needs lots of data")
    sets = {p.name: shingles(p.read_text(), 5) for p in d.glob("*.txt")}
    sigs = {n: minhash(s, 128, 1) for n, s in sets.items()}
    b, r, pairs = lsh_candidates(sigs, 128, 0.7)
    found = {(a, b2) for a, b2 in pairs if jaccard(sets[a], sets[b2]) >= 0.8}
    assert ("a.txt", "b.txt") in found or ("b.txt", "a.txt") in found


def test_ngram_decontam_detects_leak(tmp_path, capsys):
    p = tmp_path / "prompt.txt"
    c1 = tmp_path / "c1.txt"
    c2 = tmp_path / "c2.txt"
    p.write_text("the quick brown fox")
    c1.write_text("the quick brown fox jumps over the dog")
    c2.write_text("completely different topic about cats")
    rc = ngram_decontam.main_args(["--corpus", str(c1), str(c2), "--prompts", str(p), "--n", "3"])
    assert rc == 1  # leak detected


def test_ngram_decontam_clean(tmp_path):
    p = tmp_path / "prompt.txt"
    c = tmp_path / "c.txt"
    p.write_text("the quick brown fox")
    c.write_text("completely different topic about cats")
    rc = ngram_decontam.main_args(["--corpus", str(c), "--prompts", str(p), "--n", "3"])
    assert rc == 0


def test_plant_test_passes(tmp_path):
    rc = plant_test.main_args(["--out", str(tmp_path / "plant"), "--seed", "7"])
    assert rc == 0
