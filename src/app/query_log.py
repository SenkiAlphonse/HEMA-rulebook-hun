"""Search query logging — emits structured JSON lines for analysis.

Privacy: only the query string, language, and result metadata are logged.
NO IP addresses, user agents, session IDs, or other identifying data.

Output: a dedicated logger ``hema.query`` writes one JSON object per line to
stdout (captured by hosting platform logs). Disable by setting the env var
``HEMA_QUERY_LOG=0``.

Future upgrade path: swap the handler to a FileHandler pointing at a
persistent disk path (Render disk) without touching call sites.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time

_LOGGER_NAME = "hema.query"
_ENABLED = os.environ.get("HEMA_QUERY_LOG", "1") != "0"


def _build_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    # Output is the message itself (we pre-serialize to JSON).
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # don't double-log via root
    return logger


_logger = _build_logger()


def log_search(
    *,
    query: str,
    rules_lang: str,
    result_count: int,
    top_rule_id: str | None = None,
    variant_filter: str | None = None,
    weapon_filter: str | None = None,
) -> None:
    """Log a single search event as a JSON line.

    Cheap and fire-and-forget; never raises (logging errors are swallowed so a
    failed log call cannot break a user-facing search).
    """
    if not _ENABLED:
        return
    try:
        payload = {
            "ts": int(time.time()),
            "event": "search",
            "query": query,
            "lang": rules_lang,
            "result_count": result_count,
            "top_rule_id": top_rule_id,
            "variant_filter": variant_filter,
            "weapon_filter": weapon_filter,
        }
        _logger.info(json.dumps(payload, ensure_ascii=False))
    except Exception:
        # Never let logging break the request path.
        pass
