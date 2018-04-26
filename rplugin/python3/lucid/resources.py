import logging
from datetime import datetime

from lucid.util import humanize_bytes, humanize_time
from lucid.backend import PodmanImage, OpenShiftPod

from conu import DockerImage, DockerContainer

log = logging.getLogger("lucid")

ISO_DATETIME_PARSE_STRING = "%Y-%m-%dT%H:%M:%SZ"
ISO_DATETIME_PARSE_STRING_WITH_MI = "%Y-%m-%dT%H:%M:%S.%fZ"

RESOURCE_DISPLAYED_ITEM_MAP = {}


def maps_to_resource(resource_kls):
    def inner(di_kls):
        def wrapped(*args):
            """ magic """
            RESOURCE_DISPLAYED_ITEM_MAP[resource_kls] = di_kls
        return wrapped()
    return inner


def get_displayed_item_for_resource(resource, backend):
    try:
        di_kls = RESOURCE_DISPLAYED_ITEM_MAP[resource.__class__]
    except KeyError:
        log.error("no mapping for resource %s (%s)", resource, resource.__class__)
    else:
        return di_kls(backend, resource)


class DisplayedItem:
    """ every item in the listing has to implement this interface """

    def __init__(self, backend, resource):
        self.backend = backend
        self.resource = resource

    @property
    def last_changed(self):
        raise NotImplemented("last_changed property is not implemented")

    @property
    def displayed_name(self):
        raise NotImplemented("name property is not implemented")

    @property
    def resource_type(self):
        raise NotImplemented("resource_type property is not implemented")

    @property
    def status(self):
        raise NotImplemented("status property is not implemented")

    def remove(self):
        raise NotImplemented("remove method is not implemented")


def di_to_str(di, max_size):
    """ print DisplayedItem as a pretty string, fit in the size """
    weigths = (3, 3, 12, 7, 5)
    one_point = int(max_size / sum(weigths))

    real_size = []
    # idx, value
    max_id = (0, 0)
    for cur_id, w in enumerate(weigths):
        v = w * one_point
        if v > max_id[1]:
            max_id = cur_id, v
        real_size.append(v)
    # append remaining
    real_size[max_id[0]] += max_size - sum(real_size)

    d = {
        "name": di.displayed_name[:real_size[2] - 1],
        "type": di.resource_type,
        "backend": di.backend,
        "changed": humanize_time(di.last_changed),
        "status": di.status[:real_size[3] - 1]
    }

    pre_template = "{backend.name:%d}{type:%d}{name:%d}{status:%d}{changed:%d}"
    template = pre_template % (
        real_size[0],
        real_size[1],
        real_size[2],
        real_size[3],
        real_size[4],
    )
    return template.format(**d)


@maps_to_resource(DockerImage)
class DockerImageDI(DisplayedItem):
    def __init__(self, backend, resource):
        DisplayedItem.__init__(self, backend, resource)
        self.date_created = None

    @property
    def last_changed(self):
        if self.date_created is None:
            self.date_created = datetime.fromtimestamp(self.resource.short_metadata["Created"])
        return self.date_created

    @property
    def displayed_name(self):
        if self.resource.name:
            return self.resource.get_full_name()
        if self.resource.digest:
            return self.resource.digest
        else:
            return self.resource.get_id()[:16]

    @property
    def resource_type(self):
        return "image"

    @property
    def status(self):
        return humanize_bytes(self.resource.short_metadata["VirtualSize"])

    def remove(self):
        return self.resource.rmi()


@maps_to_resource(DockerContainer)
class DockerContainerDI(DisplayedItem):
    def __init__(self, backend, resource):
        DisplayedItem.__init__(self, backend, resource)
        self.date_created = None

    @property
    def last_changed(self):
        if self.date_created is None:
            self.date_created = datetime.fromtimestamp(self.resource.short_metadata["Created"])
        return self.date_created

    @property
    def displayed_name(self):
        if self.resource.name:
            name = self.resource.name
        else:
            name = self.resource.get_id()[:12]
        return "%s %s %s" % (name, self.resource.image, self.resource.short_metadata["Command"])

    @property
    def resource_type(self):
        return "container"

    @property
    def status(self):
        return self.resource.short_metadata["Status"]

    def remove(self):
        return self.resource.delete()


@maps_to_resource(PodmanImage)
class PodmanImageDI(DisplayedItem):
    def __init__(self, backend, resource):
        super().__init__(backend, resource)
        self.date_created = None

    @property
    def last_changed(self):
        if self.date_created is None:
            t = self.resource.get_metadata()["created"][:-4]
            self.date_created = datetime.strptime(
                t + "Z", ISO_DATETIME_PARSE_STRING_WITH_MI)
        return self.date_created

    @property
    def displayed_name(self):
        try:
            return self.resource.get_metadata()["names"][0]
        except (IndexError, KeyError, TypeError):
            return self.resource.get_id()[:16]

    @property
    def resource_type(self):
        return "image"

    @property
    def status(self):
        return humanize_bytes(self.resource.get_metadata()["size"])


@maps_to_resource(OpenShiftPod)
class OpenShiftPodDI(DisplayedItem):
    def __init__(self, backend, resource):
        super(DisplayedItem, self).__init__(backend, resource)
        self.date_changed = None

    @property
    def last_changed(self):
        if self.date_changed is None:
            t = self.resource.get_metadata()["status"]["conditions"][0]["lastTransitionTime"]
            self.date_changed = datetime.strptime(t, ISO_DATETIME_PARSE_STRING)
        return self.date_changed

    @property
    def displayed_name(self):
        return self.resource.get_metadata()["metadata"]["name"]

    @property
    def resource_type(self):
        return "pod"

    @property
    def status(self):
        return self.resource.get_metadata()["status"]["phase"]
