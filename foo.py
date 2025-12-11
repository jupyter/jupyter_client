import orjson


def orjson_packer(
    obj: t.Any, *, option: int | None = orjson.OPT_NAIVE_UTC | orjson.OPT_UTC_Z
) -> bytes:
    return orjson.dumps(obj, options=option)
