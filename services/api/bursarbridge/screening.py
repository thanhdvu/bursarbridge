"""Government-list Watchman adapter. Unavailable or unknown sources fail closed."""

import os

import httpx

from .security import digest


class Screening:
    def __init__(self):
        self.mode = os.getenv("SCREENING_MODE", "watchman")
        self.url = os.getenv("WATCHMAN_URL", "http://127.0.0.1:8084")

    def screen(self, name, entity_type="business"):
        if self.mode == "synthetic":
            return {
                "status": "hit" if name == "MOCK-SANCTIONS-HIT" else "clear",
                "source": "MOCK",
                "listHashes": {"MOCK": digest("synthetic test list v1")},
                "cutoff": "0.80",
            }
        try:
            info = httpx.get(self.url + "/v2/listinfo", timeout=5).json()
            lists = info.get("lists", {})
            allowed = {"us_ofac", "us_csl", "us_fincen", "eu_csl", "uk_ofsi", "un_csl"}
            if not lists or not set(lists).issubset(allowed) or not all(v > 0 for v in lists.values()):
                raise ValueError("Government lists missing or unapproved data loaded")
            response = httpx.get(
                self.url + "/v2/search",
                params={"type": entity_type, "name": name, "minMatch": "0.80", "limit": 5},
                timeout=5,
            )
            response.raise_for_status()
            hits = response.json().get("entities") or []
            return {
                "status": "hit" if hits else "clear",
                "source": "Watchman",
                "listHashes": info.get("listHashes", {}),
                "cutoff": "0.80",
                "version": info.get("version"),
                "queryHash": digest(name),
                "hits": [
                    {
                        "sourceList": h.get("sourceList"),
                        "sourceID": h.get("sourceID"),
                        "match": h.get("match"),
                    }
                    for h in hits
                ],
            }
        except Exception:
            return {"status": "unavailable", "source": "Watchman", "listHashes": {}, "cutoff": "0.80"}
