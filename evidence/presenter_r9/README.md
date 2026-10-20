# Presenter round 9: current verification

- **229 pytest tests**, Ruff clean; **78/78 full scripted conversations**; **T01-T20 20/20** against real FISCO and native government-list Watchman.
- Independent T01-T20 verifier: **20 runs, 156 entries, 36 anchors**, on-chain receipts/roots checked. No chain reset.
- Extra delayed-refund case: **37 audit entries / 5 real anchors**, student-signed MOCK chaser, manual complaint index, unchanged bank balance. This is separate from T01-T20. [Raw recovery trace](real_chain_recovery.json), [letter](letter.pdf), [complaint index](complaint.pdf).
- [Direct live API read check](live_read_check.json): API 8000, v7 seed, 12 Jan simulated today, tuition 7,174,000 KRW, signed Korean-time windows, external dorm/NHIS obligations, rent setup. No extra hosted calls in this check. The private synthetic ledger was backed up before explicit reset; no public stack deployment occurred.
- Invoice/refund/rental fixtures and the actual chaser/complaint PDFs were rendered and visually checked. API PDF routes advertise application/pdf. No dependencies or secrets changed.

## What was corrected

The earlier payable bundle mixed collectors and refund rules. The signed v7 invoice contains tuition only; the separate-obligation projection identifies collector/timing and explicitly excludes dorm/NHIS from this transfer and claim. The dorm office's unused-fee rule is unknown. The 70k monthly NHIS figure is a MOCK budget, not a tariff. Old signed seeds are never rewritten and cannot create a new bundled transfer.

The payment window is signed and checked both in preparation and at the bank. Today is explicit, with Korea-time 09:00 opening / 17:00 closing. The admission offer is not the standard visa certificate; the simulated bursar issues that only after matched registration payment. No embassy submission is made.

[Rent diagnosis](rent_diagnosis.json) found missing mandates, not a failed wire. The API supplies purpose-specific setup, checks the canonical MOCK lease against bank-held data, keeps Hao's pending request and resumes it once the parent signs. This is not production lease authentication.

A missed promise now creates a dated chaser with a student consent hash, recipient and signed/evidence references. Only a MOCK outbox entry is recorded; a further seven simulated days can prepare the manual external-route pack. It contains a redacted cover/index, not exported raw identity/bank files. Portal eligibility, external submission and recovery remain outside the demo.

## Focused hosted reading review and quota

**No full hosted run.** Initial three changed cases: **2/3**; C78 was factually useful but omitted the official complaint route. The route became a structured reference fact and the prompt asks for it on non-payment questions. The refusal reply also now separates signing before classes from the later refund promise. Only C76/C78 were rechecked: **2/2**, every reply source openai. C77's initial Chinese rent handoff passed. These five executions are not combined into a claimed full-suite pass.

Vietnamese is short and understandable, names Linh as signer and ba as recipient; the parent answer uses anh. The rent answer in Chinese naturally asks for the lease and Dad's monthly authorization. The final non-payment answer names e-People/MOE and keeps submission manual. Some terms remain formal (withdrawal request, no-guarantee wording); this is engineering review, not native-speaker sign-off. Scripted replies are shorter, and the hosted model initially did worse on the missing-route case; both facts are retained here.

**Initial C76:** Linh cần ký đơn rút nhập học và đề nghị hoàn học phí; theo cam kết, trường sẽ hoàn trước hoặc vào 16/03/2027. Số tiền thực nhận ước tính MOCK là 132.551.177 VND, chỉ về tài khoản gốc của ba; đây chưa phải khoản đã nhận và không được bảo đảm.

**Initial C77:** Hao,请先上传租赁合同,并由爸爸签署每月房租付款授权;材料齐全后,才能继续核对房东并办理付款。

**Initial C78:** Nếu trường chưa hoàn học phí đúng hạn cam kết 16/03/2027, BursarBridge sẽ soạn thư nhắc để sinh viên duyệt trước khi gửi mô phỏng; nếu vẫn chưa nhận được tiền sau 7 ngày, bước tiếp theo là chuẩn bị bộ hồ sơ khiếu nại đã che thông tin nhạy cảm để nộp thủ công. Việc nhắc và khiếu nại không bảo đảm thu hồi được tiền cho anh.

**Recheck C76:** Linh cần ký đơn rút nhập học và đề nghị hoàn học phí trước ngày 02/03/2027. Theo chính sách, trường cam kết hoàn học phí đã đóng chậm nhất ngày 16/03/2027 về tài khoản gốc của ba. Số tiền về dự kiến theo mô phỏng là 132.551.177 VND sau phí ngân hàng và chênh lệch tỷ giá, chưa phải số tiền được bảo đảm.

**Recheck C78:** Nếu trường quá hạn hoàn học phí đã cam kết vào 16/03/2027, bước tiếp theo là sinh viên duyệt thư nhắc hoàn tiền mô phỏng để gửi trường. Nếu sau 7 ngày kể từ thư nhắc vẫn chưa nhận được tiền, BursarBridge sẽ chuẩn bị bộ hồ sơ khiếu nại đã che thông tin nhạy cảm để nộp thủ công qua Korea e-People / Bộ Giáo dục; không tự động nộp hay bảo đảm thu hồi tiền cho anh.

Official context: [MOE petition service](https://www.moe.go.kr/sub/infoRenew.do?m=010201), [e-People multilingual route](https://www.epeople.go.kr/petition/htp/htp.npaid), [NHIS foreigner guidance](https://www.nhis.or.kr/english/wbheaa02900m01.do). These do not establish Hanbit's fictional refund policy or the MOCK insurance budget.
