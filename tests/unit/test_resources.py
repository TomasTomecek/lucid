from lucid.resources import DisplayedItem, maps_to_resource


def test_maps_to_resource_decorator():
    class SomeResource:
        pass

    @maps_to_resource(SomeResource)
    class SomeDI(DisplayedItem):
        pass

    from lucid.resources import RESOURCE_DISPLAYED_ITEM_MAP

    assert SomeResource in RESOURCE_DISPLAYED_ITEM_MAP