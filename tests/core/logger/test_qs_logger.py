#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Tests for cloudshell.core.logger.qs_logger
"""

import logging
import os
import re
import shutil

from mock import MagicMock
from unittest import TestCase

from cloudshell.core.logger import qs_logger
from cloudshell.core.logger.interprocess_logger import MultiProcessingLog

CUR_DIR = os.path.dirname(__file__)
full_settings = MagicMock(return_value={'LOG_PATH': '../../Logs',
                                        'TIME_FORMAT': '%d-%b-%Y--%H-%M-%S',
                                        'LOG_LEVEL': 'INFO',
                                        'FORMAT': '%(asctime)s [%(levelname)s]: %(name)s %(module)s - %(funcName)-20s %(message)s'})

cut_settings = MagicMock(return_value={'TIME_FORMAT': '%d-%b-%Y--%H-%M-%S',
                                       'LOG_LEVEL': 'INFO',
                                       'FORMAT': '%(asctime)s [%(levelname)s]: %(name)s %(module)s - %(funcName)-20s %(message)s'})


class TestQSLogger(TestCase):
    _LOGS_PATH = os.path.join(os.path.dirname(__file__), "../../Logs")

    def setUp(self):
        """ Remove all existing test Logs folders before each suite """
        self.qs_conf = os.getenv("QS_CONFIG")
        self.log_path = os.getenv("LOG_PATH")

        os.environ["QS_CONFIG"] = os.path.join(CUR_DIR, "config/test_qs_config.ini")
        os.environ["LOG_PATH"] = os.path.join(CUR_DIR, "../../Logs")

        if os.path.exists(self._LOGS_PATH):
            shutil.rmtree(self._LOGS_PATH)

    def tearDown(self):
        """ Close all existing logging handlers after each suite """
        if self.qs_conf:
            os.environ["QS_CONFIG"] = self.qs_conf
        elif "QS_CONFIG" in os.environ:
                del os.environ["QS_CONFIG"]

        if self.log_path:
            os.putenv("LOG_PATH", self.log_path)
        elif "LOG_PATH" in os.environ:
                del os.environ["LOG_PATH"]

        for logger in qs_logger._LOGGER_CONTAINER.values():
            for handler in logger.handlers:
                handler.close()

    def test_01_get_settings(self):
        """ Test suite for get_settings method """
        exp_response = {'LOG_PATH': '../../Logs',
                        'TIME_FORMAT': '%d-%b-%Y--%H-%M-%S',
                        'LOG_LEVEL': 'INFO',
                        'FORMAT': '%(asctime)s [%(levelname)s]: %(name)s %(module)s - %(funcName)-20s %(message)s'}

        self.assertEqual(qs_logger.get_settings(), exp_response)

    def test_02_get_accessible_log_path(self):
        """ Test suite for get_accessible_log_path method """
        path = qs_logger.get_accessible_log_path()
        self.assertTrue(re.search(r"Logs[\\/]Autoload[\\/]default--\d{2}-\w+-\d{4}--\d{2}-\d{2}-\d{2}\.log", path))
        self.assertTrue(os.path.dirname(path))

        path = qs_logger.get_accessible_log_path(qs_logger.get_accessible_log_path("reservation_id", "handler_name"))
        self.assertTrue(re.search(r"Logs[\\/]reservation_id[\\/]handler_name--\d{2}-\w+-\d{4}--\d{2}-\d{2}-\d{2}\.log", path))
        self.assertTrue(os.path.dirname(path))

        if "LOG_PATH" in os.environ:
            del os.environ["LOG_PATH"]
        qs_logger.get_settings = cut_settings
        self.assertIsNone(qs_logger.get_accessible_log_path())

    def test_03_get_qs_logger(self):
        """ Test suite for get_qs_logger method """
        qs_logger.get_settings = full_settings
        self.assertTrue(isinstance(qs_logger.get_qs_logger().handlers[0], MultiProcessingLog))
        self.assertTrue(isinstance(qs_logger.get_qs_logger(log_group='test1').handlers[0], MultiProcessingLog))

        if "LOG_PATH" in os.environ:
            del os.environ["LOG_PATH"]
        qs_logger.get_settings = cut_settings
        self.assertTrue(isinstance(qs_logger.get_qs_logger(log_group='test2').handlers[0], logging.StreamHandler))

        self.assertEqual(sorted(qs_logger._LOGGER_CONTAINER.keys()), sorted(["Ungrouped", "test1", "test2"]))

    def test_04_normalize_buffer(self):
        """ Test suite for normalize_buffer method """
        self.assertEqual(qs_logger.normalize_buffer("\033[1;32;40mGreenOnWhiteBack "
                                                    "\033[4;31mRedUnderscore "
                                                    "\033[93mYellow"), "GreenOnWhiteBack RedUnderscore Yellow")
        self.assertEqual(qs_logger.normalize_buffer("\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff"), "---")
        self.assertEqual(qs_logger.normalize_buffer("\r\n \n\r"), "\n \n\r")

        self.assertEqual(qs_logger.normalize_buffer(("test", "tuple")), "('test', 'tuple')")
        self.assertEqual(qs_logger.normalize_buffer({"test": "dict"}), "{'test': 'dict'}")
        self.assertEqual(qs_logger.normalize_buffer(u"unicode text"), "unicode text")
