"""Boots every example in the registry and checks the routes it declares.

Examples with no file of their own in this directory are covered only by this
module.
"""

from __future__ import annotations

import pytest

from examples import EXAMPLES


@pytest.mark.parametrize(
    "worker",
    [pytest.param(example, id=example.test_id) for example in EXAMPLES],
    indirect=True,
)
def test_declared_routes_answer(worker):
    for path, expected_status in worker.example.smoke:
        response = worker.get(path)
        assert response.status_code == expected_status, (
            f"{worker.example.directory} GET {path} -> {response.status_code} "
            f"(expected {expected_status}): {response.text[:300]}"
        )


def test_every_example_declares_smoke_checks():
    missing = [example.directory for example in EXAMPLES if not example.smoke]
    assert not missing, f"examples with no smoke checks: {missing}"
