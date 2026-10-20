# Refund projection and semester schedule follow-up

- 220 tests; 75/75 scripted conversations. Full hosted run: 71/75; C72-C75 fell back and are failures, not hosted passes. An independent focused C28/C75 run passed 2/2 with all sources openai; these runs are not combined. The next batch was stopped after repeated HTTP 429. A bounded probe returned HTTP 429 with Retry-After: 6299 seconds (about 105 minutes), so no further calls were made before that deadline.
- T01-T20: 20/20, real FISCO and native government-list Watchman. Independent verification: 20 runs, 151 entries, 36 on-chain anchors/receipts. No chain reset.
- The API owns the pre-receipt MOCK estimate, and receipt removes it in favour of the bank reconciliation. List/detail/cards/events share current original-account presentation. Tests cover matching estimated/received costs and net return, updated balance, manual/legacy estimate absence, original-case reuse and tranche-specific due dates.
- v6: 4,477,000 KRW due 15 January, then 4,477,000 KRW due 15 February 2027. Full remaining-balance approvals use the earliest unpaid signed deadline. Historical v5 signatures remain untouched.
- Live hosted parent thread: v6, stable reference and unchanged financial state, prompt progress before model completion. This is local HTTP, not a browser/tunnel load test.

## Hosted reading review

Minh is addressed as anh, without bạn. The two differently worded filed-refund questions answer the existing claim, its deadline and deductions rather than showing invoice quote/pack cards. The net return is an estimate until receipt. Vietnamese is understandable and consistent; filed-cost replies remain dense and echo the card cost lines, and the late-registration explanation still sounds more bureaucratic than everyday family speech. This is engineering review, not native-speaker sign-off. The successful hosted samples showed no asserted language regression versus scripted. Full hosted green is blocked by the local proxy rate limit, not waived or claimed; this is not exhaustive language QA.

**Minh:** khi nào tiền học phí của con về, bị trừ bao nhiêu?

**Assistant:** Hồ sơ hoàn tiền đã được gửi; theo chính sách, tiền sẽ được hoàn chậm nhất 16/03/2027, tính từ ngày bắt đầu học, về đúng tài khoản gốc anh đã dùng để thanh toán. Hiện chưa nhận được tiền: ước tính MOCK số tiền về là 165.532.581 VND, với phí ngân hàng ban đầu 25.000 VND, phí chuyển tiền quốc tế/trung gian 375.000 VND, hao hụt tỷ giá 3.385.869 VND và khoản trường giữ lại 0 VND; hóa đơn không thu phí nhập học, các chi phí ngân hàng và tỷ giá do gia đình chịu nên số thực nhận chưa được bảo đảm.

**Minh:** tiền hoàn khi nào về, bị trừ bao nhiêu?

**Assistant:** Hồ sơ đang được yêu cầu hoàn và chưa nhận được tiền; theo chính sách, hạn hoàn là 16/03/2027, tính từ ngày bắt đầu học, về đúng tài khoản gốc anh đã dùng để thanh toán. Ước tính MOCK số tiền về là 165.532.581 VND, sau phí ngân hàng ban đầu 25.000 VND, phí chuyển quốc tế/trung gian 375.000 VND và hao hụt tỷ giá 3.385.869 VND do gia đình chịu; trường giữ lại 0 VND, hóa đơn không thu phí nhập học, và số thực nhận chưa được bảo đảm.

The active refund reference contains status and display placeholders, never an account, balance, SWIFT, credential, consent token or model-supplied payment parameter. Money authority is unchanged. See [tests](../../services/api/tests/test_refund_contract.py), [projection](../../services/api/bursarbridge/engine.py), [raw hosted report](hosted_75.json), [live HTTP check](live_http.json).
