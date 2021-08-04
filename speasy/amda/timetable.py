"""AMDA Timetable definition. Serves a cosmetic need for now, functionality to be added in the future.
"""
import numpy as np

from speasy.common.variable import SpeasyVariable


class TimetableIndex:
    def __init__(self, uid, name):
        self.uid = uid
        self.name = name

    def __repr__(self):
        return f'<TimetableIndex: {self.name}, id: {self.uid}>'


class TimeTable(SpeasyVariable):
    """AMDA TimeTable container. Timetables contain two time columns one for the begining of an
    event and one for the end.
    """
    pass
    # def __init__(self, time=np.empty(0), data=np.empty((0, 1)), meta=None, columns=None):
    #    super().__init__(time=time,data=data,meta=meta,columns=columns)


class Catalog(TimeTable):
    """AMDA Catalog container. Catalogs are TimeTables with added columns.
    """
    pass
