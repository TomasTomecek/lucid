"""
Configuration module for lucid
"""

import logging


log = logging.getLogger("lucid")


class Configuration:
    def __init__(self, vim_vars):
        """
        :param vim_vars: variables from nvim
        """
        self.vim_vars = vim_vars

    def get_window_method(self, default=":tabnew"):
        """ command to use when starting lucid: split, vsplit, tabnew, '' (current window) """
        window_method = self.vim_vars.get("lucid_window_method", default)
        log.debug("window method = %s", window_method)
        return window_method

    def get_window_details_method(self, default=":tabnew"):
        """ command to use when showing details: split, vsplit, tabnew, '' (current window) """
        window_method = self.vim_vars.get("lucid_window_details_method", default)
        log.debug("window details method = %s", window_method)
        return window_method
