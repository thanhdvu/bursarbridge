"""Presentation only. Signed raw actions and credentials retain canonical bytes."""

TEXT = {
    "Spring 2027 - semester 1": [
        "Spring 2027 - semester 1",
        "Học kỳ 1 – mùa xuân 2027",
        "2027년 봄학기 – 1학기",
        "2027年春季 — 第一学期",
    ],
    "Semester tuition": ["Semester tuition", "Học phí học kỳ", "학기 등록금", "学期学费"],
    "Dormitory March-June (4 months)": [
        "Dormitory March-June (4 months)",
        "Ký túc xá tháng 3–6 (4 tháng)",
        "3–6월 기숙사비 (4개월)",
        "3至6月宿舍费（4个月）",
    ],
    "Bridge insurance (fictional university group policy)": [
        "Bridge insurance (fictional university group policy)",
        "Bảo hiểm chuyển tiếp (chính sách nhóm của trường giả định)",
        "임시 보험 (가상 대학 단체 보험)",
        "过渡保险（虚构大学团体保单）",
    ],
    "MOCK refund board rate": [
        "MOCK refund board rate",
        "Tỷ giá niêm yết hoàn tiền MOCK",
        "MOCK 환불 고시 환율",
        "MOCK 退款牌价",
    ],
    "HBU-REF-01 fictional 1% charge": [
        "HBU-REF-01 fictional 1% charge",
        "Phí 1% theo chính sách giả định HBU-REF-01",
        "가상 정책 HBU-REF-01에 따른 1% 수수료",
        "虚构政策 HBU-REF-01：收取1%手续费",
    ],
    "HBU-REF-01 fictional zero retention": [
        "HBU-REF-01 fictional zero retention",
        "Không giữ lại học phí theo chính sách giả định HBU-REF-01",
        "가상 정책 HBU-REF-01: 공제 없음",
        "虚构政策 HBU-REF-01：不扣留学费",
    ],
    "HBU-REF-01 fictional 0% retention": [
        "HBU-REF-01 fictional 0% retention",
        "Không giữ lại học phí theo chính sách giả định HBU-REF-01",
        "가상 정책 HBU-REF-01: 공제 없음",
        "虚构政策 HBU-REF-01：不扣留学费",
    ],
}


TEXT.update(
    {
        "Original outward bank fee is not refunded": [
            "Original outward bank fee is not refunded",
            "Phí chuyển đi ban đầu không được hoàn",
            "최초 송금 수수료는 환불되지 않음",
            "原汇出银行费用不退",
        ],
        "MOCK KRW to USD to home-currency conversion loss": [
            "MOCK KRW to USD to home-currency conversion loss",
            "Chênh lệch đổi KRW qua USD về tiền nhà (MOCK)",
            "KRW에서 USD를 거쳐 본국 통화로 환전 손실 (MOCK)",
            "韩元经美元兑换本币的损失（MOCK）",
        ],
        "MOCK intermediary bank wire fee": [
            "MOCK intermediary bank wire fee",
            "Phí chuyển khoản qua ngân hàng trung gian (MOCK)",
            "중개 은행 송금 수수료 (MOCK)",
            "中间银行电汇费（MOCK）",
        ],

    }
)

TEXT = {translation: row for row in TEXT.values() for translation in row}


TEXT["No admission fee charged; tuition-only claim, no dormitory or insurance payment"] = [
    "No admission fee charged; tuition-only claim, no dormitory or insurance payment",
    "Không thu phí nhập học; chỉ hoàn học phí, không gồm ký túc xá và NHIS",
    "입학금 미청구; 등록금만 환불, 기숙사·NHIS 제외",
    "未收入学费；仅退学费，不含宿舍和NHIS",
]


TEXT.update(
    {
        "Health insurance after arrival": [
            "Health insurance after arrival",
            "Bảo hiểm y tế sau khi đến Hàn",
            "입국 후 건강보험",
            "入境后的医疗保险",
        ],
        "Separate dormitory notice before move-in": [
            "Separate dormitory notice before move-in",
            "Nộp theo thông báo riêng của ký túc xá trước khi nhận phòng",
            "입주 전 기숙사 별도 고지에 따라 납부",
            "入住前按宿舍单独通知缴费",
        ],
        "After arrival and enrollment; student pays the actual NHIS bill, e.g. Korean-account auto-debit": [
            "After arrival and enrollment; student pays the actual NHIS bill, e.g. Korean-account auto-debit",
            "Sau khi đến Hàn và tham gia bảo hiểm, sinh viên trả hóa đơn NHIS thực tế, có thể trích nợ tài khoản Hàn Quốc",
            "입국·가입 후 학생이 실제 NHIS 고지액을 납부하며 한국 계좌 자동이체 가능",
            "入境参保后由学生支付实际NHIS账单，可从韩国账户自动扣款",
        ],
        "Ask the dormitory office about unused fees; no exact entitlement or date verified": [
            "Ask the dormitory office about unused fees; no exact entitlement or date verified",
            "Phần ký túc xá chưa sử dụng phải hỏi ban quản lý theo quy định riêng; chưa xác minh mức hay hạn hoàn",
            "미사용 기숙사비는 기숙사 자체 규정을 확인해야 하며 환불액·기한 미확인",
            "未使用宿舍费须向宿舍办公室确认，退款金额和日期尚未核实",
        ],
        "Outside the tuition claim; actual NHIS coverage and billing rules apply": [
            "Outside the tuition claim; actual NHIS coverage and billing rules apply",
            "Không nằm trong hồ sơ hoàn học phí; áp dụng quy định bảo hiểm và thu phí thực tế của NHIS",
            "등록금 환불 대상이 아니며 실제 NHIS 보장·청구 규정 적용",
            "不在学费退款申请内，适用实际NHIS保障和收费规则",
        ],
        "Promised tuition refund has not arrived. Please confirm the wire and revised payment date.": [
            "Promised tuition refund has not arrived. Please confirm the wire and revised payment date.",
            "Khoản hoàn học phí đã quá hẹn nhưng chưa về. Xin trường xác nhận lệnh chuyển và ngày trả mới.",
            "약속한 등록금 환불이 도착하지 않았습니다. 송금과 변경 지급일을 확인해 주세요.",
            "承诺的学费退款尚未到账，请确认汇款及新的付款日期。",
        ],
        "MOCK 70,000/month planning assumption, not a verified NHIS premium": [
            "MOCK 70,000/month planning assumption, not a verified NHIS premium",
            "Dự toán MOCK 70.000 KRW/tháng, không phải mức phí NHIS chính thức",
            "월 70,000 KRW MOCK 예산이며 공식 NHIS 보험료가 아님",
            "每月70,000 KRW为MOCK预算，并非核实的NHIS保费",
        ],
        "MOCK adviser-based budget, not a payment instruction": [
            "MOCK adviser-based budget, not a payment instruction",
            "Dự toán MOCK theo chia sẻ của cố vấn, không phải lệnh thanh toán",
            "자문 기반 MOCK 예산이며 지급 지시가 아님",
            "顾问提供的MOCK预算，不是付款指令",
        ],
        "Private-rent alternative; do not also budget the dormitory": [
            "Private-rent alternative; do not also budget the dormitory",
            "Thuê nhà riêng thay cho ký túc xá; không tính cả hai",
            "민간 월세는 기숙사 대안이며 중복 계산하지 않음",
            "校外租房替代宿舍，不重复计算",
        ],
        "Bank-held standing lease; uploaded text never sets account or rent": [
            "Bank-held standing lease; uploaded text never sets account or rent",
            "Đối chiếu hợp đồng lưu tại ngân hàng; nội dung tải lên không được đặt tài khoản hay tiền thuê",
            "은행 보관 임대 기록 대조; 업로드 문구로 계좌·월세 설정 불가",
            "核对银行保存的租约记录；上传文字不能设定账户或租金",
        ],
    }
)


def localize(value, locale):
    index = ["en", "vi", "ko", "zh"].index(locale) if locale in {"en", "vi", "ko", "zh"} else 0
    if isinstance(value, list):
        return [localize(v, locale) for v in value]
    if isinstance(value, dict):
        return {
            k: v
            if k in {"rawAction", "credential", "jwt"}
            else TEXT[v][index]
            if k in {"term", "clause", "label", "when", "refundPolicy", "summary", "housing", "source"}
            and isinstance(v, str)
            and v in TEXT
            else localize(v, locale)
            for k, v in value.items()
        }
    return value
