import pytest

from ghostline.core.ai import captions_for_ai
from ghostline.core.transcript import Line


def lines(*texts):
    return [Line(float(i), t) for i, t in enumerate(texts)]


L = lines("One.", "Two.", "Three.", "Four.", "Five.", "Six.", "Seven.")


def test_new_sends_only_unsent_lines_and_advances():
    text, sent = captions_for_ai(L[:3], "", "new", 0)
    assert (text, sent) == ("One. Two. Three.", 3)
    text, sent = captions_for_ai(L, "", "new", sent)
    assert (text, sent) == ("Four. Five. Six. Seven.", 7)


def test_new_with_nothing_new_is_empty():
    assert captions_for_ai(L, "", "new", len(L)) == ("", len(L))


def test_partial_sentence_is_always_included():
    text, sent = captions_for_ai(L, "what is a thread", "new", len(L))
    assert text == "what is a thread"
    assert sent == len(L)


def test_cleared_transcript_resends_everything():
    # sent_count larger than the transcript means it was cleared since the last send
    assert captions_for_ai(L[:2], "", "new", 7) == ("One. Two.", 2)


def test_last5_and_all():
    assert captions_for_ai(L, "", "last5", 0)[0] == "Three. Four. Five. Six. Seven."
    assert captions_for_ai(L, "Eight", "all", 99)[0] == "One. Two. Three. Four. Five. Six. Seven. Eight"


def test_blank_lines_are_skipped():
    assert captions_for_ai(lines("  ", "Hi."), "  ", "all", 0)[0] == "Hi."


def test_unknown_mode():
    with pytest.raises(ValueError):
        captions_for_ai(L, "", "bogus", 0)
