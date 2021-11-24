"""AMDA_Webservice utility functions. This module defines some conversion functions specific to AMDA_Webservice, mainly
conversion procedures for parsing CSV and VOTable data.

"""
import os
import datetime
from urllib.request import urlopen
from speasy.products.variable import SpeasyVariable
import pandas as pds
import numpy as np

from speasy.products.timetable import TimeTable
from speasy.products.catalog import Catalog, Event
from speasy.core.datetime_range import DateTimeRange


def load_csv(filename):
    """Load a CSV file

    :param filename: CSV filename
    :type filename: str
    :return: CSV contents
    :rtype: SpeasyVariable
    """
    if '://' not in filename:
        filename = f"file://{os.path.abspath(filename)}"
    with urlopen(filename) as csv:
        line = csv.readline().decode()
        meta = {}
        y = None
        while line[0] == '#':
            if ':' in line:
                key, value = line[1:].split(':', 1)
                meta[key.strip()] = value.strip()
            line = csv.readline().decode()
        columns = [col.strip() for col in meta['DATA_COLUMNS'].split(', ')[:]]
        with urlopen(filename) as f:
            data = pds.read_csv(f, comment='#', delim_whitespace=True, header=None, names=columns).values.transpose()
        time, data = data[0], data[1:].transpose()
        if "PARAMETER_TABLE_MIN_VALUES[1]" in meta:
            min_v = np.array([float(v) for v in meta["PARAMETER_TABLE_MIN_VALUES[1]"].split(',')])
            max_v = np.array([float(v) for v in meta["PARAMETER_TABLE_MAX_VALUES[1]"].split(',')])
            y = (max_v + min_v) / 2.
        elif "PARAMETER_TABLE_MIN_VALUES[0]" in meta:
            min_v = np.array([float(v) for v in meta["PARAMETER_TABLE_MIN_VALUES[0]"].split(',')])
            max_v = np.array([float(v) for v in meta["PARAMETER_TABLE_MAX_VALUES[0]"].split(',')])
            y = (max_v + min_v) / 2.
        return SpeasyVariable(time=time, data=data, meta=meta, columns=columns[1:], y=y)


def _build_event(data, colnames):
    return Event(datetime.datetime.strptime(data[0], "%Y-%m-%dT%H:%M:%S.%f"),
                 datetime.datetime.strptime(data[1], "%Y-%m-%dT%H:%M:%S.%f"),
                 {name: value for name, value in zip(colnames[2:], data[2:])})


def load_timetable(filename) -> TimeTable:
    """Load a timetable file
    :param filename: filename
    :type filename: str
    :return: AMDA_Webservice timetable
    :rtype: speasy.common.timetable.TimeTable

    """
    if '://' not in filename:
        filename = f"file://{os.path.abspath(filename)}"
    with urlopen(filename) as votable:
        # save the timetable as a dataframe, speasy.common.SpeasyVariable
        # get header data first
        from astropy.io.votable import parse as parse_votable
        import io
        votable = parse_votable(io.BytesIO(votable.read()))
        name = next(filter(lambda e: 'Name' in e, votable.description.split(';\n'))).split(':')[-1]
        # convert astropy votable structure to SpeasyVariable
        tab = votable.get_first_table()
        # prepare data
        data = tab.array.tolist()
        dt_ranges = [DateTimeRange(datetime.datetime.strptime(t0, "%Y-%m-%dT%H:%M:%S.%f"),
                                   datetime.datetime.strptime(t1, "%Y-%m-%dT%H:%M:%S.%f")) for (t0, t1) in
                     data]
        var = TimeTable(name=name, meta={}, dt_ranges=dt_ranges)
        return var


def load_catalog(filename) -> Catalog:
    """Load a timetable file

    :param filename: filename
    :type filename: str
    :return: speasy.amda.timetable.Catalog
    :rtype: speasy.amda.timetable.Catalog

    """
    if '://' not in filename:
        filename = f"file://{os.path.abspath(filename)}"
    with urlopen(filename) as votable:
        # save the timetable as a dataframe, speasy.common.SpeasyVariable
        # get header data first
        from astropy.io.votable import parse as parse_votable
        import io
        votable = parse_votable(io.BytesIO(votable.read()))
        # convert astropy votable structure to SpeasyVariable
        tab = votable.get_first_table()
        name = next(filter(lambda e: 'Name' in e, votable.description.split(';\n'))).split(':')[-1]
        colnames = list(map(lambda f: f.name, tab.fields))
        data = tab.array.tolist()
        events = [_build_event(line, colnames) for line in data]
        var = Catalog(name=name, meta={}, events=events)
        return var


def get_parameter_args(start_time: datetime, stop_time: datetime, product: str, **kwargs):
    """Get parameter arguments

    :param start_time: parameter start time
    :type start_time: datetime.datetime
    :param stop_time: parameter stop time
    :type stop_time: datetime.datetime
    :return: parameter arguments in dictionary
    :rtype: dict
    """
    return {'path': f"amda/{product}", 'start_time': f'{start_time.isoformat()}',
            'stop_time': f'{stop_time.isoformat()}'}
