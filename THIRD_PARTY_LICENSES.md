# Third-party notices

Only synthetic fixtures are distributed. No OpenSanctions bulk data, CC BY-NC datasets, real institutional branding or real credentials are used.

Direct runtime dependencies (exact resolved versions in `services/api/uv.lock`):

| Component | License | Source |
|---|---|---|
| Python | PSF-2.0 | https://github.com/python/cpython |
| FastAPI | MIT | https://github.com/fastapi/fastapi |
| Uvicorn | BSD-3-Clause | https://github.com/encode/uvicorn |
| SQLModel | MIT | https://github.com/fastapi/sqlmodel |
| SQLAlchemy | MIT | https://github.com/sqlalchemy/sqlalchemy |
| LangGraph | MIT | https://github.com/langchain-ai/langgraph |
| PyJWT | MIT | https://github.com/jpadilla/pyjwt |
| cryptography | Apache-2.0 OR BSD-3-Clause | https://github.com/pyca/cryptography |
| base58 | MIT | https://github.com/keis/base58 |
| py_webauthn | BSD-3-Clause | https://github.com/duo-labs/py_webauthn |
| web3.py | MIT | https://github.com/ethereum/web3.py |
| HTTPX | BSD-3-Clause | https://github.com/encode/httpx |
| python-multipart | Apache-2.0 | https://github.com/Kludex/python-multipart |
| pypdf | BSD-3-Clause | https://github.com/py-pdf/pypdf |
| ReportLab | BSD-3-Clause | https://hg.reportlab.com/hg-public/reportlab/ |
| PyYAML | MIT | https://github.com/yaml/pyyaml |
| pytest | MIT | https://github.com/pytest-dev/pytest |
| Ruff | MIT | https://github.com/astral-sh/ruff |
| FISCO BCOS and builder (downloaded locally, not vendored) | Apache-2.0 | https://github.com/FISCO-BCOS/FISCO-BCOS |
| Moov Watchman (government OFAC list only) | Apache-2.0 | https://github.com/moov-io/watchman |
| Go 1.27.2 (native Watchman build toolchain) | BSD-3-Clause | https://go.dev/LICENSE |
| Caddy (deployment reverse proxy; official package, not vendored) | Apache-2.0 | https://github.com/caddyserver/caddy |
| uv (deployment Python tooling) | MIT OR Apache-2.0 | https://github.com/astral-sh/uv |
| Node.js (deployment runtime/build tool) | MIT and bundled dependency notices | https://github.com/nodejs/node |
| pnpm (deployment build tool) | MIT | https://github.com/pnpm/pnpm |
| QEMU user emulation (optional local arm64 verification only, not deployed/vendored) | GPL-2.0 | https://www.qemu.org/docs/master/about/license.html |
| python-dotenv | BSD-3-Clause | https://github.com/theskumar/python-dotenv |
| solc 0.8.19 build compiler | GPL-3.0 | https://github.com/ethereum/solidity |

Government sanctions source: US Treasury OFAC via Watchman, with list-content hashes in screening evidence. Frankfurter ECB reference snapshot source and date are embedded in `services/api/bursarbridge/ecb_snapshot.json`. These data are not represented as a commercial bank quote. The compiler runs as a separate build tool; application contracts are MIT-licensed and contain no compiler source.

Upstream license files remain in installed packages/downloads. A machine-generated installed-package notice inventory is part of the evidence build. Frankfurter reference data is attributed to its central-bank provider, not represented as a live bank execution rate.
