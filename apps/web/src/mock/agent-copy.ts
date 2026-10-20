/**
 * Copy for the scripted (mock) agent. Mirrors what the backend's `scripted` provider does:
 * the agent replies in the language the user wrote in. Written natively per language,
 * not translated word for word. Vietnamese addresses the parent as "anh" and the student as "bạn".
 */
import type { Locale } from "@/lib/api/types";

type Dict = Record<Locale, string>;
type Params = Record<string, string | number>;

const C = {
  // ---- steps ----
  "step.read_doc": {
    en: "Reading {file}",
    vi: "Đang đọc {file}",
    ko: "{file} 읽는 중",
    zh: "正在读取 {file}",
  },
  "step.reading_fee": {
    en: "Reading the university’s fee record…",
    vi: "Mình đang đọc hồ sơ học phí của trường…",
    ko: "대학 등록금 기록을 읽는 중…",
    zh: "正在读取学校的缴费记录…",
  },
  "step.bank_pack": {
    en: "Checking the bank paperwork…",
    vi: "Đang kiểm tra hồ sơ gửi ngân hàng…",
    ko: "은행 제출 서류 확인 중…",
    zh: "正在核对银行材料…",
  },
  "step.signature": {
    en: "Checking the university's signature on the invoice",
    vi: "Kiểm tra chữ ký số của trường trên hoá đơn",
    ko: "청구서의 대학 전자서명 확인",
    zh: "核验发票上的学校数字签名",
  },
  "step.credential": {
    en: "Verifying Hanbit's payee credential",
    vi: "Xác minh chứng nhận người nhận do Hanbit cấp",
    ko: "한빛대학교 수취인 인증서 검증",
    zh: "验证韩光大学签发的收款方凭证",
  },
  "step.registry": {
    en: "Checking credential status on the evidence chain",
    vi: "Kiểm tra trạng thái chứng nhận trên chuỗi bằng chứng",
    ko: "증거 체인에서 인증서 상태 확인",
    zh: "在存证链上查询凭证状态",
  },
  "step.account": {
    en: "Matching account and name with Lotus Home Bank",
    vi: "Đối chiếu số tài khoản và tên với Lotus Home Bank",
    ko: "Lotus Home Bank에서 계좌·예금주 대조",
    zh: "与莲花银行核对账号和户名",
  },
  "step.rules": {
    en: "Applying {corridor} rules (Circular 20/2022)",
    vi: "Áp dụng quy định {corridor} (Thông tư 20/2022)",
    ko: "{corridor} 송금 규정 적용 (베트남 통지 20/2022)",
    zh: "适用 {corridor} 汇款规则（越南第20/2022号通知）",
  },
  "step.quote": {
    en: "Getting a live quote",
    vi: "Lấy tỷ giá hiện tại",
    ko: "실시간 환율 견적 받기",
    zh: "获取实时报价",
  },
  "step.pack": {
    en: "Preparing the bank paperwork pack",
    vi: "Chuẩn bị bộ hồ sơ chuyển tiền cho ngân hàng",
    ko: "은행 제출 서류 묶음 준비",
    zh: "准备银行汇款材料包",
  },
  "step.policy": {
    en: "Asking the policy engine",
    vi: "Hỏi bộ quy tắc an toàn",
    ko: "정책 엔진에 판단 요청",
    zh: "提交策略引擎裁决",
  },
  "step.extract_email": {
    en: "Extracting payment details from the email",
    vi: "Tách thông tin thanh toán trong email",
    ko: "이메일에서 결제 정보 추출",
    zh: "从邮件中提取付款信息",
  },
  "step.compare": {
    en: "Comparing with the account Hanbit vouched for",
    vi: "So với tài khoản mà Hanbit đã xác nhận",
    ko: "한빛대학교가 보증한 계좌와 비교",
    zh: "与韩光大学认证的账户比对",
  },
  "step.letter": {
    en: "Checking the decision letter matches Linh",
    vi: "Kiểm tra thư quyết định đúng là của Linh",
    ko: "결정 통지서가 Linh 본인 것인지 확인",
    zh: "核对拒签信与 Linh 身份一致",
  },
  "step.find_payment": {
    en: "Finding the tuition payment to recover",
    vi: "Tìm khoản học phí cần lấy lại",
    ko: "환불받을 등록금 결제 찾기",
    zh: "查找需要退回的学费付款",
  },
  "step.refund_policy": {
    en: "Reading Hanbit's refund terms (HBU-REF-01-v2)",
    vi: "Đọc điều khoản hoàn tiền của Hanbit (HBU-REF-01-v2)",
    ko: "한빛대 환불 약관 확인 (HBU-REF-01-v2)",
    zh: "查阅韩光大学退款条款（HBU-REF-01-v2）",
  },
  "step.draft_claim": {
    en: "Preparing the withdrawal and refund forms",
    vi: "Soạn đơn hủy nhập học và đơn xin hoàn tiền",
    ko: "입학 취소서와 환불 신청서 준비",
    zh: "准备撤销入学申请和退款申请",
  },
  "step.redirect": {
    en: "Checking where the refund would go",
    vi: "Kiểm tra tiền hoàn sẽ về đâu",
    ko: "환불금이 어디로 가는지 확인",
    zh: "核对退款去向",
  },
  "step.lookup": {
    en: "Looking up the invoice and today's rate",
    vi: "Tra hoá đơn và tỷ giá hôm nay",
    ko: "청구서와 오늘 환율 조회",
    zh: "查询发票和今日汇率",
  },
  "step.status": {
    en: "Checking the bank and the bursar",
    vi: "Kiểm tra với ngân hàng và phòng tài vụ của trường",
    ko: "은행과 대학 재무처 상태 확인",
    zh: "向银行和学校财务处查询",
  },
  "step.quota": {
    en: "Checking the annual FX quota (USD 50k per person)",
    vi: "Kiểm tra hạn mức ngoại tệ năm",
    ko: "연간 외화 한도 확인 (1인 5만 달러)",
    zh: "核对年度购汇额度（每人5万美元）",
  },

  // ---- replies ----
  "reply.intro": {
    en: "Hi {name}. I handle tuition payments to {uni} for your family, and I only ever pay accounts the university has vouched for. Forward me the invoice when it arrives, or ask me anything about the money.",
    vi: "Chào {name}. Mình lo việc đóng học phí cho trường {uni} giúp cả nhà, và chỉ chuyển tiền tới tài khoản đã được chính trường xác nhận. Khi có hoá đơn, bạn chuyển tiếp cho mình là được, hoặc hỏi mình bất cứ điều gì về khoản tiền nhé.",
    ko: "안녕하세요, {name}님. 가족을 대신해 {uni} 등록금 납부를 맡고 있어요. 대학이 직접 보증한 계좌로만 송금해요. 청구서가 오면 저에게 전달해 주시거나, 돈에 관해 궁금한 걸 물어보세요.",
    zh: "{name}你好。我负责帮你们家向{uni}缴学费，而且只会付款到学校亲自认证过的账户。收到发票后转给我就行，关于这笔钱有任何问题也可以问我。",
  },
  "reply.ask_invoice": {
    en: "Got it, the Spring 2027 tuition. I won't guess the amount: could you forward the invoice from Hanbit (the PDF or the bursar's email)? I'll take it from there and send your dad one card to approve.",
    vi: "Ok, học phí kỳ Xuân 2027 nhé. Mình không đoán số tiền đâu: bạn chuyển tiếp giúp mình hoá đơn của trường Hanbit (file PDF hoặc email của phòng tài vụ) nha. Phần còn lại mình lo, ba bạn chỉ cần duyệt một lần.",
    ko: "네, 2027년 봄학기 등록금이요. 금액은 추측하지 않을게요. 한빛대학교 청구서(PDF나 재무처 이메일)를 전달해 주시겠어요? 나머지는 제가 처리하고, 아버님께는 승인 카드 한 장만 보낼게요.",
    zh: "好的，是2027年春季学期的学费。金额我不会猜：请把韩光大学的发票（PDF或财务处邮件）转给我。剩下的交给我，你爸爸只需要确认一次。",
  },
  "reply.invoice_ok": {
    en: "The invoice is genuine: it's signed by Hanbit University and the account belongs to their Office of the Bursar. {receive} lands at Hanbit; your dad's account pays {send} including all fees, which is {cost} above the mid-market rate.",
    vi: "Hoá đơn là thật: có chữ ký số của trường Hanbit và tài khoản đúng là của Phòng Tài vụ trường. Trường nhận đủ {receive}; tài khoản của ba bạn trả {send} đã gồm mọi phí, chỉ cao hơn tỷ giá thị trường {cost}.",
    ko: "진짜 청구서예요. 한빛대학교가 서명했고, 계좌도 대학 재무처 명의가 맞아요. 대학은 {receive}을 받고, 아버님 계좌에서는 모든 수수료 포함 {send}이 나가요. 시장 중간 환율 대비 추가 비용은 {cost}예요.",
    zh: "这张发票是真的：有韩光大学的数字签名，收款账户也确实属于学校财务处。学校将收到 {receive}，你爸爸账户共支付 {send}（含全部费用），比市场中间价多 {cost}。",
  },
  "reply.approval_sent": {
    en: "This is the first payment to Hanbit, so it needs your dad's own approval. I've sent him one card with everything on it. You don't need to do anything else.",
    vi: "Đây là lần đầu chuyển cho trường Hanbit nên cần chính ba bạn duyệt. Mình đã gửi ba một thẻ duyệt có đủ mọi thông tin. Bạn không cần làm gì thêm đâu.",
    ko: "한빛대학교로 보내는 첫 송금이라 아버님이 직접 승인하셔야 해요. 필요한 정보를 모두 담은 승인 카드를 보내드렸어요. Linh님은 더 하실 일이 없어요.",
    zh: "这是第一次向韩光大学付款，所以需要你爸爸本人确认。我已经把包含全部信息的确认卡发给他了，你这边不用再做什么。",
  },
  "reply.mandate_missing": {
    en: "Everything checks out, but your dad hasn't set a tuition limit yet, so I can't ask him to pay. I've asked him to set it (it takes a minute). As soon as he does, his approval card goes out automatically.",
    vi: "Mọi thứ đều hợp lệ, nhưng ba bạn chưa đặt giới hạn đóng học phí nên mình chưa thể gửi yêu cầu thanh toán. Mình đã nhắn ba đặt giới hạn (mất khoảng một phút). Ba đặt xong là thẻ duyệt sẽ tự gửi đến ba.",
    ko: "모두 확인됐지만 아버님이 아직 등록금 한도를 설정하지 않으셔서 결제 요청을 보낼 수 없어요. 한도 설정을 부탁드렸어요(1분이면 돼요). 설정하시는 즉시 승인 카드가 자동으로 전달돼요.",
    zh: "一切核验通过，但你爸爸还没有设置学费授权额度，所以暂时不能发起付款请求。我已提醒他设置（大约一分钟）。他设置好后，确认卡会自动发给他。",
  },
  "reply.already_pending": {
    en: "Your dad already has this payment waiting for his approval. I'll tell you the moment he signs.",
    vi: "Ba bạn đã có thẻ duyệt khoản này rồi, đang chờ ba ký. Ba ký xong mình báo bạn ngay.",
    ko: "이 결제는 이미 아버님 승인 대기 중이에요. 서명하시면 바로 알려드릴게요.",
    zh: "这笔付款已经在等你爸爸确认了。他一签名我就告诉你。",
  },
  "reply.already_paid": {
    en: "Hanbit has received {receive} in tuition. This tuition bill is paid.",
    vi: "Hanbit đã nhận học phí {receive}. Hóa đơn học phí này đã được thanh toán rồi nhé.",
    ko: "한빛대학교가 등록금 {receive}을 받았어요. 이 등록금 고지서는 납부 완료됐어요.",
    zh: "韩光大学已收到 {receive} 学费，这张学费账单已付清。",
  },
  "reply.blocked_discount": {
    en: "I stopped this. The email offers a 15% discount if you pay a different account by Friday, but Hanbit has never vouched for that account and the sender isn't the university. This is a known scam pattern. Nothing was sent, and your real invoice is untouched.",
    vi: "Mình đã chặn yêu cầu này. Email hứa giảm 15% nếu chuyển vào một tài khoản khác trước thứ Sáu, nhưng trường Hanbit chưa bao giờ xác nhận tài khoản đó, và người gửi cũng không phải trường. Đây là chiêu lừa đảo quen thuộc. Không có đồng nào bị chuyển, hoá đơn thật vẫn giữ nguyên.",
    ko: "이 요청은 막았어요. 금요일까지 다른 계좌로 내면 15% 할인해 준다는 메일인데, 한빛대학교가 그 계좌를 보증한 적이 없고 발신자도 대학이 아니에요. 전형적인 사기 수법이에요. 돈은 한 푼도 나가지 않았고, 진짜 청구서는 그대로예요.",
    zh: "我拦下了这个请求。邮件说周五前汇到另一个账户就能打八五折，但韩光大学从未认证过那个账户，发件人也不是学校。这是常见的诈骗手法。没有任何钱被转出，真实发票不受影响。",
  },
  "reply.refusal": {
    en: "I'm so sorry about the visa, Linh. Sign the two forms below, cancel admission and the refund request, and Hanbit returns the tuition by {promise} (two weeks after classes start on {start}), only to your dad's account. Dorm and health insurance were never paid through us.",
    vi: "Tiếc quá Linh ơi. Bạn ký hai đơn bên dưới (hủy nhập học và xin hoàn tiền), trường hoàn học phí chậm nhất {promise} (hai tuần sau khai giảng {start}), chỉ về tài khoản của ba. Ký túc xá và bảo hiểm không đóng qua mình nên không nằm trong khoản này.",
    ko: "비자 소식은 정말 유감이에요, Linh님. 아래 두 서류(입학 취소서, 환불 신청서)에 서명하면 한빛대가 {promise}까지(개강일 {start} 후 2주) 등록금을 아버님 계좌로만 돌려줘요. 기숙사비와 보험료는 저희를 통해 내지 않았어요.",
    zh: "签证的事很遗憾，Linh。签好下面两份表（撤销入学和退款申请），学校会在 {promise} 前（{start} 开学后两周）把学费只退回你爸爸的账户。宿舍费和保险没有通过我们支付。",
  },
  "reply.needs": {
    en: "I’ll prepare the {amount} tuition as soon as the steps above are done. Nothing has moved.",
    vi: "Mình sẽ chuẩn bị khoản học phí {amount} ngay khi xong các bước ở trên. Chưa có tiền nào được chuyển.",
    ko: "위 단계가 끝나는 대로 {amount} 등록금을 준비할게요. 아직 아무 돈도 움직이지 않았어요.",
    zh: "上面几步完成后，我马上准备 {amount} 的学费。目前没有任何资金转出。",
  },
  "reply.rent_needs_lease": {
    en: "Before I can pay rent, two things: upload the rental agreement (the bank checks it against its own record), and your parent sets the monthly rent limit. Nothing has moved.",
    vi: "Trước khi trả tiền nhà cần hai việc: bạn tải lên hợp đồng thuê (ngân hàng đối chiếu với hồ sơ của họ), và ba mẹ đặt hạn mức tiền nhà hằng tháng. Chưa có tiền nào di chuyển.",
    ko: "월세를 내기 전에 두 가지가 필요해요. 임대차 계약서를 올리고(은행이 자체 기록과 대조해요), 부모님이 월세 한도를 정해야 해요. 아직 아무 돈도 움직이지 않았어요.",
    zh: "付房租之前需要两件事：你上传租房合同（银行会与自己的记录核对），以及父母设置每月房租额度。目前没有任何资金变动。",
  },
  "reply.rent_paid": {
    en: "The bank is holding this month’s {amount} rent for {payee}, within Dad’s signed limit. Dad can see it in his app and cancel for 30 minutes.",
    vi: "Ngân hàng đang giữ khoản tiền nhà {amount} cho {payee}, đúng hạn mức ba đã ký. Ba có thể xem trong ứng dụng và hủy trong 30 phút.",
    ko: "은행이 {payee}에게 보낼 이번 달 월세 {amount}을 보류하고 있어요. 아버님이 서명한 한도 안이며, 앱에서 확인하고 30분 안에 취소할 수 있어요.",
    zh: "银行正在暂扣本月付给 {payee} 的房租 {amount}，在爸爸签署的额度内。爸爸可以在应用里查看，并在30分钟内取消。",
  },
  "reply.rent_done": {
    en: "There is already a rent request for this month. Check its payment card for the latest update.",
    vi: "Đã có yêu cầu tiền nhà tháng này rồi. Con xem thẻ thanh toán để biết khoản đó đến đâu nhé.",
    ko: "이번 달 월세 요청이 이미 있어요. 결제 카드에서 진행 상황을 확인해 주세요.",
    zh: "本月已经有一笔房租请求。请查看付款卡片了解最新进度。",
  },
  "reply.rent_needs": {
    en: "Your dad hasn’t set a rent limit yet, so I can’t pay rent. I’ve asked him to set it for Seoul Garden Residence.",
    vi: "Ba bạn chưa đặt hạn mức tiền nhà nên mình chưa trả được. Mình đã nhờ ba đặt hạn mức cho Seoul Garden Residence.",
    ko: "아버님이 아직 월세 한도를 정하지 않으셔서 월세를 낼 수 없어요. Seoul Garden Residence 한도를 정해 달라고 요청했어요.",
    zh: "你爸爸还没有设置房租额度，所以暂时不能付房租。我已提醒他为 Seoul Garden Residence 设置额度。",
  },
  "reply.refusal_after_start": {
    en: "Classes have already started, so Hanbit's degree office has to assess this case by hand. There's no automatic amount or date, and I won't guess one. The money can still only go back to your dad's account.",
    vi: "Trường đã khai giảng nên phòng đào tạo của Hanbit phải xem xét trường hợp này thủ công. Chưa có số tiền hay ngày hoàn tự động, và mình sẽ không đoán. Tiền vẫn chỉ về lại tài khoản của ba.",
    ko: "이미 개강해서 한빛대 학사팀이 직접 검토해야 해요. 자동으로 정해지는 금액이나 날짜가 없고, 제가 추측하지도 않을게요. 환불금은 여전히 아버님 계좌로만 돌아가요.",
    zh: "已经开学了，所以需要韩光大学的教务处人工审核。没有自动的金额或日期，我也不会去猜。钱仍然只能退回你爸爸的账户。",
  },
  "reply.refund_parent_wait": {
    en: "Linh needs to sign two forms first: cancelling her admission and the refund request. Only she can do that. Once she signs, Hanbit pays the whole semester back to your account, within two weeks after classes start.",
    vi: "Linh cần ký hai đơn trước: đơn hủy nhập học và đơn xin hoàn tiền. Chỉ Linh ký được. Linh ký xong, trường Hanbit hoàn cả học kỳ về tài khoản của anh, trong vòng hai tuần sau ngày khai giảng.",
    ko: "먼저 Linh님이 입학 취소서와 환불 신청서 두 장에 서명해야 해요. 본인만 할 수 있어요. 서명하면 한빛대가 개강 후 2주 안에 학기 전체 금액을 아버님 계좌로 돌려드려요.",
    zh: "需要 Linh 先签两份表：撤销入学和退款申请，只有她本人能签。她签完后，韩光大学会在开学后两周内把整个学期的费用退回您的账户。",
  },
  "reply.refund_sign_first": {
    en: "Your two forms are ready above. Once you sign, the claim goes to Hanbit and I'll follow it until the money is back in your dad's account.",
    vi: "Hai đơn của bạn đã sẵn ở trên. Bạn ký xong là hồ sơ gửi tới trường, mình theo dõi tới khi tiền về tài khoản của ba.",
    ko: "서류 두 장이 위에 준비돼 있어요. 서명하시면 신청서가 한빛대로 가고, 돈이 아버님 계좌로 돌아올 때까지 제가 챙길게요.",
    zh: "两份表已经在上面准备好了。你签完后申请就会提交给学校，我会一直跟进，直到钱回到你爸爸的账户。",
  },
  "reply.no_payment": {
    en: "There's no tuition payment to recover: nothing has left your dad's account. If the visa was refused, there's nothing to undo on the money side.",
    vi: "Chưa có khoản học phí nào cần lấy lại: tiền vẫn chưa rời tài khoản của ba bạn. Nếu visa bị từ chối thì về mặt tiền bạc không có gì phải xử lý.",
    ko: "환불받을 등록금 결제가 없어요. 아버님 계좌에서 아직 돈이 나가지 않았거든요. 비자가 거절됐더라도 돈 문제로 처리할 건 없어요.",
    zh: "目前没有需要退回的学费：钱还没有从你爸爸的账户转出。即使拒签，资金方面也无需处理。",
  },
  "reply.refund_redirect": {
    en: "Blocked, and it always will be. A refund can only go back to the account that paid, which is your dad's at Lotus Home Bank. Nobody can change that, not you, not me, not a 'refund agent'. Real universities never charge a fee to speed up a refund.",
    vi: "Đã chặn, và sẽ luôn chặn. Tiền hoàn chỉ được về đúng tài khoản đã chuyển đi, tức tài khoản của ba bạn tại Lotus Home Bank. Không ai đổi được điều này, kể cả bạn, mình hay một 'dịch vụ hỗ trợ hoàn tiền'. Trường thật không bao giờ thu phí để hoàn tiền nhanh hơn.",
    ko: "차단했고, 앞으로도 항상 차단돼요. 환불금은 송금한 원래 계좌, 즉 Lotus Home Bank의 아버님 계좌로만 돌아갈 수 있어요. Linh님도, 저도, '환불 대행'도 바꿀 수 없어요. 진짜 대학은 환불을 빨리 해 준다며 수수료를 받지 않아요.",
    zh: "已拦截，而且永远会拦截。退款只能退回原付款账户，也就是你爸爸在莲花银行的账户。谁都改不了：你不行，我不行，所谓的“退款代理”更不行。真正的学校从不收取加急退款费用。",
  },
  "reply.police": {
    en: "This is a known scam. Real police, embassies and universities never ask a family to move money into a “safe account” or to keep it secret. Nothing was sent, and that account can never be paid. If you’re worried, call your family directly, then the police on their official number.",
    vi: "Đây là chiêu lừa đảo quen thuộc. Công an, đại sứ quán hay trường học thật không bao giờ bắt gia đình chuyển tiền vào “tài khoản an toàn” hay yêu cầu giữ bí mật. Chưa có đồng nào bị chuyển, và tài khoản đó không bao giờ được nhận tiền. Nếu lo, bạn gọi thẳng cho gia đình, rồi gọi công an qua số chính thức.",
    ko: "잘 알려진 사기 수법이에요. 진짜 경찰·대사관·대학은 가족에게 “안전계좌”로 돈을 옮기거나 비밀로 하라고 하지 않아요. 아무것도 보내지 않았고, 그 계좌로는 절대 송금되지 않아요. 걱정되면 가족에게 직접 전화한 뒤 경찰 공식 번호로 확인하세요.",
    zh: "这是常见的诈骗手法。真正的警察、使馆或学校绝不会要求家人把钱转到“安全账户”，也不会要求保密。什么都没有转出，那个账户也永远不会被付款。如果担心，请先直接联系家人，再拨打警方官方电话核实。",
  },
  "reply.how_much": {
    en: "Hanbit's invoice {ref} is {receive}, due {due}. At today's rate that's about {send} from your dad's account, all fees included.",
    vi: "Hoá đơn {ref} của Hanbit là {receive}, hạn {due}. Theo tỷ giá hôm nay, tài khoản của ba sẽ trả khoảng {send}, đã gồm mọi phí.",
    ko: "한빛대 청구서 {ref}는 {receive}이고, 납부 기한은 {due}예요. 오늘 환율로는 수수료 포함 아버님 계좌에서 약 {send}이 나가요.",
    zh: "韩光大学发票 {ref} 金额为 {receive}，截止日期 {due}。按今日汇率，你爸爸账户约需支付 {send}（含全部费用）。",
  },
  "reply.how_much_parent": {
    en: "Hanbit's invoice {ref} is {receive}, due {due}. At today's rate your account pays about {send}, all fees included.",
    vi: "Hoá đơn {ref} của trường Hanbit là {receive}, hạn {due}. Theo tỷ giá hôm nay, tài khoản của anh trả khoảng {send}, đã gồm mọi phí.",
    ko: "한빛대 청구서 {ref}는 {receive}이고, 납부 기한은 {due}예요. 오늘 환율로는 수수료 포함 약 {send}이 나가요.",
    zh: "韩光大学发票 {ref} 金额为 {receive}，截止日期 {due}。按今日汇率，您的账户约需支付 {send}（含全部费用）。",
  },
  "reply.no_invoice_yet": {
    en: "I don't have Hanbit's invoice yet, so I won't quote a number. Once Linh forwards it, I'll tell you the exact amount and the all-in cost in VND.",
    vi: "Mình chưa có hoá đơn của trường Hanbit nên không đưa con số phỏng đoán. Khi Linh chuyển hoá đơn, mình sẽ báo chính xác số tiền và tổng chi phí bằng VND.",
    ko: "아직 한빛대 청구서를 받지 못해서 추측한 금액은 말씀드리지 않을게요. Linh님이 전달하면 정확한 금액과 원화·동화 총비용을 알려드릴게요.",
    zh: "我还没有收到韩光大学的发票，所以不会报一个猜测的数字。Linh 转来后，我会告诉你们准确金额和以越南盾计的全部费用。",
  },
  "reply.schedule": {
    en: "Hanbit also allows two parts of {part}: the first by {d1}, the second by {d2}.",
    vi: "Trường cũng cho đóng làm hai đợt, mỗi đợt {part}: đợt 1 trước {d1}, đợt 2 trước {d2}.",
    ko: "두 번에 나눠 낼 수도 있어요. 각 {part}, 1차는 {d1}까지, 2차는 {d2}까지예요.",
    zh: "学校也允许分两期缴纳，每期 {part}：第一期 {d1} 前，第二期 {d2} 前。",
  },
  "reply.status_waiting": {
    en: "The payment is waiting for Dad's approval. Nothing has left his account yet.",
    vi: "Khoản tiền đang chờ ba duyệt. Chưa có đồng nào rời tài khoản của ba.",
    ko: "결제가 아버님 승인을 기다리고 있어요. 아직 계좌에서 나간 돈은 없어요.",
    zh: "付款正在等爸爸确认，账户里还没有钱转出。",
  },
  "reply.status_moving": {
    en: "The payment is still on its way. I’ll confirm when Hanbit has received it.",
    vi: "Tiền đang trên đường đến trường. Khi Hanbit xác nhận đã nhận, mình sẽ báo nhé.",
    ko: "송금이 아직 진행 중이에요. 한빛대학교가 받으면 알려드릴게요.",
    zh: "款项仍在途中。韩光大学确认收到后，我会告诉你。",
  },
  "reply.status_refund": {
    en: "The claim is with Hanbit. Classes start {start}; Hanbit pays within two weeks of that, by {deadline}, and only to {account}. What comes back is a little less than what went out: the bank fees and the currency conversion, not a charge by the school.",
    vi: "Hồ sơ đã ở trường Hanbit. Trường khai giảng ngày {start} và hoàn tiền trong vòng hai tuần sau đó, chậm nhất {deadline}, chỉ về tài khoản {account}. Số tiền về sẽ ít hơn một chút so với lúc chuyển đi: đó là phí ngân hàng và chênh lệch đổi tiền, trường không thu phí.",
    ko: "신청서는 한빛대에 있어요. 개강일은 {start}이고, 그로부터 2주 안, 늦어도 {deadline}까지 {account} 계좌로만 환불돼요. 돌아오는 금액은 보낸 금액보다 조금 적어요. 은행 수수료와 환전 차이 때문이고, 학교가 떼는 돈은 없어요.",
    zh: "申请已经在韩光大学。{start}开学，学校在开学后两周内、最晚{deadline}前退款，只退到{account}。退回的钱会比汇出时少一点：那是银行手续费和换汇差价，学校不扣钱。",
  },
  "reply.status_refund_back": {
    en: "It's back: {amount} arrived in {account}. The card shows where every đồng of the difference went.",
    vi: "Tiền đã về: {amount} vào tài khoản {account}. Thẻ bên dưới cho thấy phần chênh lệch đi đâu, từng đồng.",
    ko: "돌아왔어요. {account} 계좌로 {amount}이 들어왔어요. 차액이 어디로 갔는지는 카드에 하나하나 나와 있어요.",
    zh: "钱已经回来了：{amount} 已到账 {account}。差额的每一笔去向都在卡片里。",
  },
  "reply.status_none": {
    en: "Nothing is moving right now. No payments pending, no money in flight.",
    vi: "Hiện không có giao dịch nào. Không có khoản chờ duyệt, không có tiền đang chuyển.",
    ko: "지금 진행 중인 건 없어요. 대기 중인 결제도, 이동 중인 돈도 없어요.",
    zh: "目前没有进行中的交易：没有待确认的付款，也没有在途资金。",
  },
  "reply.crypto": {
    en: "I can't do that. I don't move tuition into crypto, stablecoins or anything 'for yield', and I don't give investment advice. Tuition stays in your family's bank account until it goes to the university. If you want to compare savings options, a licensed adviser at your bank is the right person.",
    vi: "Mình không làm việc này được. Mình không chuyển tiền học phí sang tiền mã hoá, stablecoin hay bất cứ thứ gì 'sinh lời', và cũng không tư vấn đầu tư. Học phí nằm yên trong tài khoản ngân hàng của gia đình cho đến khi chuyển cho trường. Nếu muốn so sánh cách gửi tiết kiệm, bạn nên hỏi chuyên viên được cấp phép của ngân hàng.",
    ko: "그건 할 수 없어요. 등록금을 코인이나 스테이블코인, '수익' 상품으로 옮기지 않고, 투자 조언도 하지 않아요. 등록금은 대학으로 보내기 전까지 가족 은행 계좌에 그대로 있어요. 저축 상품을 비교하고 싶다면 은행의 공인 상담사와 이야기해 보세요.",
    zh: "这个我做不了。我不会把学费转成加密货币、稳定币或任何“理财”产品，也不提供投资建议。学费在付给学校之前会一直留在家里的银行账户。如果想比较储蓄方式，请咨询银行的持牌顾问。",
  },
  "reply.passport": {
    en: "I can't share that. I only ever see the last 4 digits of passports and account numbers, and I never hand out a family member's documents in chat. If you need Dad's passport for a form, ask him directly, and I can tell you exactly which page the form needs.",
    vi: "Mình không chia sẻ được thông tin này. Mình chỉ thấy 4 số cuối của hộ chiếu và số tài khoản, và không bao giờ gửi giấy tờ của người khác trong khung chat. Nếu cần hộ chiếu của ba để điền hồ sơ, bạn hỏi trực tiếp ba nhé; mình có thể chỉ chính xác hồ sơ cần trang nào.",
    ko: "그 정보는 알려드릴 수 없어요. 저는 여권과 계좌번호의 마지막 4자리만 볼 수 있고, 가족의 서류를 채팅으로 넘기지 않아요. 서류 작성에 아버님 여권이 필요하면 직접 여쭤보세요. 어떤 면이 필요한지는 제가 정확히 알려드릴게요.",
    zh: "这个我不能提供。我只能看到护照号和账号的后4位，也不会在聊天里转交家人的证件。如果填表需要爸爸的护照，请直接问他；需要哪一页我可以告诉你。",
  },
  "reply.remember_account": {
    en: "I won't save that as Hanbit's account. Only the university itself can vouch for its accounts, by issuing a signed credential. Nothing typed in chat or written in an email can add a payee, so a scammer can't do it either.",
    vi: "Mình sẽ không lưu tài khoản đó làm tài khoản của trường Hanbit. Chỉ chính trường mới xác nhận được tài khoản của mình, bằng chứng nhận có chữ ký số. Không thứ gì gõ trong chat hay viết trong email có thể thêm người nhận, nên kẻ lừa đảo cũng không làm được.",
    ko: "그 계좌를 한빛대 계좌로 저장하지 않을게요. 대학 계좌는 대학이 서명한 인증서로만 보증할 수 있어요. 채팅이나 이메일에 적힌 내용으로는 수취인을 추가할 수 없어서, 사기범도 할 수 없어요.",
    zh: "我不会把它存为韩光大学的账户。学校账户只能由学校本身通过签名凭证来认证。聊天或邮件里的任何内容都无法添加收款方，所以骗子也做不到。",
  },
  "reply.raise_limit": {
    en: "I can't change my own limits; that's on the never-list. Only your dad can change the tuition limit, by signing a new one with his passkey.",
    vi: "Mình không thể tự nâng giới hạn của mình; đó là việc bị cấm tuyệt đối. Chỉ ba bạn mới đổi được giới hạn học phí, bằng cách ký giới hạn mới bằng passkey của ba.",
    ko: "제 한도는 제가 바꿀 수 없어요. 절대 금지 항목이에요. 등록금 한도는 아버님만 패스키로 새로 서명해서 바꿀 수 있어요.",
    zh: "我不能修改自己的额度，这在绝对禁止清单上。只有你爸爸用通行密钥签署新的授权，才能更改学费额度。",
  },
  "reply.freeze_hint": {
    en: "Tap Freeze if something feels wrong. Payments still in their 30-minute hold are cancelled and the money returns. Other outgoing approvals pause; refunds keep coming back to Dad.",
    vi: "Thấy bất thường thì bấm Đóng băng nhé. Khoản còn trong 30 phút chờ sẽ được hủy, tiền trả về tài khoản. Các yêu cầu chuyển khác tạm dừng; tiền hoàn vẫn về cho ba.",
    ko: "이상하다 싶으면 동결을 눌러 주세요. 30분 보류 중인 결제는 취소되고 돈이 돌아와요. 다른 송금 승인은 멈추지만 아버지께 오는 환불은 계속돼요.",
    zh: "觉得不对劲就点冻结。仍在30分钟保留期内的付款会取消并退回资金。其他向外付款审批暂停，退给爸爸的钱仍会到账。",
  },
  "reply.structuring": {
    en: "I can't help split one payment across relatives to stay under each person's quota; that's prohibited structuring under SAFE rules. The documented path is to pay the amount on Hanbit's fee notice from one payer, with the notice as supporting evidence, or to pay in instalments as the university allows.",
    vi: "Mình không thể giúp chia một khoản cho nhiều người thân để lách hạn mức mỗi người; đó là hành vi chia nhỏ giao dịch bị cấm theo quy định của SAFE.",
    ko: "한 번의 송금을 친척 여러 명에게 나눠 1인 한도를 피하는 건 도와드릴 수 없어요. 중국 외환관리국(SAFE) 규정상 금지된 분할 송금이에요. 정식 방법은 대학 납부 고지서 금액을 한 명이 송금하고 고지서를 증빙으로 제출하거나, 대학이 허용하는 분납을 이용하는 거예요.",
    zh: "我不能帮您把一笔付款拆分给多位亲属以规避每人额度，按外汇局（SAFE）规定这属于禁止的拆分购汇。合规做法是由一位付款人按学校缴费通知书金额汇款并附通知书作为证明，或按学校允许的方式分期缴纳。",
  },
  "reply.fallback": {
    en: "I can help with Hanbit tuition, the refund if the visa is refused, and anything about where the money is. Try forwarding the invoice, or ask \"how much is due in VND?\"",
    vi: "Mình giúp được việc đóng học phí Hanbit, lấy lại tiền nếu trượt visa, và mọi câu hỏi về tiền đang ở đâu. Bạn thử chuyển tiếp hoá đơn, hoặc hỏi \"phải đóng bao nhiêu tiền Việt?\" nhé.",
    ko: "한빛대 등록금 납부, 비자 거절 시 환불, 돈이 어디 있는지에 관한 건 뭐든 도와드릴 수 있어요. 청구서를 전달하거나 \"동화로 얼마 내야 해?\"라고 물어보세요.",
    zh: "我可以帮忙缴韩光大学的学费、拒签后的退款，以及查询资金去向。可以试试转发发票，或者问“要付多少越南盾？”",
  },
  "reply.frozen": {
    en: "Outgoing payments are paused. Refunds can still come back to Dad. He can unfreeze with his passkey; valid signed limits resume, and cancelled payments stay cancelled.",
    vi: "Đang tạm dừng chuyển tiền ra ngoài. Tiền hoàn vẫn về cho ba nhé. Ba mở lại bằng passkey thì hạn mức đã ký còn hạn dùng lại được; khoản đã hủy không tự gửi lại.",
    ko: "보내는 결제는 잠시 멈췄어요. 아버지께 오는 환불은 계속돼요. 패스키로 해제하면 유효한 기존 한도가 복원되고 취소된 결제는 다시 보내지 않아요.",
    zh: "向外付款已暂停，退给爸爸的钱仍会到账。爸爸可用通行密钥恢复，仍有效的原授权额度会恢复，已取消的付款不会自动重发。",
  },
  "reply.parent_intro": {
    en: "Hello {name}. Right now: {state}. You only need to act when I send you something to approve.",
    vi: "Chào anh {name}. Hiện tại: {state}. Anh chỉ cần làm gì khi mình gửi thẻ cần duyệt.",
    ko: "안녕하세요, {name}님. 현재 상황: {state}. 승인할 일이 생기면 그때만 알려드릴게요.",
    zh: "{name}您好。目前：{state}。只有需要您确认时我才会打扰您。",
  },
} satisfies Record<string, Dict>;

export type CopyKey = keyof typeof C;

export function copy(locale: Locale, key: CopyKey, params: Params = {}) {
  const dict = C[key] as Dict;
  let s = dict[locale] ?? dict.en;
  for (const [k, v] of Object.entries(params)) s = s.replaceAll(`{${k}}`, String(v));
  return s;
}

/** Detect the language a message was written in; fall back to the UI locale. */
export function detectLocale(text: string, fallback: Locale): Locale {
  if (!text.trim()) return fallback;
  if (/[가-힯ᄀ-ᇿ]/.test(text)) return "ko";
  if (/[一-鿿]/.test(text)) return "zh";
  if (/[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]/i.test(text)) return "vi";
  const t = text.toLowerCase();
  if (/\b(ba oi|me oi|chuyen tien|hoc phi|cho con|nha|nhe|bao nhieu|tien|truot|dong tien|khong|duoc)\b/.test(t)) return "vi";
  if (/\b(the|is|how|what|when|where|pay|please|my|dad|can|you|much|due)\b/.test(t)) return "en";
  if (/[a-z]/.test(t) && fallback !== "vi") return "en";
  return fallback;
}

export function normalize(text: string) {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .normalize("NFC"); // re-compose Hangul (NFD splits syllables into jamo)
}
