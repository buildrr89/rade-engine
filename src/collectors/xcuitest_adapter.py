# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations


def collect_from_xcuitest(*args, **kwargs):
    raise NotImplementedError(
        "XCUITest collection is deferred until the runtime collector phase."
    )
