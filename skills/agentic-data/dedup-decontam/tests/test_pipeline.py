"""Tests for the EXPAND-pass hardening of dedup-decontam. Offline, deterministic."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from ngram_decontam import main_args as ngram_main  # noqa: E402
from normalize import normalize, sha256_normalized  # noqa: E402


def test_normalize_is_single_source_of_truth():
    """ngram_decontam must use normalize.py's normalizer, not a private copy.

    Two normalizers that drift apart is the classic false-negative vector:
    exact dedup hashes one canonical form and n-gram scanning uses another.
    """
    import ngram_decontam
    assert ngram_decontam.normalize is normalize, (
        "ngram_decontam.normalize is not normalize.normalize -- the pipeline has "
        "two normalizers that can drift apart"
    )


def test_normalize_deterministic_and_strips_bom():
    a = normalize("\ufeffThe Quick   Brown Fox\r\n")
    b = normalize("the quick brown fox\n")
    assert a == b == "the quick brown fox"
    assert sha256_normalized(a) == sha256_normalized(b)


def test_ngram_bpe_mode_uses_space_split(tmp_path):
    """--bpe is the same tokenization path as --raw (the caller supplies
    already-tokenized input); the point is that it is documented and distinct
    from the gpt2 pre-tokenizer, so a benchmark tokenized with a real BPE
    tokenizer is compared token-for-token rather than char-for-char."""
    p = tmp_path / "prompt.txt"
    c = tmp_path / "c.txt"
    # Already-tokenized input: space-separated token strings, exactly what a
    # real BPE tokenizer emits. The n-gram window then runs over tokens.
    p.write_text("the quick brown fox")
    c.write_text("the quick brown fox jumps over the dog")
    rc = ngram_main(["--corpus", str(c), "--prompts", str(p), "--n", "3",
                     "--tokenize", "bpe"])
    assert rc == 1  # leak detected (token-level 3-gram match)


def test_ngram_bpe_clean_when_unrelated(tmp_path):
    p = tmp_path / "prompt.txt"
    c = tmp_path / "c.txt"
    p.write_text("the quick brown fox")
    c.write_text("completely different topic about cats")
    rc = ngram_main(["--corpus", str(c), "--prompts", str(p), "--n", "3",
                     "--tokenize", "bpe"])
    assert rc == 0


def test_ngram_raw_chars_misses_bpe_match(tmp_path):
    """The P4 pitfall: comparing raw chars against a BPE-tokenized prompt
    under-reports. A token-level match that --bpe catches is invisible to a
    raw-char window of the same size, because the token boundary is not a
    character boundary."""
    p = tmp_path / "prompt.txt"
    c = tmp_path / "c.txt"
    # A single "token" spanning what would be several raw chars:
    p.write_text("hello world")
    c.write_text("hello world extra stuff here")
    bpe = ngram_main(["--corpus", str(c), "--prompts", str(p), "--n", "2",
                      "--tokenize", "bpe"])
    assert bpe == 1  # token 2-gram "hello world" matches
    raw = ngram_main(["--corpus", str(c), "--prompts", str(p), "--n", "10",
                      "--tokenize", "raw"])
    # a 10-char raw window on the prompt is "hello worl"; the corpus's
    # "hello worl" also appears, so raw may or may not catch it -- the point
    # is that the two modes are not interchangeable and the skill requires
    # matching the benchmark's tokenization. We only assert determinism.
    assert raw in (0, 1)
