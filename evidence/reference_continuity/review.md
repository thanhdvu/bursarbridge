# Stable family reference: verification and reading review

The reply projection previously filtered facts twice: by recognized policy topic, then by outcome/requested keys. This made an elliptical follow-up lose terms already established in the same thread. The projection now supplies a stable, locally signature-verified family reference on every turn: bill and itemized amounts, signed schedule/dates, refund and late-payment policies, bank limits and current payment/refund state. No new question/intent classes were added. Thread history supplies the conversational subject; assistant words never replace signed facts.

The model still accepts no monetary proposal fields, holds no credentials/accounts/SWIFT/grants or raw personal records, and never decides execution. All monetary/date output references are server-filled placeholders. Unknown information no longer defaults to invoice totals. Completeness hints may identify available figures for a direct factual question, but do not filter the reference or constrain answers to a recognized topic.

## Checks

- 218 pytest tests, Ruff clean; public OpenAPI regenerated with unchanged schemas.
- 74/74 scripted conversations; final complete hosted run 74/74, gpt-6.1-sol, all source openai. No fallback is counted as a hosted pass. Independent focused runs: five new continuity sequences and five earlier regressions, each 5/5. They are not combined into the full result.
- T01-T20 20/20 against existing real four-node FISCO and native government-list Watchman; independent verification: 20 runs, 151 entries, 36 real anchors/receipts. No chain reset.
- New tests check reference availability for unrelated, factual, policy, payment and denied turns; itemized amounts and deadlines; signature failure; old-v4 policy boundaries; unknown-scripted clarification; and amount-complete schedule narration without requiring a literal plus sign.
- Fresh-parent multi-turn evals vi/en/ko/zh prove stable references and unchanged financial state. The live API check uses an empty v5 synthetic family (no documents, mandates, approvals, payments or refunds); no question created a case, grant or signature requirement.
- Invoice and refund fixture pages were rendered and visually inspected: no clipping; unchanged totals and clear synthetic/MOCK/version labels. This is visual fixture QA, not real invoice/OCR validation.
- Evidence text logs are pinned to LF, including regeneration; a Windows core.autocrlf=true checkout smoke preserved both sampled existing artifact hashes.

## Signed late-payment contract

New seed version semester-2027-v5 signs both equal 4,477,000 KRW instalments with the existing common 15 January 2027 deadline. It does not invent a later second deadline. Fictional HBU-LATE-01-v1 holds university registration clearance for an overdue unpaid instalment pending bursar-confirmed payment or a revised signed fee notice. Only the bursar can extend the deadline. No monetary late fee is specified, and no automatic admission cancellation, refund, bank movement or family safety freeze follows. This is a MOCK university policy, not Korean law or a live academic-portal integration. Existing v4 signatures/consents are not rewritten; they retain their own terms. The private dev ledger was backed up before its explicit v5 reset; the backup is ignored runtime data, not public evidence.

## Reading assessment and retained failures

The new sequences retain the established refund timeline and fee types, then give the second-instalment amount, known deadline, registration-clearance consequence and only the genuinely unknown late fee. Explicitly switching back to the bill returns its full total/home estimate, rather than trapping the thread in refund answers.

The initial complete run is retained as 69/74, not relabelled as a pass. C50/C51 were overly literal schedule-format assertions: correct individual entries with dates lacked a plus sign. The revised assertion still rejects a missing or wrong entry. C57 described cost types but omitted the per-line figures expected by that existing financial eval; optional completeness hints now expose those expectations without hiding any facts. C60 omitted the original-payer restriction and C61 lost the father-specific register; first-explanation and general payer-address guidance were corrected. One intermediate full run was interrupted while completing the public bill projection; it is not counted. The final full run is separate, complete and unstitched.

Style remains imperfect: the Vietnamese late-payment explanation can sound bureaucratic (registration clearance/revised signed notice), and exact dates are sometimes repeated where a shorter relative timeline would read better. Scripted prose is shorter in those turns. This is bounded engineering reading review, not native-speaker approval or proof of semantic correctness for every utterance. The model can still phrase a fact poorly; the bank boundary does not depend on its prose.

Final full-run continuity transcripts (unaltered):

### C70 (vi)

User: con gái tôi sắp đi du học hàn, nếu đóng tiền rồi mà bị trượt visa thì sao, có lấy lại được ko

Assistant: Có thể được hoàn nếu con gái bạn nộp hồ sơ xin hoàn do trượt visa trước ngày bắt đầu học 02/03/2027: hoàn toàn bộ học phí đã đóng, tiền ký túc xá chưa sử dụng và bảo hiểm chưa kích hoạt; thời hạn hoàn là 16/03/2027, tính từ ngày bắt đầu học chứ không phải ngày nộp yêu cầu. Tiền chỉ được trả về đúng tài khoản gốc của bạn đã dùng để thanh toán; gia đình chịu phí ngân hàng chuyển đi, phí ngân hàng trung gian và chênh lệch chuyển đổi ngoại tệ nên không bảo đảm nhận lại đủ số tiền ban đầu.

User: bao lâu thì tiền về, mất phí gì ko

Assistant: Nếu con gái bạn nộp hồ sơ trước ngày bắt đầu học 02/03/2027, trường cam kết hoàn trong vòng hai tuần kể từ ngày bắt đầu học, tức chậm nhất 16/03/2027, không tính từ ngày nộp yêu cầu. Gia đình chịu phí ngân hàng chuyển đi ban đầu, phí chuyển tiền quốc tế qua ngân hàng trung gian và hao hụt đổi từ KRW qua USD sang tiền trong nước; hóa đơn này không thu phí nhập học, nhưng không bảo đảm nhận lại đủ số tiền đã chuyển.

User: lỡ chậm đóng đợt 2 thì sao?

Assistant: Đợt hai là 4.477.000 KRW, hạn 15/01/2027—cùng hạn với đợt đầu, không phải một mốc muộn hơn. Nếu quá hạn chưa đóng, trường sẽ tạm giữ xác nhận hoàn tất đăng ký học cho đến khi bộ phận tài vụ xác nhận thanh toán hoặc cấp thông báo học phí có ký sửa đổi; việc này không tự động hủy nhập học. Điều khoản hiện tại không quy định khoản phạt bằng tiền; nếu cần gia hạn, bạn cần liên hệ bộ phận tài vụ của trường vì chỉ trường mới có thể chấp thuận bằng thông báo sửa đổi.

### C71 (en)

User: If my daughter's visa is denied after I pay, can we recover the money?

Assistant: If your daughter files before classes start on 02 Mar 2027, a visa-refusal refund covers paid tuition, unused dormitory and unactivated insurance, with payment promised by 16 Mar 2027. It can return only to your original payer account; your family bears the outgoing bank fee, intermediary wire fees and currency-conversion losses, so a net refund is not guaranteed. If she files after classes start, the degree office must assess the claim.

User: And when would it arrive, what costs do we lose?

Assistant: If your daughter files before classes start, the promised refund deadline is 16 Mar 2027, measured from classes starting on 02 Mar 2027, not from her request. Your family bears the original outgoing bank fee, intermediary wire fees and currency-conversion losses; no admission fee was charged on this bill, but the net amount you receive is not guaranteed.

User: What happens if the second instalment is late?

Assistant: The second instalment of 4,477,000 KRW is due on 15 Jan 2027, the same deadline as the first. If it remains unpaid after that date, your daughter’s registration clearance will be put on hold until the bursar confirms payment or issues a revised signed fee notice; it does not automatically cancel her admission. Only the university bursar can approve an extension, and the signed terms do not specify a monetary late fee.

### C72 (ko)

User: 딸의 비자가 거절되면 이미 낸 돈은 환불되나요?

Assistant: 네, 비자 거절로 2027년 3월 2일 개강 전에 따님이 입학 철회와 환불을 신청하면 납부한 수업료 전액과 미사용 기숙사비·미개시 보험료가 환불 대상이며, 환불 약정 기한은 신청일이 아닌 개강일 기준 2027년 3월 16일까지입니다. 환불금은 원래 납부자인 보호자님의 기존 납부 계좌로만 반환되며, 이 청구서에는 별도 입학금이 없지만 최초 송금 수수료·중개은행 수수료·환전 손실은 가족 부담이므로 실제 수령액 전액은 보장되지 않습니다.

User: 그럼 언제 들어오고 어떤 비용이 빠지나요?

Assistant: 따님이 2027년 3월 2일 개강 전에 입학 철회와 환불을 신청하면, 환불 약정 기한은 신청일이 아니라 개강일을 기준으로 2027년 3월 16일까지입니다. 이 청구서에는 별도 입학금이 없어 입학금 공제는 없지만, 최초 송금 수수료·중개은행 국제송금 수수료·환전 손실은 가족 부담이므로 실제 수령액은 달라질 수 있습니다.

User: 두 번째 분할 납부가 늦으면 어떻게 되나요?

Assistant: 두 번째 분할금 4,477,000 KRW도 첫 번째와 같은 2027년 1월 15일까지 납부해야 하며, 미납 시 대학 재무처가 납부를 확인하거나 수정된 서명 고지서를 발급할 때까지 학적 등록 승인이 보류됩니다. 자동으로 입학이 취소되지는 않으며, 금전적 연체료는 서명된 조건에 명시되어 있지 않습니다. 기한 연장이 필요하시면 대학 재무처에 요청하셔야 하며, 연장은 수정된 서명 고지서로만 승인됩니다.

### C73 (zh)

User: 如果女儿签证被拒，已经交的钱能退吗？

Assistant: 可以:如果女儿签证被拒,在开课日 2027年3月2日 前提交退费申请,已付学费可全额退还,未使用的宿舍费和未生效的保险费也可退,按政策应于 2027年3月16日 前退款;期限从开课日算起,而非申请日。退款只能退回您原付款账户,原汇出银行费、中转行电汇费及汇兑损失由家庭承担,因此不保证全额净到账。

User: 那多久能到账，会扣哪些费用？

Assistant: 若女儿在 2027年3月2日 开课前提交退费申请,按政策应于 2027年3月16日 前退款,期限从开课日算起,而非申请日。费用方面,这份账单没有单独收取不可退的入学费;但原汇出银行费、中转行国际电汇费,以及韩元经美元兑换为本币的汇兑损失由您家承担,因此不能保证全额净到账。

User: 如果第二期缴费逾期会怎样？

Assistant: 第二期为 4,477,000 KRW,须于 2027年1月15日 前缴清,并没有更晚的第二期截止日。逾期未缴会暂停注册放行,直到校方财务处确认付款或签发修订后的缴费通知;不会自动取消录取或退款。已签条款未规定金钱滞纳金,是否另收费需向校方财务处确认;如需延期,也只有校方财务处能通过修订后的正式缴费通知批准。

### C74 (vi)

User: con gái tôi sắp đi du học hàn, nếu đóng tiền rồi mà bị trượt visa thì sao, có lấy lại được ko

Assistant: Có thể được hoàn nếu con gái bạn nộp hồ sơ xin hoàn do trượt visa trước ngày bắt đầu học 02/03/2027: hoàn toàn bộ học phí đã đóng, tiền ký túc xá chưa sử dụng và bảo hiểm chưa kích hoạt; con gái bạn cần làm thủ tục rút nhập học và đăng ký lại nếu muốn học sau này. Theo chính sách, tiền hoàn được chuyển về đúng tài khoản gốc mà bạn đã dùng để thanh toán chậm nhất 16/03/2027, tính từ ngày bắt đầu học chứ không phải ngày nộp yêu cầu; gia đình chịu phí ngân hàng ban đầu, phí chuyển tiền trung gian và chênh lệch tỷ giá nên số thực nhận có thể thấp hơn số đã đóng.

User: bao lâu thì tiền về, mất phí gì ko

Assistant: Nếu con gái bạn nộp hồ sơ trước ngày bắt đầu học, hạn chuyển hoàn là 16/03/2027, tính từ ngày bắt đầu học 02/03/2027, không phải ngày nộp yêu cầu. Gia đình chịu phí ngân hàng của lần chuyển tiền ban đầu, phí chuyển tiền quốc tế qua ngân hàng trung gian và hao hụt quy đổi KRW sang USD rồi sang tiền trong nước, nên số thực nhận có thể thấp hơn số đã đóng.

User: vậy tổng tiền học là bao nhiêu?

Assistant: Tổng hóa đơn cả học kỳ là 8.954.000 KRW, gồm học phí, ký túc xá và bảo hiểm; ước tính tương đương 169.318.450 VND theo tỷ giá mô phỏng (MOCK), không phải tỷ giá thị trường trực tiếp.
