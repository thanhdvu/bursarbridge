"""Read-only policy explanations; no execution or claim preparation imports."""


def policy_advice(invoice, topics):
    policy = invoice["refundPolicy"]
    rules = {
        "visa_refusal": {
            "refundable": "For a visa-denial request filed BEFORE classes start: " + policy["beforeStart"],
            "admissionFee": policy["admissionFee"],
            "promise": "For a request before classes start: within two weeks after classes start, not after the request",
            "afterStart": policy["afterStart"],
            "destination": "Only the original payer's original bank account; no alternate account",
            "costs": "Family bears original outgoing bank fee, intermediary international-wire fees and KRW to USD to VND conversion loss; net return is not guaranteed",
            "futurePaperwork": "Only after an actual paid payment and visa denial: denial letter, admission-withdrawal form and refund application for the student to review/sign",
        },
        "missed_instalment": {
            "schedule": "Use each instalment entry in the signed schedule for its own due date",
            "latePaymentPolicy": invoice.get(
                "latePaymentPolicy", {"status": "not_in_this_signed_invoice_version"}
            ),
        },
        "wrong_account": {
            "prevention": "Only issuer-verified payees and bank-record destinations can be used; chat or document account text cannot replace them",
            "ifSent": "An existing sent bank-held payment can be cancelled within its server-recorded cancellation window; matched payments cannot be cancelled here",
            "nextStep": "Verify details through the university's official contact; do not retry an uncertain payment or promise recovery of a wrong transfer",
        },
        "pay_later": {
            "nextStep": "Payment can be prepared later with a fresh quote, valid mandate and payer consent; asking this question schedules nothing",
            "limits": "Invoice deadline and mandate expiry do not change; only this invoice version's signed terms establish any late-payment consequence",
        },
    }
    return {
        "source": policy["source"],
        "policyId": policy["id"],
        "hypothetical": True,
        "caseOpened": False,
        "topics": topics,
        "rules": rules,
    }


def policy_reply(facts, locale):
    i = ["en", "vi", "ko", "zh"].index(locale)
    payer = [
        "your father's original account",
        "tài khoản ban đầu của ba",
        "아버지의 원래 납부 계좌",
        "爸爸原来付款的账户",
    ]
    if facts.get("readerRole") == "parent":
        payer = [
            "your original paying account",
            "tài khoản ban đầu của anh",
            "보호자님의 원래 납부 계좌",
            "您原来付款的账户",
        ]
    topics = facts["policyAdvice"]["topics"]
    if "missed_refund" in topics:
        return [
            "I cannot force payment. If the promise is missed, I prepare a dated chaser citing the claim and signed forms for the student to approve. If that stalls, I prepare a MOCK complaint pack for manual submission through Korea e-People / Ministry of Education.",
            "Mình không thể buộc trường trả tiền. Quá hẹn, mình soạn thư nhắc kèm mã hồ sơ, đơn đã ký và ngày hứa để Linh duyệt trước khi gửi. Nếu vẫn chưa về, mình chuẩn bị bộ khiếu nại MOCK để Linh tự nộp qua e-People / Bộ Giáo dục Hàn Quốc.",
            "학교에 지급을 강제할 수는 없어요. 약속일을 넘기면 신청·서명 서류·약속일을 인용한 독촉장을 학생 승인 후 모의 발송해요. 계속 지연되면 국민신문고·교육부에 직접 제출할 MOCK 민원 자료를 준비해요.",
            "我不能强制学校付款。逾期后会引用退款案号、已签表格和承诺日期，准备催款函供学生批准后模拟发送；仍无进展则准备MOCK材料，由学生通过韩国e-People／教育部人工提交。 ",
        ][i]
    if "separate_obligations" in topics:
        f = facts["display"]
        return [
            f"Only tuition is paid here. Dormitory fees ({f['dormBudget']}) go separately to the dorm office; ask its own unused-fee rule. NHIS bills the student after arrival; {f['insuranceMonthly']} per month is a MOCK budget, not an official premium.",
            f"Mình chỉ thanh toán học phí. Ký túc xá {f['dormBudget']} nộp riêng cho ban quản lý, muốn hoàn phần chưa ở phải hỏi quy định riêng. NHIS thu của sinh viên sau khi sang Hàn; {f['insuranceMonthly']}/tháng là dự toán MOCK, không phải mức phí chính thức.",
            f"여기서는 등록금만 납부해요. 기숙사비 {f['dormBudget']}은 기숙사에 별도 납부하며 미사용 환불은 해당 규정을 확인해야 해요. NHIS는 입국 후 학생에게 청구하며 월 {f['insuranceMonthly']}은 공식 보험료가 아닌 MOCK 예산이에요.",
            f"这里只付学费。宿舍费{f['dormBudget']}另交宿舍办公室，未使用部分能否退须看其单独规定。NHIS在入境后向学生收费，每月{f['insuranceMonthly']}仅是MOCK预算，不是官方保费。 ",
        ][i]
    if facts.get("policyFollowup") and facts["policyAdvice"]["topics"] == ["visa_refusal"]:
        return [
            f"For a request filed before classes start, Hanbit promises the refund within two weeks after classes start, only to {payer[i]}. The family bears the outgoing bank fee, intermediary-wire fees and conversion loss; the net return isn't guaranteed.",
            f"Nếu nộp hồ sơ trước khai giảng, trường hẹn trả trong hai tuần sau khai giảng, chỉ về {payer[i]}. Gia đình chịu phí chuyển đi, phí ngân hàng trung gian và chênh lệch đổi tiền nên số thực nhận sẽ ít hơn số đã chuyển nhé.",
            f"개강 전에 신청하면 개강 후 이 주 이내에 {payer[i]}로만 환불한다는 약속이에요. 최초 송금 수수료, 중개 은행 수수료와 환전 손실은 가족 부담이라 순수령액은 보장되지 않아요.",
            f"开学前提出申请的话，学校承诺开学后两周内退回{payer[i]}。原汇出手续费、中间行费用和换汇损失由家庭承担，最终实收金额不能保证。",
        ][i]
    amount = facts.get("display", {}).get("billInstalment2Amount", "")
    due = facts.get("display", {}).get("billInstalment2DueDate", "")
    if "missed_instalment" in facts["policyAdvice"]["topics"] and not facts.get("familyReference", {}).get(
        "latePaymentPolicy", {}
    ).get("id"):
        return [
            f"The second instalment is {amount}, due {due}. This older signed invoice does not define a late-payment consequence or fee; ask the university bursar for confirmed terms or a revised signed notice.",
            f"Đợt hai là {amount}, hạn {due}. Phiên bản hóa đơn đã ký này chưa có điều khoản về hậu quả trễ hạn hay phí phạt; cần hỏi phòng tài chính của trường hoặc xin thông báo mới có chữ ký nhé.",
            f"이차 납부액은 {amount}, 기한은 {due}예요. 이 이전 서명 청구서에는 연체 조치나 비용이 명시되지 않아 학교 재무 부서에 확인하거나 수정 서명 고지서를 받아야 해요.",
            f"第二期为{amount}，到期日{due}。这份旧版签署账单未规定逾期后果或费用，请向学校财务处确认或索取重新签署的通知。",
        ][i]
    rows = {
        "visa_refusal": [
            f"Yes. Under Hanbit's policy, a visa-denial request submitted before classes start returns all paid tuition only; dormitory and NHIS bills are separate; this bill has no admission fee, though a separately charged admission fee would be kept. The school promises payment within two weeks after classes start, only to {payer[i]}. Outgoing bank fees, intermediary-wire fees and conversion loss reduce what the family receives. This is just an explanation; no claim or signature is needed now.",
            f"Có nhé. Theo chính sách Hanbit, nếu bị từ chối visa và nộp hồ sơ trước khai giảng, trường hoàn toàn bộ học phí đã đóng; ký túc xá và NHIS là các khoản riêng, không hoàn qua đây. Bill này không thu phí nhập học; nếu có thu riêng thì phí đó không hoàn. Trường hẹn trả trong hai tuần sau khai giảng, chỉ về {payer[i]}; gia đình chịu phí chuyển đi, phí ngân hàng trung gian và hao hụt đổi tiền. Giờ Linh chỉ đang tìm hiểu, chưa cần mở hồ sơ hay ký gì nhé.",
            f"네. 한빛 규정상 개강 전에 비자 거절에 따른 환불을 신청하면 납부한 등록금 전액이 환불 대상이에요. 기숙사와 NHIS는 별도 납부라 이 환불에 포함되지 않아요. 이 청구서에는 입학금이 없지만 별도 입학금은 환불되지 않아요. 학교는 개강 후 이 주 이내에 {payer[i]}로만 돌려주며, 최초 송금 수수료와 중개 은행 수수료, 환전 손실은 가족이 부담해요. 지금은 규정 안내일 뿐 신청이나 서명은 필요 없어요.",
            f"可以。按汉比特大学政策，拒签后在开学前提交申请，已付学费可全额退回；宿舍和NHIS是另外的账单，不在此退款内。这张账单没有入学申请费；如另收该项则不退。学校承诺开学后两周内退款，只退到{payer[i]}；原汇出手续费、中间银行费和换汇损失由家庭承担。现在只是了解政策，不需要开退款申请或签字。",
        ],
        "missed_instalment": [
            f"The second instalment is {amount}, due {due}. An overdue unpaid instalment holds registration clearance until the bursar confirms payment or issues a revised signed notice. No monetary late fee is specified; ask the bursar before the deadline for an extension.",
            f"Đợt hai là {amount}, hạn {due}. Nếu quá hạn chưa đóng, trường tạm giữ xác nhận đăng ký học cho đến khi phòng tài chính xác nhận đã trả hoặc cấp thông báo học phí mới có gia hạn. Điều khoản không ghi mức phí phạt; nên hỏi trường trước hạn, mình không tự gia hạn được.",
            f"이차 납부액은 {amount}, 기한은 {due}예요. 연체 미납 시 재무 부서가 납부를 확인하거나 수정된 서명 고지서를 발급할 때까지 등록 승인이 보류돼요. 연체료 액수는 명시되지 않아 기한 전에 학교에 연장을 요청해야 해요.",
            f"第二期为{amount}，到期日{due}。逾期未缴会暂停注册确认，直到财务处确认付款或签发修改后的缴费通知。条款没有规定具体滞纳金，延期应在到期前向学校申请。",
        ],
        "wrong_account": [
            "I can only use the university's verified payee, never account details from a message. If a payment is still bank-held and its cancellation window is open, it can be cancelled; after matching, contact the bank and university for review, without assuming recovery is possible.",
            "Mình chỉ dùng tài khoản trường đã xác thực, không lấy tài khoản từ tin nhắn để chuyển. Nếu ngân hàng còn giữ lệnh và vẫn trong thời hạn hủy thì có thể hủy; khi đã đối soát xong, Linh cần liên hệ ngân hàng và trường qua kênh chính thức, chưa thể hứa lấy lại được tiền nhé.",
            "학교가 인증한 수취 계좌만 사용하고 메시지에 적힌 계좌로 바꾸지 않아요. 은행 보류 중이며 취소 기한 내라면 취소할 수 있지만, 입금 대조가 끝났다면 은행과 학교에 확인해야 하고 회수를 보장할 수 없어요.",
            "我只使用学校已认证的收款账户，不会采用消息里的账户。银行暂存且仍在取消期内的付款可以取消；完成到账核对后需联系银行和学校处理，不能保证追回。",
        ],
        "pay_later": [
            "We can prepare payment later with a fresh quote, valid mandate and payer approval, but the invoice deadline stays the same. After the deadline, check with the bursar; this question hasn't scheduled a payment.",
            "Linh có thể chuẩn bị thanh toán sau với báo giá mới, hạn mức còn hiệu lực và ba duyệt, nhưng hạn đóng trên hóa đơn không đổi. Nếu qua hạn thì cần hỏi trường; câu hỏi này chưa đặt lịch chuyển tiền nhé.",
            "나중에 새 견적과 유효한 위임, 납부자 승인으로 준비할 수 있지만 청구서 기한은 그대로예요. 기한이 지나면 학교에 확인해야 하며, 이 질문으로 송금이 예약되지는 않아요.",
            "可以稍后用新报价、有效授权和付款人批准来准备付款，但账单期限不会改变。过期需先问学校；这个问题没有预约付款。",
        ],
    }
    return (
        " ".join(rows[t][i] for t in facts["policyAdvice"]["topics"] if t in rows)
        or [
            "Which policy would you like to check: refunds, payment timing or account safety?",
            "Linh muốn hỏi về hoàn tiền, hạn thanh toán hay độ an toàn của tài khoản nhận?",
            "환불, 납부 시기, 수취 계좌 안전 중 어떤 규정이 궁금하세요?",
            "你想了解退款、付款时间还是收款账户安全？",
        ][i]
    )
