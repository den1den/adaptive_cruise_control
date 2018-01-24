def dict_update(base: dict, update: dict):
    if update:
        base.update(update)
    return base


def dict_poll(d: dict, key, default):
    if key in d:
        default = d[key]
        del d[key]
    return default


def alpha_to_int(alpha: str):
    assert len(alpha) == 1
    i = 'abcdefghijklmnopqrstuvwxyz'.index(alpha)
    return i


def dict_val_to_array(d: dict, key):
    v = d.setdefault(key, [])
    if type(v) is str:
        v = [v]
        d[key] = v
    return v


def dict_poll_all_if_present(d: dict, *keys):
    r = {}
    for k in keys:
        if k in d:
            r[d] = k
            del r[d]
    return r


def dict_remove_empty_list(d: dict, key):
    if key in d:
        v = d[key]
        assert type(v) is list
        if len(v) == 0:
            del d[key]
            return True
    return False


def iter_list_or_single(v):
    if type(v) is list:
        for x in v:
            yield x
    else:
        yield v
