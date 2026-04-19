# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations


def extract_build_metadata(*args, **kwargs):
    raise NotImplementedError(
        "Build connector is deferred until the repo/build scan phase."
    )
