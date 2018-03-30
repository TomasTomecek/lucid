"""
TODO:
 * implement status line (integrate with airline)
"""
import logging
import os

from lucid.app import App

import neovim


log = logging.getLogger("lucid")


def set_logging(
        logger_name="lucid",
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs).03d %(filename)-17s %(levelname)-6s %(message)s',
        date_format='%H:%M:%S'):
    """
    Set personal logger for this library.

    :param logger_name: str, name of the logger
    :param level: int, see logging.{DEBUG,INFO,ERROR,...}: level of logger and handler
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
    """ position to index: vim's getpos into index """
    return p - 1


def a2i(a, p):
    """ args to index; vim's getpos(.) -> index """
    return p2i(a[0][p])


def get_buffer_method(vim):
    # TODO: create configuration interface
    # FIXME: make this generic
    buffer_method = vim.vars.get("lucid_buffer_method", ":tabnew")
    log.debug("buffer method = %s", buffer_method)
    return buffer_method


@neovim.plugin
class Lucid(object):
    def __init__(self, vim):
        set_logging()
        self.v = vim
        self.app = App()
        self.width = 0

    def init_buffer(self):
        buffer_method = get_buffer_method(self.v)
        self.v.command(buffer_method)
        self.v.command(":call LucidInitMapping()")

        buf = self.v.current.buffer

        buf.name = "Lucid Container Interface"
        buf.options["swapfile"] = False
        buf.options["buftype"] = "nofile"
        buf.options['modeline'] = False
        buf.options['filetype'] = 'lucid'

        win = self.v.current.window
        self.width = win.width

        win.options["wrap"] = False
        win.options["cursorline"] = True
        win.options["cursorcolumn"] = False
        win.options["concealcursor"] = "nvic"
        win.options["conceallevel"] = 3

        # TODO: create new mapping to override 'i', 'a', 'A', 'c', 'C', 'I'
        # FIXME: disable horizontal navigation
        # FIXME: hide cursor, show only cursorline

        self.refresh()

    def _set_statusline(self):
        self.v.command(":set statusline+=%d\ items" % len(self.v.current.buffer))

    def refresh(self):
        # TODO: insert marks for each line
        self.v.current.buffer[:] = self.app.populate_list(self.width)
        self._set_statusline()

    # this needs to be sync=True, otherwise the position is wrong
    @neovim.function('_cui_delete', sync=True)
    def delete(self, args):
        log.debug("delete(args = %s)", args)
        if args:
            # delete(args=[[3, 1, 4, 2147483647]])
            self.s.delete(a2i(args, 0), end_idx=a2i(args, 2))
        else:
            row = self.v.current.window.cursor[0]
            idx = p2i(row)
            self.s.delete(idx)
        self.refresh()

    # this needs to be sync=True, otherwise the position is wrong
    @neovim.function('LucidShowDetails', sync=True)
    def inspect(self, args):
        idx = a2i(args, 1)
        resource = self.app.get_resource(idx)

        # FIXME: make configurable
        self.v.command(":tabnew")

        buf = self.v.current.buffer
        buf[:] = self.app.get_details_for(idx)

        buf.name = "Details of %s %s" % (resource.resource_type, resource.displayed_name)
        buf.options["swapfile"] = False
        buf.options["buftype"] = "nowrite"
        buf.options['modeline'] = False

        win = self.v.current.window
        self.width = win.width

        win.options["wrap"] = False

        # buf.options['filetype'] = 'json'
        # apparently set command also enforces colors or what
        self.v.command(":set ft=json")

    # TODO: make async
    @neovim.function('LucidRun', sync=True)
    def init(self, args):
        self.init_buffer()
