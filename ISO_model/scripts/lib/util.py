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


def dict_val_to_array(d: dict, key, assert_present=False):
    if assert_present:
        assert key in d
    v = d.setdefault(key, [])
    if type(v) is not list:
        v = [v]
        d[key] = v
    return v


def dict_poll_all_if_present(d: dict, *keys):
    r = {}
    for k in keys:
        if k in d:
            v = d[k]
            r[k] = v
            del d[k]
    return r


def dict_remove_if_empty_list(d: dict, key):
    if key in d:
        v = d[key]
        if type(v) is list:
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
