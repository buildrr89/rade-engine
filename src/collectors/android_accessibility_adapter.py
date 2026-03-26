# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations


def collect_from_android_accessibility(*args, **kwargs):
    raise NotImplementedError(
        "Android accessibility collection is deferred until the runtime collector phase."
    )
