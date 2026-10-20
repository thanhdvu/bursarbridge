"""Signed seed, quotation and synthetic documents must describe the same semester."""

from decimal import Decimal
from io import BytesIO

from pypdf import PdfReader

from bursarbridge.catalog import INSTALMENTS, INVOICE_VERSION, LINES, TOTAL
from bursarbridge.fixtures import pdf


def test_semester_catalog_quote_and_pdf_consistency(journey):
    assert INVOICE_VERSION == "tuition-2027-v8"
    amounts = [Decimal(line["amount"]["amount"]) for line in LINES]
    assert amounts == [Decimal("7174000")]
    assert sum(amounts) == sum(map(Decimal, INSTALMENTS)) == Decimal(TOTAL) == Decimal("7174000")
    quote = journey.ok("GET", "/fx/quote", params={"from": "VND", "side": "receive"})
    assert quote["receive"] == {"amount": TOTAL, "currency": "KRW"}
    for kind in ("invoice", "refund"):
        reader = PdfReader(BytesIO(pdf(kind)))
        text = reader.pages[0].extract_text()
        assert len(reader.pages) == 1
        for amount in [*amounts, Decimal(TOTAL)]:
            assert f"{amount:,.2f}" in text
        assert INVOICE_VERSION in text and "tuition" in text.lower()
        assert "Original bill not reviewed or copied" in text
        assert "MOCK" in text and "SYNTHETIC" in text
    assert "No account in this PDF is authority" in PdfReader(BytesIO(pdf("refund"))).pages[0].extract_text()


def test_insufficient_cap_does_not_authorize_tuition(journey):
    cards = journey.prepare(cap="7000000.00")
    denial = next(e["data"] for e in cards if e.get("kind") == "blocked")
    assert "CAP_EXCEEDED" in {r["code"] for r in denial["reasons"]}
    assert journey.ok("GET", "/payments") == []


def test_new_semester_refund_uses_paid_amount_and_original_payer(journey):
    payment = journey.pay()
    assert payment["receive"] == {"amount": TOTAL, "currency": "KRW"}
    assert payment["send"] == {"amount": "135663956.10", "currency": "VND"}
    refusal = journey.upload("refusal")
    journey.chat("Visa refused", [refusal["id"]])
    approval = journey.ok("GET", "/approvals")[0]
    assert approval["rawAction"]["refundAmount"] == payment["receive"]
    journey.approve(approval, "student_linh")
    journey.advance_refund()
    refund = journey.ok("GET", "/refunds")[0]
    assert refund["status"] == "reconciled" and refund["destination"]["id"] == "acct_parent_minh"
    reconciliation = refund["reconciliation"]
    assert reconciliation["sentOut"] == payment["send"]
    assert reconciliation["receivedBack"] == {"amount": "132551176.98", "currency": "VND"}
    assert [line["amount"]["amount"] for line in reconciliation["lines"]] == [
        "25000.00",
        "2712779.12",
        "375000.00",
        "0.00",
    ]
