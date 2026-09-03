"""
Regressionstest fuer den Feedback-Learning-Trigger.

Hintergrund: Der Lern-Trigger zaehlte negative Feedbacks ueber die Werte
'rejected'/'action_ignored'/'incorrect' — Strings, die der Schreibpfad
(record_feedback -> FeedbackType) nie erzeugt. Dadurch blieb negative_count
faktisch immer 0 und die Adaption feuerte nie. Diese Tests nageln fest, dass
NEGATIVE_FEEDBACK_TYPES ausschliesslich echte FeedbackType-Werte enthaelt und
den negativen Teil vollstaendig abdeckt.
"""

from ai_feedback_learning import NEGATIVE_FEEDBACK_TYPES, FeedbackType


VALID_VALUES = {ft.value for ft in FeedbackType}

# Der positive/neutrale Teil, der NICHT als negativ zaehlen darf.
NON_NEGATIVE = {
    FeedbackType.IMPLICIT_CLICK.value,
    FeedbackType.EXPLICIT_HELPFUL.value,
    FeedbackType.ACTION_COMPLETED.value,
}


def test_negative_types_are_real_feedback_values():
    """Jeder Eintrag muss ein tatsaechlicher FeedbackType-Wert sein."""
    for v in NEGATIVE_FEEDBACK_TYPES:
        assert v in VALID_VALUES, f"{v!r} ist kein gueltiger FeedbackType"


def test_stale_literals_are_not_feedback_values():
    """Die alten Trigger-Strings existieren als FeedbackType nicht (Bug-Ursache)."""
    for stale in ("rejected", "action_ignored", "incorrect"):
        assert stale not in VALID_VALUES


def test_negative_set_covers_all_negative_types():
    """Alle negativen FeedbackTypes muessen erfasst sein, keine positiven."""
    expected_negative = {
        FeedbackType.IMPLICIT_IGNORE.value,
        FeedbackType.IMPLICIT_DISMISS.value,
        FeedbackType.EXPLICIT_NOT_HELPFUL.value,
        FeedbackType.EXPLICIT_WRONG.value,
        FeedbackType.ACTION_SKIPPED.value,
    }
    assert set(NEGATIVE_FEEDBACK_TYPES) == expected_negative


def test_no_positive_type_counted_as_negative():
    assert NON_NEGATIVE.isdisjoint(set(NEGATIVE_FEEDBACK_TYPES))
