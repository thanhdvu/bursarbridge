"""Readable projections of the consent-bound synthetic forms, not bank instructions."""

from io import BytesIO
from textwrap import wrap

from reportlab.pdfgen import canvas

KINDS = {"admission_withdrawal", "tuition_refund_application"}


def pdf(approval, kind):
    packet = approval["rawAction"]["paperwork"]
    destination = packet["destination"]
    lines = [
        "Hanbit University (MOCK) | SYNTHETIC - NO REAL FUNDS",
        "Admission withdrawal" if kind == "admission_withdrawal" else "Tuition refund application",
        "I withdraw my freshman admission following visa refusal; I must reapply, not take leave."
        if kind == "admission_withdrawal"
        else "I request refund of the actual payment below under the fictional university contract.",
        f"Original payment: {approval['rawAction']['paymentId']}",
        f"Paid claim basis: {packet['claimAmount']['amount']} {packet['claimAmount']['currency']}",
        f"Eligibility: {packet['eligibility']}",
        f"Classes start: {packet['policy']['classesStart']}",
        f"Promise by: {packet['deadline'] or 'Manual degree-office assessment; no automatic promise'}",
        f"Denial letter attached: {packet['documents'][2]['documentId']}",
        f"Destination: {destination['bank']} | {destination['maskedNumber'].replace(chr(8226), '*')}",
        f"SWIFT: {destination['swift']} (MOCK, from original payer bank record)",
        "No destination declared in chat or uploaded documents can replace this bank record.",
        "Tuition-only refund before classes; dormitory and NHIS paid separately, not included.",
        "Original bank fee, intermediary wire fee and cross-currency loss remain family costs.",
        f"Student signer: {packet['documents'][0]['signerId']}",
        f"Consent hash binding both forms and evidence: {approval['consentHash']}",
        f"Signature state: {approval['status']} (API WebAuthn consent, not a PDF ink signature)",
    ]
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(595, 842), invariant=1)
    c.setFont("Helvetica", 10)
    y = 795
    for line in lines:
        for part in wrap(line, 88):
            c.drawString(36, y, part)
            y -= 15
        y -= 8
    c.save()
    return buffer.getvalue()
