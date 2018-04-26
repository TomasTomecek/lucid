import json
import logging

from conu import DockerBackend
from lucid.backend import OpenShiftBackend, PodmanBackend
from lucid.resources import get_displayed_item_for_resource, di_to_str

log = logging.getLogger("lucid")


def get_docker_resources():
    """ return (backend, [list of resources]) """
    with DockerBackend() as b:
        return b, b.list_containers() + b.list_images()


def get_podman_resources():
    """ return (backend, [list of resources]) """
    with PodmanBackend() as b:
        return b, b.list_images()


def get_backends(fi):
    """
    get list of backend classes according to filter

    :param fi: list of str; backend names, all = give all of them
    :return: list of backend classes
    """
    all_backend_classes = [
        DockerBackend,
        # OpenShiftBackend,
        PodmanBackend,
    ]
    if "all" in fi:
        return all_backend_classes
    return [x for x in all_backend_classes if x.name in fi]


class Listing:
    """ provide list of objects """
    QUERY_MAP = {
        DockerBackend: get_docker_resources,
        PodmanBackend: get_podman_resources,
    }

    def __init__(self, query):
        log.debug("guery = %s", query)
        self.query = query
        self.backend_classes = get_backends(query.get("backend", ["all"]))
        self.resource_query = query.get("resource", ["all"])

    def get_list(self):
        result = []
        for bc in self.backend_classes:
            log.debug("getting list of resources for %s", bc)
            cb = self.QUERY_MAP[bc]
            try:
                backend, li = cb()
            except Exception as ex:
                # TODO: make this configurable; just print in nvim that some backend failed
                #       and users should check logs
                log.error("there was an error when getting resources from backend %s: %s",
                          bc, ex)
                continue
            log.debug("callback yielded %d results", len(li))
            if "all" not in self.resource_query:
                li = [item for res in self.resource_query for item in li if item.type == res]
            li = [get_displayed_item_for_resource(x, backend) for x in li
                  if get_displayed_item_for_resource(x, backend)]
            result += li
        return result


class App:
    """ Center-piece of everything, all the core logic """
    def __init__(self):
        self.displayed_items = []

    def populate_list(self, display_width, query):
        """ load all resources from backends"""
        listing = Listing(query)
        li = listing.get_list()

        # TODO: implement sorting
        # self.displayed_resources[:] = sorted(li, )

        self.displayed_items[:] = li
        return [di_to_str(x, display_width) for x in self.displayed_items]

    def delete(self, start_idx, end_idx=None):
        log.info("delete %s - %s", start_idx, end_idx)
        if end_idx:
            for i in self.displayed_items[start_idx:end_idx]:
                # TODO: remove in parallel
                i.remove()
        else:
            self.displayed_items[start_idx].remove()

    def get_details_for(self, idx):
        log.debug("get details for idx %s", idx)
        d = self.displayed_items[idx].resource.get_metadata()
        return json.dumps(d, indent=2).split("\n")

    def get_displayed_item(self, idx):
        log.debug("get displayed item for idx %s", idx)
        return self.displayed_items[idx]
