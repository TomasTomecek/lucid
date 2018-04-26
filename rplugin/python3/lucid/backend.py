"""
move everything from here inside conu

the code in here must import only from lucid leaf modules
"""
import json
import logging
import subprocess

from conu.apidefs.backend import Backend
from conu.apidefs.container import Container
from conu.apidefs.image import Image


log = logging.getLogger("lucid")


def get_command_output(cmd):
    try:
        return subprocess.check_output(cmd)
    except subprocess.CalledProcessError as ex:
        log.error("out = %s, err = %s, rc = %s", ex.output, ex.stderr, ex.returncode)
        raise


class PodmanImage(Image):
    def __init__(self, metadata):
        try:
            reference = metadata["names"][0]
        except (IndexError, KeyError):
            reference = None
        super(PodmanImage, self).__init__(reference)
        self._id = metadata.get("id", None)
        self._metadata = metadata

    def get_metadata(self, refresh=False):
        return self._metadata


class PodmanBackend(Backend):
    name = "podman"

    def list_images(self):
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
            response.append(PodmanImage(i))
        return response


# TODO: create Resource type in conu
class OpenShiftPod:
    def __init__(self, metadata):
        self._metadata = metadata

    def get_metadata(self):
        return self._metadata


class OpenShiftBackend(Backend):
    name = "openshift"

    def list_pods(self):
        cmd = ["oc", "-o", "json", "get", "pods", "--all-namespaces"]
        response = []
        try:
            out = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as ex:
            log.error("oc command failed: %s, %s", ex.stderr, ex.stdout)
        else:
            j = json.loads(out)
            for item in j["items"]:
                response.append(OpenShiftPod(item))
        return response
