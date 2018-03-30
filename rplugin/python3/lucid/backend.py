"""
all the backends
"""
import json
import logging
import subprocess
from datetime import datetime

import docker
from conu import DockerImage, DockerImagePullPolicy

from lucid.util import humanize_bytes, humanize_time


ISO_DATETIME_PARSE_STRING = "%Y-%m-%dT%H:%M:%SZ"
ISO_DATETIME_PARSE_STRING_WITH_MI = "%Y-%m-%dT%H:%M:%S.%fZ"

log = logging.getLogger("lucid")


def get_command_output(cmd):
    try:
        return subprocess.check_output(cmd)
    except subprocess.CalledProcessError as ex:
        log.error("out = %s, err = %s, rc = %s", ex.output, ex.stderr, ex.returncode)
        raise


class Backend:
    name = ""

    def __init__(self):
        pass

    def get_list(self):
        pass

    def delete(self, obj):
        pass


class Resource:
    """ every item in the listing has to implement this interface """

    def __init__(self, backend):
        self.backend = backend

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

    def to_str(self, max_size):
        """ print this resource as a pretty string, fit in the size """
        d = {
            "name": self.displayed_name[:32],
            "type": self.resource_type,
            "backend": self.backend,
            "changed": humanize_time(self.last_changed),
            "status": self.status
        }
        template = "{backend.name:12} {type:10} {name:32} {status:16} {changed:12}"
        return template.format(**d)


class PodmanImage(Resource):
    def __init__(self, backend, metadata):
        super(PodmanImage, self).__init__(backend)
        self.m = metadata
        self.date_created = None

    @property
    def last_changed(self):
        if self.date_created is None:
            t = self.m["created"][:-4]
            self.date_created = datetime.strptime(
                t + "Z", ISO_DATETIME_PARSE_STRING_WITH_MI)
        return self.date_created

    @property
    def displayed_name(self):
        try:
            return self.m["names"][0]
        except (IndexError, KeyError, TypeError):
            return self.m["Id"][:16]

    @property
    def resource_type(self):
        return "image"

    @property
    def status(self):
        return humanize_bytes(self.m["size"])


class PodmanBackend(Backend):
    name = "podman"

    def get_list(self):
        # {
        #     "id": "9110ae7f579f35ee0c3938696f23fe0f5fbe641738ea52eb83c2df7e9995fa17",
        #     "names": [
        #         "docker.io/library/fedora:27"
        #     ],
        #     "digest": "sha256:8f97ccd41222754a70204fec8faa07504f790454a22c888bd92f0c52463e0f3d",
        #     "created": "2018-03-07T20:51:34.488688562Z",
        #     "size": 246136632
        # }
        c = ["sudo", "podman", "images", "--format", "json"]
        images_s = subprocess.check_output(c)
        images = json.loads(images_s)
        response = []
        for i in images:
            response.append(PodmanImage(self, i))
        return response


class DockerImageResource(Resource, DockerImage):
    def __init__(self, backend, short_metadata):
        Resource.__init__(self, backend)
        DockerImage.__init__(self, None, pull_policy=DockerImagePullPolicy.NEVER)
        self._id = short_metadata["Id"]
        self.s = short_metadata
        self.date_created = None

    @property
    def last_changed(self):
        if self.date_created is None:
            self.date_created = datetime.fromtimestamp(self.s["Created"])
        return self.date_created

    @property
    def displayed_name(self):
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
            result.append(DockerImageResource(self, i))
        return result


class OpenShiftPod(Resource):
    def __init__(self, backend, metadata):
        super(OpenShiftPod, self).__init__(backend)
        self.m = metadata
        self.date_changed = None

    @property
    def last_changed(self):
        if self.date_changed is None:
            t = self.m["status"]["conditions"][0]["lastTransitionTime"]
            self.date_changed = datetime.strptime(t, ISO_DATETIME_PARSE_STRING)
        return self.date_changed

    @property
    def displayed_name(self):
        return self.m["metadata"]["name"]

    @property
    def resource_type(self):
        return "pod"

    @property
    def status(self):
        return self.m["status"]["phase"]


class OpenShiftBackend(Backend):
    name = "openshift"

    def get_list(self):
        cmd = ["oc", "-o", "json", "get", "pods", "--all-namespaces"]
        response = []
        try:
            out = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as ex:
            log.error("oc command failed: %s, %s", ex.stderr, ex.stdout)
        else:
            j = json.loads(out)
            for item in j["items"]:
                response.append(OpenShiftPod(self, item))
        return response
