import logging
import json
import os
import subprocess

import neovim
import docker


log = logging.getLogger("cui")


class Backend:
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


class DisplayedObject:
    def __init__(self, data, display):
        self.data = data
        self.display = display


class DockerBackend(Backend):
    def __init__(self):
        super(DockerBackend, self).__init__()
        self.d = docker.APIClient()

    def get_list(self):
        images = self.d.images()

        # TODO: figure out displaying: raw data -> pretty data
        templ = "{obj_type:12} {backend_name:12} {id_short:14} {name:32} {misc}"
        result = []
        for i in images:
            try:
                n = i["RepoTags"][0]
            except (IndexError, KeyError, TypeError):
                n = ""
            display = templ.format(obj_type="image", backend_name="docker",
                                   id_short=i["Id"][:12], name=n, misc="")
            result.append(DisplayedObject(i, display))
        return result


class Store:
    def __init__(self):
        self.displayed_items = None
        self.b = BuildahBackend()
        self.d = DockerBackend()

    def get_list(self):
        # workflow:
        #  1. get backend items
        #  2. sort them
        #  3. render them
        #  4. save the mapping
        #  5. return
        # self.items[:] = self.b.get_list()
        self.displayed_items = self.d.get_list()
        return [x.display for x in self.displayed_items]

    def delete(self, start_idx, end_idx=None):
        log.info("delete %s - %s", start_idx, end_idx)
        if end_idx:
            for i in self.displayed_items[start_idx:end_idx]:
                self.d.d.remove_image(i.data)
        else:
            self.d.d.remove_image(self.displayed_items[start_idx].data)


def set_logging(
        logger_name="cui",
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs).03d %(filename)-17s %(levelname)-6s %(message)s',
        date_format='%H:%M:%S'):
    """
    Set personal logger for this library.

    :param logger_name: str, name of the logger
    :param level: int, see logging.{DEBUG,INFO,ERROR,...}: level of logger and handler
    :param handler_class: logging.Handler instance, default is StreamHandler (/dev/stderr)
    :param handler_kwargs: dict, keyword arguments to handler's constructor
    :param format: str, formatting style
    :param date_format: str, date style in the logs
    :return: logger instance
    """
    logger = logging.getLogger(logger_name)
    # do we want to propagate to root logger?
    # logger.propagate = False
    logger.setLevel(level)

    log_file_path = os.path.join(os.getcwd(), "lucid.log")
    f = open(log_file_path, "w")
    f.close()
    handler = logging.FileHandler(log_file_path)
    handler.setLevel(level)

    formatter = logging.Formatter(format, date_format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def p2i(p):
    """ position to index """
    return p - 1


@neovim.plugin
class ContainerUI(object):
    def __init__(self, vim):
        set_logging()
        self.v = vim
        self.s = Store()

    def init_buffer(self):
        self.v.command(":tabnew")
        self.v.command(":call LucidInitMapping()")

        buf = self.v.current.buffer

        buf.name = "Lucid Container Interface"
        buf.options["swapfile"] = False
        buf.options["buftype"] = "nofile"
        buf.options['modeline'] = False
        buf.options['filetype'] = 'lucid'

        win = self.v.current.window

        win.options["wrap"] = False
        win.options["cursorline"] = True
        win.options["cursorcolumn"] = False
        win.options["concealcursor"] = "nvic"
        win.options["conceallevel"] = 3

        # FIXME: figure out how to disable insert mode
        # FIXME: disable horizontal navigation
        # FIXME: hide cursor, show only cursorline

        self.refresh()

    def refresh(self):
        self.v.current.buffer[:] = self.s.get_list()

    # this needs to be sync=True, otherwise the position is wrong
    @neovim.function('_cui_delete', sync=True)
    def delete(self, args):
        log.debug("delete(args = %s)", args)
        if args:
            # delete(args=[[3, 1, 4, 2147483647]])
            a = args[0]
            self.s.delete(p2i(a[0]), end_idx=p2i(a[2]))
        else:
            row = self.v.current.window.cursor[0]
            idx = p2i(row)
            self.s.delete(idx)
        self.refresh()

    # this needs to be sync=True, otherwise the position is wrong
    @neovim.function('_cui_inspect', sync=True)
    def inspect(self, args):
        self.v.command(":tabnew")
        # TODO: implement

    # TODO: make async
    @neovim.function('_cui_init', sync=True)
    def init(self, args):
        self.init_buffer()
