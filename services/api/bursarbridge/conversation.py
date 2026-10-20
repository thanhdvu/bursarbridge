"""Dialogue proposals and grounded prose carry no bank parameters."""

import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .security import redact

Intent = Literal[
    "pay",
    "inform",
    "policy",
    "prepare",
    "refund",
    "rent",
    "fallback",
    "clarify_request",
    "pocket_money",
    "raise_limit",
    "registry_write",
    "export_pii",
    "crypto",
    "refund_redirect",
    "document_instruction",
    "structuring",
    "scam",
    "scam_followup",
]
BLOCKED = {
    "raise_limit",
    "registry_write",
    "export_pii",
    "crypto",
    "refund_redirect",
    "document_instruction",
    "structuring",
    "scam",
}


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Intent
    scope: Literal["remaining", "instalment"]
    needsClarification: bool


class Reply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str


def normalize(text):
    return unicodedata.normalize(
        "NFC",
        "".join(
            c
            for c in unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
            if unicodedata.category(c) != "Mn"
        ),
    ).replace("’", "'")


def tuition_mentioned(text):
    return bool(re.search(r"\b(?:hoc phi|tien hoc|tien truong|tuition|semester)\b", text)) or any(
        normalize(word) in text for word in ("등록금", "학비", "学费", "學費")
    )


def payment_mentioned(text):
    return bool(
        re.search(r"\b(?:dong|nop|tra|gui|goi|chuyen|thanh toan|pay|send|transfer|remit)\b", text)
    ) or any(
        normalize(word) in text
        for word in (
            "납부",
            "내줘",
            "내주",
            "내고",
            "내야",
            "낼",
            "내 ",
            "보내",
            "송금",
            "이체",
            "결제",
            "支付",
            "缴",
            "繳",
            "交",
            "付",
            "转",
            "轉",
            "转账",
            "轉帳",
            "汇",
            "匯",
        )
    )


def dialogue_locale(text, fallback="en"):
    """Prefer the language being spoken; attachment-only turns inherit the thread."""
    counts = {
        "ko": len(re.findall(r"[가-힣]", text)),
        "zh": len(re.findall(r"[\u3400-\u9fff]", text)),
    }
    if max(counts.values()):
        return max(counts, key=counts.get)
    lower = normalize(text)
    if re.search(r"\b(?:hoc|tien|truong|dong|nop|giup|con|ba|minh|giay|khong|hoan|han|vay|nay)\b", lower):
        return "vi"
    if re.search(
        r"\b(?:the|please|tuition|pay|send|transfer|how|when|my|help|refund|invoice|hello|what|invest|me|you|dad|need|can)\b",
        lower,
    ):
        return "en"
    return fallback


def scripted_proposal(text, documents=(), previous_scope="remaining"):
    lower = normalize(text)
    scope = previous_scope
    if any(
        normalize(x) in lower
        for x in ("instalment", "installment", "đợt", "分期", "第一笔", "분할", "회차", "first part")
    ):
        scope = "instalment"
    elif any(normalize(x) in lower for x in ("full", "toàn bộ", "hết", "全部", "전액")):
        scope = "remaining"
    intent = "fallback"
    for candidates, label in [
        (
            (
                "refund agent",
                "redirect refund",
                "refund to",
                "new refund account",
                "hoàn tiền sang",
                "退款到新",
            ),
            "refund_redirect",
        ),
        (("raise", "increase limit", "own limit", "tăng hạn mức", "nâng hạn mức", "提高限额"), "raise_limit"),
        (
            ("remember this account", "add payee", "registry", "nhớ tài khoản", "记住这个账户"),
            "registry_write",
        ),
        (
            (
                "passport number",
                "dad's passport",
                "bank credentials",
                "system prompt",
                "secret key",
                "hộ chiếu của ba",
                "护照号码",
            ),
            "export_pii",
        ),
        (("crypto", "stablecoin", "yield", "gift card", "bitcoin", "加密货币", "코인"), "crypto"),
        (("split", "uncle", "quota evasion", "chia nhỏ", "拆分"), "structuring"),
        (("police", "proof-of-funds", "verification deposit", "công an", "警察", "경찰"), "scam"),
        (
            (
                "new account",
                "bank details changed",
                "15%",
                "pre-approved",
                "ignore previous",
                "bỏ qua hướng dẫn",
                "tài khoản mới",
                "忽略之前",
            ),
            "document_instruction",
        ),
        (("visa refused", "refusal", "từ chối visa", "visa bị từ chối", "비자 거절", "拒签"), "refund"),
        (
            (
                "how much",
                "tổng",
                "chia mấy",
                "how many instalments",
                "分几期",
                "몇 회",
                "due",
                "by when",
                "bao nhiêu",
                "hạn khi nào",
                "hạn đóng",
                "견적",
                "얼마",
                "언제까지",
                "多少钱",
                "截止",
            ),
            "inform",
        ),
        (("pay rent", "monthly rent", "tiền thuê", "월세", "房租"), "rent"),
        (("prepare", "sort out", "full tuition", "trả đợt"), "pay"),
    ]:
        if any(normalize(c) in lower for c in candidates):
            intent = label
            break
    if intent == "fallback" and any(
        term in lower
        for term in (
            "tieu vat",
            "tien tieu",
            "pocket money",
            "spending money",
            "allowance",
            "용돈",
            "零花钱",
            "零用钱",
            "零用錢",
        )
    ):
        intent = "pocket_money"
    negated = bool(
        re.search(
            r"\b(?:don'?t|don t|do not|khong|dung|chua)(?:\s+\w+){0,2}\s+(?:dong|nop|tra|gui|goi|chuyen|thanh toan|pay|send|transfer)\b",
            lower,
        )
    ) or any(word in lower for word in ("不要", "别", "말고", "마세요", "않"))
    # Urgency plus a tuition action asks for help arranging payment, even when
    # phrased as "what should I do?". A factual cost/date question stays inform.
    urgent = any(
        normalize(w) in lower
        for w in ("sắp", "gấp", "trễ", "quá hạn", "urgent", "soon", "곧", "급해", "快到", "着急")
    )
    help_requested = any(
        normalize(w) in lower
        for w in ("làm sao", "giúp", "what should", "help", "어떡", "도와", "怎么办", "帮")
    )
    factual = any(
        normalize(w) in lower
        for w in ("bao nhiêu", "khi nào", "how much", "by when", "얼마", "언제까지", "多少钱", "什么时候")
    )
    if (
        intent in {"fallback", "inform"}
        and urgent
        and tuition_mentioned(lower)
        and (payment_mentioned(lower) or help_requested)
        and not factual
        and not negated
    ):
        intent = "pay"
    if intent == "fallback":
        tuition = tuition_mentioned(lower)
        payment = payment_mentioned(lower)
        if tuition and payment and not negated:
            intent = "pay"
        elif tuition or payment:
            intent = "clarify_request"
    # Separate the speech act (asking about a rule) from reporting an event or
    # requesting execution. Prohibited instructions and current taint still win.
    if intent not in BLOCKED and policy_topics(text):
        intent = "policy"
    if intent in BLOCKED:
        return Proposal(intent=intent, scope=scope, needsClarification=False)
    if any(
        any(
            w["code"] != "RENTAL_AGREEMENT_UNVERIFIED" or d["kind"] != "rental_agreement"
            for w in d["warnings"]
        )
        for d in documents
    ):
        combined = " ".join(f["value"] for d in documents for f in d["fields"]).casefold()
        intent = (
            "scam"
            if any(x in combined for x in ("police", "proof-of-funds"))
            else "refund_redirect"
            if "refund agent" in combined or "redirect refund" in combined
            else "document_instruction"
        )
    elif (
        any(d["kind"] == "refusal" and not d["warnings"] for d in documents)
        and intent not in BLOCKED
        and not hypothetical_question(text)
    ):
        # Documentary events do not depend on a particular tense or payment verb.
        intent = "refund"
    elif documents and intent == "fallback":
        intent = "prepare"
    has_number = any(len(re.sub(r"\D", "", m.group())) >= 3 for m in re.finditer(r"\d[\d,.]*", text))
    has_money_unit = bool(
        re.search(r"\d[\d,.]*\s*(?:krw|vnd|usd|cny|aud|trieu|nghin|tr\b|[km]\b|만|천|万|元)", lower)
    )
    ambiguous = intent == "pay" and (has_number or has_money_unit)
    return Proposal(intent=intent, scope=scope, needsClarification=ambiguous)


def history_for_model(thread, current):
    history = []
    for message in thread["messages"][-8:]:
        text = message.get("text")
        if text is None and message["role"] == "assistant":
            text = " ".join(e["text"] for e in message.get("events", []) if e["type"] == "token")
        if text:
            history.append({"role": message["role"], "text": redact(text[:1800])})
    history.append({"role": "user", "text": redact(current[:3000])})
    return history


def refund_question(text, focused=False):
    lower = normalize(text)
    explicit = any(normalize(w) in lower for w in ("refund", "hoàn tiền", "tiền hoàn", "환불", "退款"))
    question = any(
        normalize(w) in lower
        for w in (
            "?",
            "bao",
            "khi",
            "phí",
            "trừ",
            "làm gì",
            "làm sao",
            "when",
            "how",
            "fee",
            "what",
            "언제",
            "얼마",
            "수수료",
            "怎么",
            "多久",
            "多少",
            "费用",
        )
    )
    # Incoming/returning money is distinct from an instruction to pay a bill.
    incoming = any(
        normalize(w) in lower
        for w in (
            "tiền về",
            "nhận lại",
            "lấy lại",
            "money back",
            "return",
            "receive",
            "돌아",
            "돌려",
            "退回",
            "到账",
        )
    ) or (re.search(r"\bve\b", lower) is not None and any(w in lower for w in ("tien", "hoc phi")))
    return (
        explicit
        or (question and incoming)
        or (focused and question and not tuition_mentioned(lower) and not payment_mentioned(lower))
    )


def policy_topics(text):
    """Recognize policy subjects plus an interrogative/conditional speech act.

    Subject vocabulary is deliberately independent of whole example sentences.
    This returns topics, never financial parameters or authorization.
    """
    lower = normalize(text)

    def has(words):
        return any(normalize(w) in lower for w in words)

    question = has(
        (
            "?",
            "nếu",
            "giả sử",
            "có được",
            "được không",
            "bao lâu",
            "bao nhiêu",
            "chính sách",
            "what if",
            "if ",
            "can i",
            "could",
            "policy",
            "what happens",
            "how long",
            "면",
            "경우",
            "규정",
            "되나요",
            "있나요",
            "如果",
            "假如",
            "能否",
            "可以",
            "政策",
        )
    )
    if not question:
        return []
    not_paid = re.search(
        r"(?:school|university|truong)(?:\s+\w+){0,2}\s+(?:khong|chua|does not|doesn't|won't|not)(?:\s+\w+){0,2}\s+(?:pay|refund|tra|hoan)",
        lower,
    ) or re.search(r"학교.*(?:안|않).*(?:환불|지급|돌려)|学校.*(?:不|没).*(?:退|付)", lower)
    if not_paid:
        return ["missed_refund"]
    if has(("NHIS", "insurance", "bảo hiểm", "dorm", "ký túc", "보험", "기숙사", "保险", "宿舍")):
        return ["separate_obligations"]
    actual_refusal = has(
        (
            "visa bị từ chối",
            "visa refused",
            "visa was refused",
            "visa has been refused",
            "비자 거절됐",
            "签证拒签了",
            "拒签了",
        )
    )
    if actual_refusal and not hypothetical_question(text):
        return []
    topics = []
    if has(("visa", "비자", "签证", "拒签", "refund", "hoàn", "lấy lại", "환불", "退款")):
        topics.append("visa_refusal")
    if has(
        (
            "wrong account",
            "sai tài khoản",
            "nhầm tài khoản",
            "sai tk",
            "nhầm tk",
            "잘못된 계좌",
            "계좌를 잘못",
            "错账户",
            "错账号",
            "账户错",
        )
    ):
        topics.append("wrong_account")
    if has(
        (
            "pay later",
            "pay tomorrow",
            "trả sau",
            "đóng sau",
            "nộp sau",
            "chuyển sau",
            "나중에",
            "以后再付",
            "晚点付",
            "稍后付",
        )
    ):
        topics.append("pay_later")
    if has(("miss", "late", "overdue", "trễ", "quá hạn", "lỡ", "늦", "기한을 넘", "逾期", "错过")) and (
        tuition_mentioned(lower)
        or has(("instalment", "installment", "đợt", "hạn", "분할", "납부", "分期", "缴费"))
    ):
        topics.append("missed_instalment")
    return topics


def hypothetical_question(text):
    lower = normalize(text)
    return any(
        normalize(w) in lower for w in ("nếu", "giả sử", "what if", "if ", "면", "경우", "如果", "假如")
    )


def refund_requested_facts(text, display):
    lower = normalize(text)
    costs = any(
        normalize(w) in lower
        for w in ("phí", "trừ", "mất", "fee", "deduct", "loss", "수수료", "공제", "费用", "扣")
    )
    amount = any(normalize(w) in lower for w in ("bao nhiêu", "how much", "얼마", "多少"))
    timing = any(
        normalize(w) in lower
        for w in ("khi", "bao giờ", "bao lâu", "hẹn", "when", "how long", "언제", "多久", "什么时候")
    )
    keys = (["refundDeadline"] if timing else []) + (["refundReceivedBack"] if amount else [])
    if costs:
        keys += ["refundBankFee", "refundWireFee", "refundFxLoss", "refundRetention"]
    return [k for k in keys if k in display]


def requested_facts(text):
    lower = normalize(text)
    cost = any(normalize(w) in lower for w in ("how much", "cost", "bao nhiêu", "얼마", "多少钱"))
    date = any(normalize(w) in lower for w in ("when", "due", "hạn", "언제", "截止", "哪天", "什么时候"))
    cost = cost or "tong" in lower or "total" in lower
    schedule = any(
        normalize(w) in lower
        for w in (
            "chia",
            "mấy đợt",
            "bao nhiêu đợt",
            "how many",
            "instalments",
            "installments",
            "分期",
            "分几期",
            "몇 회",
            "분할",
        )
    )
    return (
        (["invoiceAmount", "sendAmount", "fxSource"] if cost else [])
        + (["instalmentCount", "instalmentSchedule"] if schedule else [])
        + (["dueDate"] if date else [])
    )


def display_money(value, locale="en"):
    n = Decimal(value["amount"])
    if value["currency"] == "VND":
        n = n.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    text = f"{n:,.0f}" if value["currency"] == "VND" or n == n.to_integral_value() else f"{n:,.2f}"
    if locale == "vi":
        text = text.replace(",", "_").replace(".", ",").replace("_", ".")
    return text + " " + value["currency"]


# Parallel translations keep the keyless demo truthful without a model.
ROWS = {
    "pocket_money": [
        "I understand you need pocket money. I can help with tuition and rent, but I can't arrange a personal allowance transfer.",
        "Mình hiểu Linh muốn xin ba tiền tiêu vặt. Mình chỉ hỗ trợ học phí và tiền thuê nhà, nên không chuyển tiền tiêu vặt giúp Linh được nhé.",
        "용돈이 필요하군요. 등록금과 월세는 도와드리지만 개인 용돈 송금은 지원하지 않습니다.",
        "明白，你想向爸爸要零花钱。我可以帮忙处理学费和房租，但不能办理个人零花钱转账。",
    ],
    "clarify_request": [
        "Which university bill would you like me to help you pay?",
        "Bạn muốn mình giúp thanh toán khoản nào của trường?",
        "어떤 대학 청구서 납부를 도와드릴까요?",
        "您想让我帮忙支付学校的哪笔费用？",
    ],
    "payment_pending": [
        "The bank is holding the payment during the cancellation window. Your parent can cancel it before the deadline; the university has not received it yet.",
        "Ngân hàng đang giữ khoản chuyển trong thời hạn hủy. Ba của Linh có thể hủy trước hạn; trường chưa nhận được tiền.",
        "은행이 취소 가능 시간 동안 송금을 보류하고 있습니다. 부모님이 기한 전에 취소할 수 있으며 대학은 아직 받지 않았습니다.",
        "银行正在取消期内暂存款项。家长可以在期限前取消，学校尚未收到款项。",
    ],
    "already_paid": [
        "The university has received and matched this payment. The cancellation window is closed; a visa-refusal refund uses the separate claim process.",
        "Trường đã nhận và đối soát khoản thanh toán này, nên thời hạn hủy đã hết. Nếu visa bị từ chối, mình sẽ giúp chuẩn bị hồ sơ hoàn tiền riêng.",
        "대학이 결제를 수령하고 대조를 마쳤으므로 취소 가능 시간이 끝났습니다. 비자 거절 환불은 별도 신청으로 도와드릴 수 있습니다.",
        "学校已收到款项并完成核对，取消期已结束。拒签退款需要另行提交申请。",
    ],
    "rent_executed": [
        "The rent payment is recorded within the signed monthly mandate. Repeating this request won't pay twice; the card shows the cancel window.",
        "Khoản tiền thuê đã được ghi nhận trong ủy quyền tháng. Nhắn lại không làm trả hai lần; thời hạn hủy nằm trên thẻ.",
        "월별 위임 범위 내 월세 결제가 기록되어 있습니다. 요청을 반복해도 중복 결제되지 않으며 취소 시간은 카드에서 확인할 수 있습니다.",
        "房租付款已按月度授权记录，重复请求不会重复付款，取消期限请看卡片。",
    ],
    "clarify": [
        "Do you want only the first scheduled instalment, or the full tuition? I'll use the university's signed schedule.",
        "Linh muốn trả đợt đầu theo lịch trường hay toàn bộ học phí? Mình sẽ lấy số tiền từ hồ sơ trường ký.",
        "학교 일정의 첫 분할금만 낼까요, 아니면 등록금 전액을 낼까요? 금액은 대학 서명 기록에서 가져옵니다.",
        "您是只付学校安排的首期，还是付全部学费？金额会以学校签署的记录为准。",
    ],
    "crypto": [
        "I can't invest tuition in crypto or promise returns. I can help review the tuition cost or prepare payment to the verified university.",
        "Mình không dùng tiền học để đầu tư crypto hay hứa hẹn lợi nhuận. Mình có thể giúp Linh xem chi phí hoặc chuẩn bị trả học phí cho trường đã xác minh.",
        "등록금을 코인에 투자하거나 수익을 약속할 수는 없습니다. 등록금 비용 확인이나 검증된 대학 결제 준비는 도와드릴 수 있습니다.",
        "我不能把学费用于加密货币投资或承诺收益，但可以帮您查看学费成本或准备向已核验大学付款。",
    ],
    "export_pii": [
        "I can't share someone else's passport or bank details. I can show payment status without exposing private documents.",
        "Mình không chia sẻ hộ chiếu hay thông tin ngân hàng riêng của người khác. Linh vẫn có thể xem trạng thái thanh toán mà không cần những giấy tờ đó.",
        "다른 사람의 여권이나 은행 정보는 공유할 수 없습니다. 개인정보 없이 결제 상태를 확인해 드릴 수 있습니다.",
        "我不能透露他人的护照或银行资料，可以在不暴露私人文件的情况下查看付款状态。",
    ],
    "refund_redirect": [
        "Refunds can return only to the original payer. I can track that refund; an outside agent cannot change its destination.",
        "Tiền hoàn chỉ được về người thanh toán ban đầu. Mình có thể theo dõi khoản hoàn đó; bên môi giới không thể đổi nơi nhận tiền.",
        "환불은 원래 납부자에게만 가능합니다. 환불 추적은 도와드리지만 외부 대행사가 수취 계좌를 바꿀 수는 없습니다.",
        "退款只能退回原付款人。我可以跟进退款，外部代理无权更改收款账户。",
    ],
    "document_instruction": [
        "I won't use bank details or instructions from a document. Verify changes using the university's published contact; the original verified payee remains available.",
        "Mình không lấy tài khoản mới hay lệnh chuyển tiền từ nội dung giấy tờ. Linh hãy xác minh thay đổi qua đầu mối công khai của trường; người nhận đã xác minh vẫn giữ nguyên.",
        "문서에 적힌 새 계좌나 지시로 송금하지 않습니다. 변경 사항은 대학 공식 연락처로 확인해 주세요.",
        "我不会按文件中的新账户或指令转账。请通过学校公布的联系方式核实变更。",
    ],
    "raise_limit": [
        "I can't raise my own limits. Your parent must review and sign a new mandate.",
        "Mình không tự nâng hạn mức. Bác Minh cần xem và ký ủy quyền mới nếu muốn thay đổi.",
        "제 한도를 스스로 올릴 수 없습니다. 부모님이 새 위임을 검토하고 서명해야 합니다.",
        "我不能自行提高限额，需要家长审核并签署新的授权。",
    ],
    "registry_write": [
        "Chat cannot register a university account. A trusted issuer must vouch for the payee first.",
        "Tin nhắn không thể đăng ký tài khoản của trường. Người nhận cần được bên phát hành tin cậy chứng thực trước.",
        "채팅으로 대학 계좌를 등록할 수 없습니다. 신뢰된 발급자의 수취인 인증이 먼저 필요합니다.",
        "聊天不能登记大学账户，收款人必须先由可信签发方认证。",
    ],
    "structuring": [
        "I can't split payments to evade FX rules. Use the bank's documented tuition route with admission and fee documents.",
        "Mình không chia nhỏ thanh toán để lách quy định ngoại hối. Gia đình có thể đi theo hồ sơ học phí hợp lệ của ngân hàng, kèm thư nhập học và thông báo học phí.",
        "외환 규정을 피하려고 분할 송금할 수는 없습니다. 입학 및 학비 서류를 갖춘 은행 절차를 이용해 주세요.",
        "不能通过拆分付款规避外汇规定，请凭录取和学费材料走银行的合规学费流程。",
    ],
    "scam": [
        "This matches an authority-impersonation scam. Nothing will be transferred; contact the student independently and ask the home co-signer to review.",
        "Yêu cầu này có dấu hiệu giả danh cơ quan chức năng. Mình không chuyển tiền; gia đình hãy liên hệ trực tiếp với Linh qua kênh quen thuộc và nhờ người đồng ký ở nhà kiểm tra.",
        "기관 사칭 사기 징후가 있습니다. 송금하지 않겠습니다. 학생에게 별도 연락하고 국내 공동 서명자와 확인해 주세요.",
        "这符合冒充执法机关的诈骗特征，不会转账。请独立联系学生，并请国内共同签署人核实。",
    ],
    "fallback": [
        "I can help with tuition, study documents and visa-refusal refunds. Tell me what you need there and I'll take the next step.",
        "Mình hỗ trợ học phí, hồ sơ du học và hoàn tiền khi bị từ chối visa. Linh cứ nói việc cần làm trong những phần đó nhé.",
        "등록금, 유학 서류, 비자 거절 환불을 도와드릴 수 있습니다. 필요한 일을 말씀해 주세요.",
        "我可以帮助处理学费、留学材料和拒签退款，请告诉我您需要办理什么。",
    ],
    "CAP_EXCEEDED": [
        "The amount exceeds the signed limit. Your parent must review a new mandate first.",
        "Khoản này vượt hạn mức đã ký. Bác Minh cần xem và ký ủy quyền mới trước.",
        "서명된 한도를 초과합니다. 부모님의 새 위임 검토가 필요합니다.",
        "金额超出已签署的限额，需要家长先审核新的授权。",
    ],
    "SANCTIONS_REVIEW": [
        "The sanctions check requires review. I won't send the payment.",
        "Kết quả sàng lọc cấm vận cần được kiểm tra. Mình chưa chuyển tiền.",
        "제재 심사 검토가 필요하므로 송금하지 않습니다.",
        "制裁筛查需要复核，暂不付款。",
    ],
    "FROZEN_OR_UNAVAILABLE": [
        "Outgoing payments are paused; refunds to the original payer continue. Your parent can unfreeze to restore the signed limits.",
        "Tiền chuyển đi đang tạm dừng; tiền hoàn về tài khoản gốc vẫn tiếp tục. Ba mở đóng băng để khôi phục hạn mức đã ký nhé.",
        "결제는 보류 중입니다. 기록은 확인할 수 있으며 부모님이 정지 상태를 검토할 수 있습니다.",
        "付款已暂停，仍可查看记录，请家长检查冻结状态。",
    ],
    "outage": [
        "The assistant is temporarily unavailable. Payments are paused; records remain available.",
        "Trợ lý đang gián đoạn. Thanh toán đã tạm dừng; Linh vẫn xem được hồ sơ.",
        "일시적으로 응답할 수 없어 결제를 보류합니다. 기록은 확인할 수 있습니다.",
        "助手暂时不可用，付款已暂停，仍可查看记录。",
    ],
    "refund": [
        "I'm sorry about the visa decision. The refund claim is ready for your signature; it can return only to the original payer.",
        "Tiếc quá Linh ạ. Mình đã chuẩn bị hồ sơ hoàn tiền để Linh ký; tiền chỉ được hoàn về người đã thanh toán ban đầu.",
        "비자 결과가 안타깝습니다. 서명할 환불 신청을 준비했습니다. 원래 납부자에게만 환불됩니다.",
        "很遗憾听到拒签的消息。退款申请已准备好，等待您签署；款项只会退给原付款人。",
    ],
    "refusal_required": [
        "Upload the visa refusal letter here and I'll prepare the refund claim for your review.",
        "Linh gửi thư từ chối visa ở đây nhé, mình sẽ chuẩn bị hồ sơ hoàn tiền để Linh xem và ký.",
        "비자 거절 통지서를 올려 주시면 검토할 환불 신청을 준비하겠습니다.",
        "请上传拒签信，我会准备退款申请供您核对。",
    ],
}


def _scripted_reply(facts, locale):
    i = ["en", "vi", "ko", "zh"].index(locale)
    f, outcome = facts.get("display", {}), facts["outcome"]
    if outcome == "refused_unpaid":
        if facts.get("readerRole") == "parent" and locale == "vi":
            return "Em rất tiếc vì kết quả visa của con. Học phí chưa chuyển nên không cần thu hồi tiền; yêu cầu đóng học phí đã dừng và thông báo đã có trong ứng dụng gia đình. Anh nhắc Linh liên hệ phòng tuyển sinh để rút nhập học hoặc hỏi cách nộp lại kỳ sau nhé; chưa có đơn nào được gửi thay con."
        return [
            "I'm sorry about the visa decision. No tuition was paid, so there is nothing to recover; I have stopped the tuition request and put a notice for your father in the family app. Ask admissions about withdrawing and reapplying next intake; no withdrawal has been submitted for you.",
            "Mình rất tiếc vì kết quả visa. Học phí chưa chuyển nên không có tiền cần lấy lại; mình đã dừng yêu cầu đóng học phí và để thông báo cho ba trong ứng dụng. Linh liên hệ phòng tuyển sinh để rút nhập học hoặc hỏi cách nộp lại kỳ sau nhé; mình chưa gửi đơn thay Linh.",
            "비자 결과에 마음이 무겁겠어요. 등록금을 납부하지 않아 돌려받을 돈은 없고, 납부 요청은 중단했으며 아버지께 가족 앱 알림을 남겼어요. 입학처에 입학 철회와 다음 학기 재지원 절차를 문의해 주세요. 철회 신청을 대신 제출한 것은 아니에요.",
            "很遗憾听到签证结果。学费还没支付，所以没有需要追回的钱；我已停止缴费请求，并在家庭应用里给爸爸留了通知。请向招生办公室咨询撤回入学和下一学期重新申请；我没有代为提交退学申请。",
        ][i]
    if outcome == "domain_notice":
        code = facts.get("reason")
        if code in {"FROZEN", "FROZEN_OR_UNAVAILABLE"}:
            return [
                "Outgoing payments are paused; incoming refunds continue. Your parent can unfreeze with a passkey to restore the signed limits.",
                "Tiền chuyển đi đang tạm dừng; tiền hoàn vẫn về tài khoản gốc. Ba dùng passkey mở lại để khôi phục hạn mức đã ký nhé.",
                "결제가 일시 중지됐어요. 아버지께서 동결 사유를 확인하고 패스키로 해제해 주세요.",
                "付款已暂停。请爸爸查看冻结原因，再用通行密钥解除。 ",
            ][i]
        if code in {"CHAIN_UNAVAILABLE", "CHAIN_REGISTRATION_PENDING"}:
            return [
                "Verification is catching up; I cannot prepare a payment yet. Please try again shortly.",
                "Hệ thống đang đồng bộ xác minh nên mình chưa thể chuẩn bị thanh toán. Linh thử lại sau một chút nhé.",
                "검증을 동기화하고 있어 아직 결제를 준비할 수 없어요. 잠시 후 다시 시도해 주세요.",
                "系统正在同步核验，暂时无法准备付款。请稍后重试。 ",
            ][i]
        if code in {"CREDENTIAL_REVOKED", "CREDENTIAL_INVALID"}:
            return [
                "The university's payee credential is revoked or invalid, so I cannot use it. Ask the university to issue a valid signed record before trying again.",
                "Chứng thực người nhận của trường đã bị thu hồi hoặc không còn hợp lệ nên mình không thể dùng. Linh nhờ trường cấp lại hồ sơ có chữ ký hợp lệ nhé.",
                "대학의 수취인 인증이 취소됐거나 유효하지 않아 사용할 수 없어요. 대학에 유효한 서명 기록을 다시 요청해 주세요.",
                "学校的收款凭证已撤销或无效，暂时不能使用。请学校重新提供有效的签名记录。",
            ][i]
        if code in {"APPROVAL_EXPIRED", "QUOTE_EXPIRED"}:
            return [
                "This quote or approval has expired. Request a new quote and ask the payer to review and sign it again.",
                "Báo giá hoặc yêu cầu duyệt đã hết hạn. Linh lấy báo giá mới rồi nhờ ba xem và ký lại nhé.",
                "견적이나 승인이 만료됐어요. 새 견적을 받은 뒤 납부자에게 다시 확인과 서명을 부탁해 주세요.",
                "报价或审批已过期。请获取新报价，再请付款人重新确认并签署。",
            ][i]
        if code == "ROLE_REQUIRED":
            return [
                "This step needs the student or payer identified on the approval. Please ask that family member to complete it from their own screen.",
                "Bước này cần đúng sinh viên hoặc người thanh toán ghi trên yêu cầu duyệt thực hiện. Linh nhờ người đó mở màn hình của mình để làm tiếp nhé.",
                "이 단계는 승인에 지정된 학생 또는 납부자가 진행해야 해요. 해당 가족 구성원의 화면에서 완료해 주세요.",
                "这一步需要审批中指定的学生或付款人操作。请对应的家人在自己的页面完成。",
            ][i]
        if code == "REFUND_FORM_REQUIRES_REVIEW":
            return [
                "The refund forms need university review before this step can continue. Please ask the international office to check the claim.",
                "Hồ sơ hoàn phí cần trường xem xét trước khi làm tiếp. Linh nhờ phòng quốc tế kiểm tra yêu cầu này nhé.",
                "환불 서류는 대학 검토가 먼저 필요해요. 국제처에 청구 내용을 확인해 달라고 요청해 주세요.",
                "退款表格需要学校先审核。请联系国际办公室核查申请后再继续。",
            ][i]
        return [
            "I couldn't complete this step with the current verified records. Please review the notice and correct the missing or changed requirement before trying again.",
            "Mình chưa thể hoàn tất bước này với hồ sơ đã xác minh hiện có. Linh xem thông báo, bổ sung hoặc sửa phần còn thiếu rồi thử lại nhé.",
            "현재 확인된 기록으로는 이 단계를 완료할 수 없어요. 안내에 따라 누락되거나 변경된 조건을 확인한 뒤 다시 시도해 주세요.",
            "现有已核验资料还不能完成这一步。请按提示补充或更正所需资料后重试。 ",
        ][i]
    if outcome == "rent_needs":
        return [
            "Please upload the rental agreement; your parent signs the monthly rent limit. I will then use only the bank-checked landlord account.",
            "Linh gửi hợp đồng thuê nhà, rồi ba ký hạn mức thuê hằng tháng nhé. Mình chỉ trả cho chủ nhà đã được ngân hàng đối chiếu.",
            "임대차 계약서를 올리고 아버지께 월세 한도 서명을 부탁해 주세요. 은행이 확인한 집주인 계좌만 사용해요.",
            "请上传租约，再请爸爸签署每月房租限额。我只使用银行核验并与租约一致的房东账户。 ",
        ][i]
    if outcome == "registration_required":
        return [
            f"The signed payment window is {f.get('registrationOpens', '')} to {f.get('registrationCloses', '')}; today in the demo is {f.get('simulatedToday', '')}. Please wait for the window or ask the bursar for revised signed terms.",
            f"Hôm nay trong demo là {f.get('simulatedToday', '')}; đợt này nhận tiền từ {f.get('registrationOpens', '')} đến {f.get('registrationCloses', '')}. Linh chờ đúng đợt hoặc hỏi trường xin thông báo mới nhé.",
            f"모의 날짜는 {f.get('simulatedToday', '')}, 납부 기간은 {f.get('registrationOpens', '')}부터 {f.get('registrationCloses', '')}까지예요. 기간을 기다리거나 학교에 수정 고지서를 요청해 주세요.",
            f"演示日期为{f.get('simulatedToday', '')}，缴费窗口为{f.get('registrationOpens', '')}至{f.get('registrationCloses', '')}。请等窗口开放，或联系学校取得重新签署的通知。 ",
        ][i]
    if outcome == "policy":
        from .policy_questions import policy_reply

        return policy_reply(facts, locale)
    if outcome == "refund_info":
        policy = facts["refundPolicy"]
        if not policy["beforeStart"]:
            return [
                "The degree office must assess this after-start claim; there is no confirmed net amount or promise date yet.",
                "Trường phải xét riêng hồ sơ sau khai giảng nên chưa chốt số tiền thực nhận hay ngày trả; mình không áp bảng hoàn của khóa tiếng nhé.",
                "개강 후 학위 과정 환불은 담당 부서 심사가 필요해 아직 실수령액과 지급일이 확정되지 않았어요.",
                "开学后的学位项目退款需由办公室核定，目前还没有确认的实收金额和付款日期。 ",
            ][i]
        keys = facts.get("requestedFacts", [])
        parts = []
        if "refundDeadline" in keys:
            parts.append(
                [
                    f"The school's promise is {f['refundDeadline']}, within two weeks after classes start; I'll follow up if it is late.",
                    f"Trường hẹn trả trước {f['refundDeadline']}, trong hai tuần sau khai giảng; quá hẹn mình sẽ nhắc trường nhé.",
                    f"학교 약속일은 {f['refundDeadline']}로, 개강 후 이 주 이내예요. 늦어지면 확인을 요청할게요.",
                    f"学校承诺在 {f['refundDeadline']} 前退款，也就是开学后两周内，逾期我会跟进。 ",
                ][i]
            )
        if "refundReceivedBack" in keys:
            parts.append(
                (
                    [
                        f"The estimated return is {f['refundReceivedBack']} after bank fees and conversion loss.",
                        f"Ước tính hoàn lại {f['refundReceivedBack']} sau phí ngân hàng và chênh lệch đổi tiền nhé.",
                        f"은행 수수료와 환전 손실을 뺀 예상 환불액은 {f['refundReceivedBack']}이에요.",
                        f"扣除银行费用和换汇损失，预计退回 {f['refundReceivedBack']}。 ",
                    ]
                    if not policy["received"]
                    else [
                        f"The original payer received {f['refundReceivedBack']} after bank fees and conversion loss.",
                        f"Khoản thực nhận là {f['refundReceivedBack']} sau phí ngân hàng và chênh lệch đổi tiền nhé.",
                        f"은행 수수료와 환전 손실을 뺀 {f['refundReceivedBack']}이 원래 납부 계좌에 입금됐어요.",
                        f"扣除银行费用和换汇损失后，原付款人已收到 {f['refundReceivedBack']}。 ",
                    ]
                )[i]
            )
        if "refundBankFee" in keys:
            parts.append(
                [
                    f"The costs are the original bank fee {f['refundBankFee']}, intermediary wire fee {f['refundWireFee']} and conversion loss {f['refundFxLoss']}; admission retention is {f['refundRetention']} because none was charged.",
                    f"Các khoản trừ gồm phí chuyển đi {f['refundBankFee']}, phí ngân hàng trung gian {f['refundWireFee']} và chênh lệch đổi tiền {f['refundFxLoss']}; trường giữ lại {f['refundRetention']} vì bill không thu phí nhập học.",
                    f"최초 은행 수수료 {f['refundBankFee']}, 중개 은행 수수료 {f['refundWireFee']}, 환전 손실 {f['refundFxLoss']}이 공제돼요. 입학금은 청구되지 않아 유보액은 {f['refundRetention']}이에요.",
                    f"扣除原汇出费用 {f['refundBankFee']}、中间银行费 {f['refundWireFee']} 和换汇损失 {f['refundFxLoss']}；未收入学申请费，所以学校扣留额为 {f['refundRetention']}。 ",
                ][i]
            )
        if parts:
            return " ".join(parts)
        return [
            "I'm tracking the same refund case. The card shows its current stage; a pending student signature is needed only if the forms have not yet been filed.",
            "Mình vẫn theo dõi cùng hồ sơ hoàn tiền này nhé. Thẻ bên trên cho biết đang đến bước nào; chỉ cần Linh ký nếu hồ sơ còn chờ nộp.",
            "같은 환불 건을 계속 확인하고 있어요. 카드에 현재 단계가 표시되고, 아직 제출 전인 경우에만 학생 서명이 필요해요.",
            "我会继续跟进同一笔退款，卡片显示当前进度；只有尚未提交的申请才需要学生签署。 ",
        ][i]
    if outcome == "scam_followup":
        return [
            "End the suspicious call and verify through an official published contact. This stays in the same case; you don't need another co-sign.",
            "Linh ngắt cuộc gọi đó nhé, rồi tự gọi lại qua số công khai của cơ quan để xác minh. Mình giữ cùng hồ sơ này, không cần nhờ Lan ký lại.",
            "의심스러운 통화는 끊고 공식 공개 연락처로 직접 확인해 주세요. 같은 사건에서 계속 도와드리며 공동 서명을 다시 요청하지 않아요.",
            "请先挂断可疑来电，再通过官方公开联系方式独立核实。我们会在同一个事件中继续处理，无需再次共同签署。",
        ][i]
    if outcome == "chain_unavailable":
        return [
            "Chain verification is temporarily unavailable. I'll retry automatically; you can keep chatting and preparing documents.",
            "Kết nối xác minh đang gián đoạn, mình sẽ tự thử lại. Linh vẫn có thể nhắn tin và gửi giấy tờ nhé.",
            "검증 연결이 잠시 중단되어 자동으로 다시 시도할게요. 대화와 서류 준비는 계속할 수 있어요.",
            "验证连接暂时不可用，我会自动重试；您仍可以继续聊天和准备材料。",
        ][i]
    if outcome == "rent_executed":
        status = facts.get("paymentStatus", "sent")
        return {
            "sent": [
                "The bank is holding the rent payment during the cancel window; the landlord has not received it yet.",
                "Ngân hàng đang giữ khoản tiền thuê trong thời hạn hủy; chủ nhà chưa nhận được tiền nhé.",
                "은행이 취소 가능 시간 동안 월세 송금을 보류 중이며, 임대인은 아직 받지 않았어요.",
                "银行正在取消期内暂存房租，房东还没有收到款项。",
            ],
            "matched": [
                "The rent payment has arrived and been matched; the cancel window has closed.",
                "Tiền thuê đã đến nơi và được đối soát; thời hạn hủy đã hết nhé.",
                "월세가 도착해 대조가 끝났고 취소 가능 시간도 지났어요.",
                "房租已到账并完成核对，取消期已结束。",
            ],
        }.get(
            status,
            [
                "The rent payment was cancelled; a new payment would need a fresh request.",
                "Khoản tiền thuê đã hủy; muốn thanh toán lại cần một yêu cầu mới nhé.",
                "월세 송금이 취소되어 다시 납부하려면 새 요청이 필요해요.",
                "房租付款已取消，如需重新付款请重新发起请求。",
            ],
        )[i]
    if outcome not in {
        "inform",
        "prepare",
        "payment_blocked",
        "approval",
        "executed",
        "refund",
        "refund_parent",
    }:
        return ROWS.get(facts.get("reason", outcome), ROWS["fallback"])[i]
    if outcome == "refund_parent":
        policy = facts["refundPolicy"]
        if policy["claimStatus"] == "reconciled":
            return [
                "The refund reached your original account. The statement separates bank fees and conversion loss.",
                "Tiền hoàn đã về tài khoản đã thanh toán của bạn. Bảng đối soát tách riêng phí ngân hàng và chênh lệch đổi tiền nhé.",
                "원래 납부 계좌로 환불됐어요. 명세서에서 은행 수수료와 환전 손실을 확인하실 수 있어요.",
                "退款已回到您原来的付款账户，对账单分别列明银行费用和换汇损失。 ",
            ][i]
        name = policy["studentSigner"]
        action = (
            [
                f"{name} needs to send the denial letter and sign the withdrawal and refund forms. ",
                f"{name} cần gửi thư từ chối visa và ký đơn hủy nhập học cùng đơn hoàn tiền. ",
                f"{name} 학생이 거절 통지서를 보내고 입학 포기서와 환불 신청서에 서명해야 해요. ",
                f"请让{name}提交拒签信并签署放弃入学和退款申请。 ",
            ][i]
            if policy["studentMustAct"]
            else ""
        )
        if not policy["beforeStart"]:
            return (
                action
                + [
                    "After classes start, the degree office must assess the refund; I'll track its response.",
                    "Đã khai giảng nên phòng phụ trách chương trình phải xét khoản hoàn; mình sẽ theo dõi trả lời của trường.",
                    "개강 후에는 학위 담당 부서의 환불 심사가 필요해요. 답변을 확인할게요.",
                    "开学后需要学位项目办公室核定退款，我会跟进答复。 ",
                ][i]
            )
        return (
            action
            + [
                "For a before-start request, the school promises payment within two weeks after classes start. No admission fee was charged; bank fees and conversion losses remain family costs. The destination stays your original account.",
                "Nếu nộp trước khai giảng, trường hẹn trả trong hai tuần sau khai giảng. Bill này không thu phí nhập học; gia đình chịu phí ngân hàng và chênh lệch đổi tiền. Tiền chỉ về tài khoản bạn đã dùng để trả nhé.",
                "개강 전 신청은 개강 후 이 주 안에 환불해요. 이 청구서에는 입학금이 없고 은행 수수료와 환전 손실은 가족 부담이에요. 원래 납부 계좌로만 돌아와요.",
                "开学前申请，学校承诺开学后两周内退款。本账单未收入学费，银行费用和换汇损失由家里承担，只退回您原来的付款账户。 ",
            ][i]
        )
    if outcome == "refund":
        if not facts.get("refundPolicy", {}).get("beforeStart", True):
            return [
                "Classes have started, so the degree office must assess the refund. Please review and sign the withdrawal and refund forms; I won't apply a language-course day table.",
                "Đã khai giảng nên phòng phụ trách chương trình phải xét khoản hoàn. Linh xem và ký đơn hủy nhập học cùng đơn hoàn tiền nhé; mình không áp bảng hoàn của khóa tiếng.",
                "개강 후라 학위 담당 부서의 환불 심사가 필요해요. 입학 포기서와 환불 신청서를 확인하고 서명해 주세요. 어학 과정 환불표는 적용하지 않아요.",
                "已经开学，需要学位项目办公室核定退款。请核对并签署放弃入学及退款申请，不套用语言课程的退款表。",
            ][i]
        return [
            f"Please sign the withdrawal and refund forms before classes start. Hanbit promises payment by {f['refundDeadline']}; the estimated {f['refundReceivedBack']} returns only to your father's original account, after bank/FX costs.",
            f"Linh ký đơn hủy nhập học và đơn hoàn tiền trước khai giảng nhé. Trường hẹn trả chậm nhất {f['refundDeadline']}; ước tính {f['refundReceivedBack']} về đúng tài khoản gốc của ba, sau phí ngân hàng và đổi tiền.",
            f"개강 전에 입학 포기서와 환불 신청서에 서명해 주세요. 학교 약속일은 {f['refundDeadline']}이며, 은행·환전 비용을 뺀 예상 {f['refundReceivedBack']}은 아버지의 원래 계좌로만 돌아와요.",
            f"请在开学前签署放弃入学和退款申请。学校承诺在{f['refundDeadline']}前退款；扣除银行和换汇成本后预计{f['refundReceivedBack']}，只退回爸爸原来的付款账户。",
        ][i]
    if outcome == "inform" and (
        "instalmentSchedule" in facts.get("requestedFacts", [])
        or "fxSource" in facts.get("requestedFacts", [])
    ):
        keys = facts["requestedFacts"]
        base_keys = [k for k in keys if k not in {"instalmentCount", "instalmentSchedule", "fxSource"}]
        text = _scripted_reply({**facts, "requestedFacts": base_keys}, locale) if base_keys else ""
        if "instalmentSchedule" in keys:
            text += (
                " "
                + [
                    f"The signed invoice allows {f['instalmentCount']} instalments: {f['instalmentSchedule']}.",
                    f"Hóa đơn trường đã ký chia {f['instalmentCount']} đợt: {f['instalmentSchedule']} nhé.",
                    f"학교 서명 청구서는 {f['instalmentCount']}회 분할 납부예요: {f['instalmentSchedule']}.",
                    f"学校签署的账单分 {f['instalmentCount']} 期：{f['instalmentSchedule']}。 ",
                ][i]
            )
        if "fxSource" in keys:
            text += (
                " "
                + [
                    f"Estimate source: {f['fxSource']}.",
                    f"Ước tính theo {f['fxSource']}.",
                    f"예상 환율 출처: {f['fxSource']}.",
                    f"估算汇率来源：{f['fxSource']}。 ",
                ][i]
            )
        return text.strip()
    if outcome == "inform":
        keys = facts.get("requestedFacts", [])
        if not keys:
            return [
                "Do you mean the bill to pay or a refund coming back?",
                "Bạn đang hỏi về tiền cần đóng hay tiền hoàn về?",
                "납부할 청구서에 관한 질문인가요, 돌아올 환불금에 관한 질문인가요?",
                "你问的是待付账单，还是退回的钱款？",
            ][i]
        if facts.get("invoiceStatus"):
            status = (
                [
                    "This invoice is already paid.",
                    "Khoản này đã thanh toán rồi nhé.",
                    "이미 납부된 청구서예요.",
                    "这笔账单已经付清。",
                ]
                if facts["invoiceStatus"] == "paid"
                else [
                    "The bank is holding the authorized payment.",
                    "Ngân hàng đang giữ khoản đã duyệt trong thời hạn hủy nhé.",
                    "승인된 송금은 은행에서 보류 중이에요.",
                    "银行正在暂存已获批准的款项。",
                ]
            )[i]
            return (
                _scripted_reply({k: v for k, v in facts.items() if k != "invoiceStatus"}, locale)
                + " "
                + status
            )
        if keys == ["dueDate"]:
            return [
                f"It's due {f['dueDate']}.",
                f"Hạn đóng là {f['dueDate']} nhé.",
                f"납부 기한은 {f['dueDate']}이에요.",
                f"截止日期是 {f['dueDate']}。 ",
            ][i]
        if "dueDate" not in keys:
            return [
                f"The semester bill is {f['invoiceAmount']}; today's estimate including fees is {f['sendAmount']}.",
                f"Tổng tiền kỳ này là {f['invoiceAmount']}; tính cả phí, hôm nay khoảng {f['sendAmount']} nhé.",
                f"이번 학기 청구액은 {f['invoiceAmount']}, 수수료 포함 현재 예상액은 {f['sendAmount']}이에요.",
                f"这学期账单共 {f['invoiceAmount']}，今天含手续费约 {f['sendAmount']}。 ",
            ][i]
        return [
            f"The semester bill is {f['invoiceAmount']}, due {f['dueDate']}; today's estimate including fees is {f['sendAmount']}.",
            f"Tổng tiền kỳ này là {f['invoiceAmount']}, hạn đóng {f['dueDate']}; tính cả phí, hôm nay khoảng {f['sendAmount']} nhé.",
            f"이번 학기 청구액은 {f['invoiceAmount']}, 기한은 {f['dueDate']}이고 수수료 포함 현재 예상액은 {f['sendAmount']}입니다.",
            f"这学期账单共 {f['invoiceAmount']}，截止 {f['dueDate']}；今天含手续费约 {f['sendAmount']}。",
        ][i]
    if outcome == "approval":
        if facts.get("readerRole") == "parent":
            return [
                "You can review and sign the payment card now.",
                "Bạn có thể mở thẻ thanh toán để xem và ký duyệt nhé.",
                "결제 카드를 확인하고 서명해 주세요.",
                "您可以查看付款卡片并签字确认。",
            ][i]
        return [
            "Your father can review and sign the payment card now.",
            "Ba của Linh có thể mở thẻ thanh toán để xem và ký duyệt nhé.",
            "아버지께서 결제 카드를 확인하고 서명하실 수 있어요.",
            "爸爸现在可以查看付款卡片并签字确认。",
        ][i]
    if outcome == "executed":
        return [
            "The bank is holding the payment; your parent can still cancel during the window on the card.",
            "Ngân hàng đang giữ khoản chuyển; ba vẫn có thể hủy trong thời hạn trên thẻ nhé.",
            "은행에서 송금을 보류 중이에요. 카드의 취소 기한까지 부모님이 취소할 수 있어요.",
            "银行正在暂存款项，家长仍可在卡片显示的期限内取消。 ",
        ][i]
    if outcome == "payment_blocked" and facts.get("reason") == "MANDATE_REQUIRED":
        return [
            "Your parent needs to sign the tuition limit first; I'll continue when it's ready.",
            "Bác Minh cần ký hạn mức học phí trước nhé, xong mình sẽ tiếp tục giúp Linh.",
            "먼저 부모님이 등록금 한도에 서명해 주셔야 해요. 완료되면 이어서 준비할게요.",
            "需要家长先签署学费限额，签好后我会接着办理。 ",
        ][i]
    if facts.get("missingDocuments"):
        names = [
            ["invoice PDF", "admission letter"],
            ["bản PDF hóa đơn", "thư nhập học"],
            ["청구서 PDF", "입학허가서"],
            ["账单 PDF", "录取通知书"],
        ][i]
        missing = ", ".join(
            dict(zip(["invoice", "admission"], names)).get(k, k) for k in facts["missingDocuments"]
        )
        return [
            f"Upload {missing} here and I'll continue.",
            f"Linh gửi {missing} ở đây nhé, mình sẽ làm tiếp.",
            f"{missing}를 여기에 올려 주시면 이어서 준비할게요.",
            f"请在这里上传{missing}，我会接着准备。 ",
        ][i]
    return ROWS.get(facts.get("reason"), ROWS["fallback"])[i]


def scripted_reply(facts, locale):
    text = _scripted_reply(facts, locale)
    student = facts.get("readerRole", "student") == "student"
    parent = facts.get("readerRole") == "parent"
    for old, new in {
        "Bác Minh": "Ba của Linh" if student else "Bạn" if parent else "Người thanh toán",
        "bác Minh": "ba" if student else "bạn" if parent else "người thanh toán",
        "Your parent": "Your father" if student else "You" if parent else "The payer",
        "your parent": "your father" if student else "you" if parent else "the payer",
        "부모님이": "아버지께서" if student else "직접" if parent else "납부자가",
        "부모님": "아버지" if student else "납부자",
        "家长": "爸爸" if student else "您" if parent else "付款人",
    }.items():
        text = text.replace(old, new)
    if student and locale == "vi":
        text = text.replace("Bạn", "Linh").replace("bạn", "Linh")
    # Parent guidance names the student as the actor, rather than the reader.
    if parent and locale == "vi" and facts["outcome"] not in {"refund_parent", "refused_unpaid"}:
        text = text.replace("Ba của Linh", "Bạn").replace("Linh", "bạn")
    if parent and locale == "vi":
        text = text.replace("Bạn", "Anh").replace("bạn", "anh")
    if facts.get("readerRole") == "cosigner" and locale == "vi":
        text = text.replace("Bạn", "Chị").replace("bạn", "chị")
    return text
