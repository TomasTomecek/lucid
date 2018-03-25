import logging

from lucid.backend import DockerBackend, OpenShiftBackend, PodmanBackend


log = logging.getLogger("lucid")


class App:
    """ Center-piece of everything, all the core logic """
    def __init__(self):
        self.displayed_resources = []
        self.backends = [
            DockerBackend(),
            OpenShiftBackend(),
            PodmanBackend(),
        ]

    def populate_list(self, display_width):
        """ load all resources from backends"""
        # TODO: implement filtering, e.g. `:filter backend=openshift resource=pod`
        li = []
        for b in self.backends:
            li += b.get_list()

        # TODO: implement sorting
        self.displayed_resources[:] = li
        return [x.to_str(display_width) for x in self.displayed_resources]

    def delete(self, start_idx, end_idx=None):
        log.info("delete %s - %s", start_idx, end_idx)
        if end_idx:
            for i in self.displayed_resources[start_idx:end_idx]:
                # TODO: remove in parallel
                i.remove()
        else:
            self.displayed_resources[start_idx].remove()
