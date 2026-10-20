# Try BursarBridge

With Node.js 20 or later and pnpm 10 installed, run:

```sh
cd apps/web
pnpm install
pnpm dev:3700
```

Open http://localhost:3700/demo and follow the seven scenes. The web starts in **mock mode**, so you can try the whole family story on its own, without an API or a key. All money and organisations are fictional and labelled MOCK.

For **live mode**, start the local API on port 8000 using the [local setup guide](../../docs/deploy/local.md). Open the floating **Demo** controls, choose **API LIVE**, and tap **Reset demo** twice. The API must allow the passkey origin `http://localhost:3700`. Choose **API MOCK** to rehearse offline again; this browser remembers your choice.

On a phone, the Demo controls switch between Minh, Linh and Lan. The admission certificate is available before payment. Try Freeze during a payment's 30-minute hold, or forward a refusal letter before paying; reset before trying the paid-refusal and refund story. A quiet catch-up message after reset means the evidence is updating automatically.

For another API address, copy `.env.example` to `.env.local`, change `BB_API_ORIGIN`, and restart the web.

```sh
pnpm lint
pnpm typecheck
pnpm build
```

[Phone acceptance notes](qa/round6/README.md) | [Third-party licences](THIRD_PARTY_LICENSES.md)
