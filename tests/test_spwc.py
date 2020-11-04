#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `spwc` package."""
import unittest
from datetime import datetime, timezone
import spwc
from ddt import ddt, data


@ddt
class GetData(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @data(
        {
            "path": "cdaweb/MMS2_SCM_SRVY_L2_SCSRVY/mms2_scm_acb_gse_scsrvy_srvy_l2",
            "start_time": datetime(2016, 6, 1, tzinfo=timezone.utc),
            "stop_time": datetime(2016, 6, 1, 0, 10, tzinfo=timezone.utc),
            "disable_proxy": True
        },
        {
            "path": "cdaweb/THA_L2_FGM/tha_fgl_gsm",
            "start_time": datetime(2014, 6, 1, tzinfo=timezone.utc),
            "stop_time": datetime(2014, 6, 1, 0, 10, tzinfo=timezone.utc),
            "disable_proxy": True
        },
        {
            "path": "amda/c1_hia_prest",
            "start_time": datetime(2016, 1, 8, 1, 0, 0, tzinfo=timezone.utc),
            "stop_time": datetime(2016, 1, 8, 1, 0, 10, tzinfo=timezone.utc),
            "disable_proxy": True
        },
        {
            "path": "amda/c1_b_gsm",
            "start_time": datetime(2006, 1, 8, 1, 0, 0, tzinfo=timezone.utc),
            "stop_time": datetime(2006, 1, 8, 1, 0, 10, tzinfo=timezone.utc),
            "disable_proxy": True
        },
        {
            "path": "sscweb/moon",
            "start_time": datetime(2006, 1, 8, 1, 0, 0, tzinfo=timezone.utc),
            "stop_time": datetime(2006, 1, 8, 10, 0, 0, tzinfo=timezone.utc)
        }
    )
    def test_get_variable(self, kw):
        result = spwc.get_data(**kw,
                               disable_cache=True)
        self.assertIsNotNone(result)
        self.assertGreater(len(result),0)
