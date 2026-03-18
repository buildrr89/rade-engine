from __future__ import annotations


def collect_from_web_dom(*args, **kwargs):
    raise NotImplementedError(
        "Web DOM collection is deferred until the runtime collector phase."
    )
