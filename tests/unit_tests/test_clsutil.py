from apibean.core.util.clsutil import find_classes_with_metaclass

from example.metaclasses.my_meta import MyMeta
import example.metaclasses
import pydash

def test_filter_classes_from_package_with_metaclass():
    classes = find_classes_with_metaclass(example.metaclasses, MyMeta)
    cls_map = pydash.key_by(classes, lambda cls: f"{cls.__module__}.{cls.__name__}")

    assert len(cls_map) == 2
    assert cls_map.get("example.metaclasses.module_a.A") is example.metaclasses.module_a.A
    assert cls_map.get("example.metaclasses.module_b.B") is example.metaclasses.module_b.B
