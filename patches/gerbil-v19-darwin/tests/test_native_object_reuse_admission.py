"""Offline receipt policy; never launches native tests."""
import pytest

from experiment_framework.native_receipt import admit_object_reuse


def admitted():
    return dict(correctnessPassed=True, entryCacheMiss=True, entryCacheHit=False,
                staticObjectHits=70, staticObjectMisses=2, objectCalls=73)


def test_complete_backend_reuse_passes():
    assert admit_object_reuse(admitted(), 72, 70)


@pytest.mark.parametrize('changes', [
    dict(correctnessPassed=False), dict(entryCacheMiss=False),
    dict(entryCacheHit=True), dict(staticObjectHits=0, staticObjectMisses=72),
    dict(staticObjectHits=69, staticObjectMisses=3), dict(staticObjectMisses=1),
    dict(staticObjectMisses=3), dict(objectCalls=71),
])
def test_incomplete_or_non_reuse_receipt_denied(changes):
    record = admitted()
    record.update(changes)
    assert not admit_object_reuse(record, 72, 70)


@pytest.mark.parametrize('events,hits', [(0, 0), (72, 0), (72, -1), (72, 73)])
def test_invalid_policy_rejected(events, hits):
    with pytest.raises(ValueError):
        admit_object_reuse(admitted(), events, hits)
