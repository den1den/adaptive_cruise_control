def class_name_to_hutn_prefix(class_name):
    cln_capitals = ''.join(filter(str.isupper, class_name))
    if len(cln_capitals) >= 2:
        return cln_capitals.lower()
    else:
        return class_name[:2].lower()


class HutnGenerator:

    def __init__(self) -> None:
        self.indent = 0
        self.instances = {}
        self.out = None

    def _finish(self):
        for i in range(self.indent):
            self.close_block()
        self.out.close()

    def print_block(self, title: str, fn=None, closing_comma=False):
        self._print(title + ' {', 1)
        if fn:
            fn()
            self.close_block(',' if closing_comma else '')

    def print_attr_array(self, attname, cls, id_gen, body_gen, items: list):
        i = 0
        for item in items:
            if i == 0:
                title = '%s: %s "%s"' % (attname, cls, id_gen(item))
            else:
                title = '%s "%s"' % (cls, id_gen(item))
            self.print_block(
                title,
                lambda: body_gen(item),
                i < len(items) - 1,
            )
            i += 1

    def print_blocks(self, cls, id_gen, body_gen, items):
        first = True
        for i in items:
            self.print_block(
                ('' if first else ', ') + '%s "%s"' %
                (cls, id_gen(i)),
                lambda: body_gen(i)
            )
            first = False

    def inst(self, class_name, hutn_id, obj=None, keys=None, closing_comma=False):
        if obj is None:
            obj = {}
        self.print_block(
            '%s "%s"' % (class_name, hutn_id),
            lambda: self.values(obj, keys),
            closing_comma=closing_comma
        )

    def inst_with_id(self, class_name, obj, keys=None, closing_comma=False):
        hutn_id_prefix = class_name_to_hutn_prefix(class_name)
        self.inst(
            class_name,
            hutn_id_prefix + obj['id'],
            obj,
            keys,
            closing_comma
        )

    def values(self, key_values, keys=None):
        if not keys:
            keys = sorted(key_values.keys())
        for k in keys:
            if k.endswith('__refs_to_id'):
                continue
            reference_to = key_values.get(k + '__refs_to_id', None)
            v = key_values[k]
            self.print_kv(k, v, reference_to)

    def print_kv(self, key, value, reference_to=None):
        if type(key) is not str:
            raise AssertionError("Key must be string of `%s`" % key)
        if type(value) is list and len(value) == 0:
            return
        self._print(key + ': ' + self.to_repr(value, reference_to))

    def close_block(self, appendix=''):
        self.indent -= 1
        self._print('}' + appendix)

    def _print(self, line=None, indent_inc=0):
        if line:
            print('\t' * self.indent + line, file=self.out)
        else:
            print(file=self.out)
        self.indent += indent_inc

    def to_repr(self, value, reference_to=None):
        if type(value) is list:
            value_strings = [self.to_repr(v, reference_to) for v in value]
            if reference_to:
                return ', '.join(value_strings)
            else:
                return "[" + ', '.join(value_strings) + "]"
        if reference_to:
            ref_id_prefix = class_name_to_hutn_prefix(reference_to)
            return reference_to + ' "' + ref_id_prefix + value + '"'
        if type(value) is str:
            return '"' + value + '"'
        elif type(value) is int:
            return "%d" % value
        raise AssertionError("value type `%s` not recognized for `%s`" % (type(value), value))

    def print_model_instances(self, ijson_parser, as_array=None):
        # filename must adhere to `model_inst_list` scheme
        root = ijson_parser.get()
        class_name = root['class_name']
        instances_dict = root['instances']
        if as_array:
            self._print(as_array + ':')
        n = 0
        for inst_id, instance_data in sorted(instances_dict.items()):
            instance_data.setdefault('id', inst_id)
            self.inst_with_id(class_name, instance_data,
                              closing_comma=n < len(instances_dict) - 1)
            n += 1

    def print_package(self, package):
        self._print('@Spec {{ metamodel "{0}" {{ nsUri: "{0}" }} }}'.format(package))
        self._print()
