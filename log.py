# coding = UTF-8
"""
Logging utility for PisteCreator

By default we log in temporary file 

A signal is emmited for each log if required
"""
from builtins import str
from builtins import object

import sys
import tempfile
import os

LEVELS = {"debug": 0, "notice": 1, "warning": 2, "error": 3}


def _format(kwd, args):
    return (
        kwd
        + ": "
        + " ".join([str(arg) for arg in args]).replace("\n", "\n" + str(kwd) + ": ")
        + "\n"
    )


class NullProgressDisplay(object):
    """ Null Progress Display """

    def __init__(self):
        pass

    def set_ratio(self, ratio):
        pass


class ConsoleProgressDisplay(object):
    """ Console Progress Display """

    def __init__(self):
        if sys.stdout.isatty():
            sys.stdout.write("  0%")
            sys.stdout.flush()

    def set_ratio(self, ratio):
        """ Display progress through simulation dates

        :param ratio: ratio of calculated dates
        :type ratio: float
        """
        if sys.stdout.isatty():
            sys.stdout.write("\b" * 4 + "% 3d%%" % (int(ratio * 100)))
            sys.stdout.flush()

    def __del__(self):
        if sys.stdout.isatty():
            sys.stdout.write("\n")
        else:
            sys.stdout.write("100%\n")
        sys.stdout.flush()


class QGisProgressDisplay(object):
    """QProgressBar wrapper to provide minimal interface"""

    def __init__(self):
        """Constructor"""
        from qgis.PyQt.QtWidgets import QProgressBar
        from qgis.PyQt.QtCore import Qt

        self.__widget = QProgressBar()
        self.__widget.setMaximum(100)
        self.__widget.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    def widget(self):
        """ Return the QProgressBar 

        :return: progress bar
        :rtype: QProgressBar
        """
        return self.__widget

    def set_ratio(self, ratio):
        """ set ratio of calculated dates

        :param ratio: ratio of calculated dates
        :type ratio: float
        """
        self.__widget.setValue(int(ratio * 100))


class Logger(object):
    """ PisteCreator Logger"""

    def __init__(
        self,
        file_=os.path.join(
            tempfile.gettempdir(),
            (
                os.environ.get("USERNAME")
                if "USERNAME" in os.environ
                else os.environ.get("USER")
            )
            + "_PisteCreator.log",
        ),
        iface=None,
        level="notice",
        enable_console=False,
    ):
        """Constructor

        :param file: log file path
        :type file: string
        :param iface: qgis interface
        :type iface: QgisInterface
        :param level: logger level
        :type level: string
        :param enable_console: flag, enable console output
        :type enable_console: bool
        """
        assert level in LEVELS

        self.__logfile = open(file_, "w+") if file_ else None
        self.__iface = iface
        self.__level = level
        self.__enable_console = enable_console

    def __del__(self):
        self.__logfile.close()

    def set_iface(self, iface):
        """ Set iface attribute

        :param iface: qgis interface
        :type iface: QgisInterface
        """
        self.__iface = iface

    def enable_console(self, flag):
        """ Activate output in the console

        :param flag: flag, enable console output
        :type flag: bool
        """
        self.__enable_console = flag

    def set_level(self, level):
        """ Set logger level

        :param level: logger level
        :type level: string
        """
        self.__level = level

    def error(self, *args):
        """ Write error"""
        if LEVELS["error"] >= LEVELS[self.__level]:
            message = _format("", args)
            if self.__iface:
                self.__iface.messageBar().pushCritical(
                    "PisteCreator", _format("", args)
                )
            if self.__logfile:
                self.__logfile.write(_format("error", args))
                self.__logfile.flush()
            if self.__enable_console and sys.stdout is not None:
                sys.stdout.write(_format("error", args))

    def warning(self, *args):
        """ Write warning"""
        if LEVELS["warning"] >= LEVELS[self.__level]:
            message = _format("", args)
            if self.__iface:
                self.__iface.messageBar().pushWarning("PisteCreator", message)
            if self.__logfile:
                self.__logfile.write(_format("warning", args))
                self.__logfile.flush()
            if self.__enable_console and sys.stdout is not None:
                sys.stdout.write(_format("warning", args))

    def notice(self, *args):
        """ Write notation"""
        if LEVELS["notice"] >= LEVELS[self.__level]:
            message = _format("", args)
            # we log too much notice in PisteCreator, we don't want theme in the message bar
            # if self.__iface:
            #    self.__iface.messageBar().pushInfo('PisteCreator', message)
            if self.__logfile:
                self.__logfile.write(_format("notice", args))
                self.__logfile.flush()
            if self.__enable_console and sys.stdout is not None:
                sys.stdout.write(_format("notice", args))

    def debug(self, *args):
        """ Write debug info"""
        if LEVELS["debug"] >= LEVELS[self.__level]:
            if self.__logfile:
                self.__logfile.write(_format("debug", args))
                self.__logfile.flush()
            if self.__enable_console and sys.stdout is not None:
                sys.stdout.write(_format("debug", args))

    def progress(self, message):
        """ Write progress

        :param message: message to write
        :type message: string"""
        from qgis.core import Qgis

        if self.__iface:
            progressMessageBar = self.__iface.messageBar().createMessage(message)
            progress = QGisProgressDisplay()
            progressMessageBar.layout().addWidget(progress.widget())
            self.__iface.messageBar().pushWidget(
                progressMessageBar, Qgis.Info, duration=1
            )
            return progress
        if self.__enable_console:
            sys.stdout.write("Progress: %s " % (message))
            return ConsoleProgressDisplay()
        return NullProgressDisplay()


logger = Logger()
