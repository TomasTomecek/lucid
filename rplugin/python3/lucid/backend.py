"""
all the backends
"""
import json
import subprocess
from datetime import datetime

import docker

from lucid.util import humanize_bytes, humanize_time


class Backend:
    name = ""
    
    def __init__(self):
        pass

    def get_list(self):
        pass

    def delete(self, obj):
        pass


# stateless?
class BuildahBackend(Backend):
    def __init__(self):
        super(BuildahBackend, self).__init__()

    def get_list(self):
        # {
        #     "id": "c24863c7a80057d71b5dbe1e1cee54414b715e2233b3a79d721f18d3ab2ead3e",
        #     "names": [
        #         "docker.io/library/container-conductor-fedora-26:0.9.3rc0"
        #     ]
        # },
        c = ["sudo", "buildah", "images", "--json"]
        images_s = subprocess.check_output(c)
        images = json.loads(images_s)

        # {
        #     "id": "80c68cabb8da5dfa1a130c31c582a647ae9a14199d4ecb44df43947b9654f824",
        #     "builder": true,
        #     "imageid": "5b48cb988991bbeda9001fcde7d2c5d06b183f67cfe50b62f3f97d98c4f54a08",
        #     "imagename": "docker.io/library/weechat-container-conductor:latest",
        #     "containername": "weechat-container_conductor"
        # },
        c = ["sudo", "buildah", "containers", "--json"]
        containers_s = subprocess.check_output(c)
        containers = json.loads(containers_s)

        # TODO: figure out displaying: raw data -> pretty data
        templ = "{obj_type:12} {backend_name:12} {id_short:14} {name:32} {misc}"
        result = []
        for i in images:
            try:
                n = i["names"][0]
            except (IndexError, KeyError, TypeError):
                n = ""
            result.append(templ.format(obj_type="image", backend_name="buildah",
                                       id_short=i["id"][:12], name=n, misc=""))
        for c in containers:
            result.append(templ.format(obj_type="container", backend_name="buildah",
                                       id_short=c["id"][:12], name=c["containername"],
                                       misc=c["containername"]))

        return result


class Resource:
    """ every item in the listing has to implement this interface """

    def __init__(self, backend):
        self.backend_instance = backend

    @property
    def last_changed(self):
        raise NotImplemented("last_changed property is not implemented")

    @property
    def name(self):
        raise NotImplemented("name property is not implemented")

    @property
    def resource_type(self):
        raise NotImplemented("resource_type property is not implemented")

    @property
    def backend(self):
        return self.backend_instance

    @property
    def status(self):
        raise NotImplemented("status property is not implemented")

    def to_str(self, max_size):
        """ print this resource as a pretty string, fit in the size """
        d = {
            "name": self.name[:32],
            "type": self.resource_type,
            "backend": self.backend,
            "changed": humanize_time(self.last_changed),
            "status": self.status
        }
        template = "{backend.name:12} {type:10} {name:32} {status:16} {changed:12}"
        return template.format(**d)


class PodmanBackend(Backend):
    name = "podman"
    def get_list(self):
        return []


class DockerImage(Resource):
    def __init__(self, backend, short_metadata):
        super(DockerImage, self).__init__(backend)
        self.s = short_metadata
        self.date_created = None

    @property
    def last_changed(self):
        if self.date_created is None:
            self.date_created = datetime.fromtimestamp(self.s["Created"])
        return self.date_created

    @property
    def name(self):
        try:
            return self.s["RepoTags"][0]
        except (IndexError, KeyError, TypeError):
            return self.s["Id"][:16]

    @property
    def resource_type(self):
        return "image"

    @property
    def status(self):
        return humanize_bytes(self.s["VirtualSize"])


class DockerBackend(Backend):
    name = "docker"
    def __init__(self):
        super(DockerBackend, self).__init__()
        self.d = docker.APIClient()

    def get_list(self):
        # TODO: add containers
        images = self.d.images()
        result = []
        for i in images:
            result.append(DockerImage(self, i))
        return result


class OpenShiftBackend(Backend):
    name = "openshift"
    def get_list(self):
        return []
