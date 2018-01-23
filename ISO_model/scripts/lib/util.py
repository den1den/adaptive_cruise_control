def dict_update(base: dict, update: dict):
    if update:
        base.update(update)
    return base


def dict_poll(d: dict, key, default):
    if key in d:
        default = d[key]
        del d[key]
    return default
