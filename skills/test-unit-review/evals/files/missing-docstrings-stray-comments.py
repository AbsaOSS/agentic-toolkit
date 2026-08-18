"""Unit tests for InvoiceGenerator.

VIOLATIONS — naming / structure:
  test_generate_valid_invoice         : no docstring (scenario not stated)
  test_generate_zero_amount           : no docstring; inline comment used instead
  test_generate_negative_amount       : stray explanatory comment outside a test method
  test_generate_missing_client_raises : no docstring; stray inline comment in body

Fixture docstring is also missing its side-effects note.
"""
import pytest
from unittest.mock import MagicMock

from billing.invoice_generator import InvoiceGenerator


@pytest.fixture
def generator():
    # this fixture creates an InvoiceGenerator — missing docstring with purpose/side-effects
    mailer = MagicMock()
    templates = MagicMock()
    templates.render.return_value = "<html>Invoice</html>"
    return InvoiceGenerator(mailer=mailer, templates=templates)


# --- generate ---


def test_generate_valid_invoice(generator):
    # no docstring — scenario is not stated as required by standards
    result = generator.generate(client_id="c1", amount=500.0)
    assert result["status"] == "sent"


def test_generate_zero_amount(generator):
    # no docstring; scenario explained via inline comment instead
    # zero amount should raise ValueError per the contract
    with pytest.raises(ValueError):
        generator.generate(client_id="c1", amount=0.0)


# Stray comment outside a test method explaining intent — should not appear here
def test_generate_negative_amount(generator):
    with pytest.raises(ValueError):
        generator.generate(client_id="c1", amount=-10.0)


def test_generate_missing_client_raises_key_error(generator):
    # inline comment used instead of a docstring
    # empty client_id is not permitted
    with pytest.raises(KeyError):
        generator.generate(client_id="", amount=100.0)
