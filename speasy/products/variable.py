import numpy as np
import pandas as pds
from datetime import datetime
from typing import List, Optional, Dict
from speasy.plotting import Plot
from speasy.core.data_containers import DataContainer, VariableTimeAxis, VariableAxis, _to_index
from copy import deepcopy

import astropy.units
import astropy.table


class SpeasyVariable(object):
    """SpeasyVariable object. Base class for storing variable data.

    Attributes
    ----------
    time: numpy.ndarray
        time vector (x-axis data)
    values: numpy.ndarray
        data
    meta: Optional[dict]
        metadata
    columns: Optional[List[str]]
        column names
    axes: Optional[List[np.ndarray]]
        Collection composed of time axis plus eventual additional axes according to values' shape

    Methods
    -------
    view:
        Return view of the current variable within the desired :data:`time_range`
    to_dataframe:
        Convert the variable to a pandas.DataFrame object
    plot:
        Plot the data with matplotlib

    """
    __slots__ = ['__values_container', '__columns', '__axes']

    def __init__(self, axes: List[VariableAxis or VariableTimeAxis], values: DataContainer,
                 columns: Optional[List[str]] = None):
        if not isinstance(axes[0], VariableTimeAxis):
            raise TypeError(f"axes[0] must be a VariableTimeAxis instance, got {type(axes[0])}")
        if axes[0].shape[0] != values.shape[0]:
            raise ValueError(
                f"Time and data must have the same length, got time:{len(axes[0])} and data:{len(values)}")

        self.__columns = list(map(str.strip, columns or []))
        if len(values.values.shape) == 1:
            values.reshape((values.shape[0], 1))  # to be consistent with pandas

        self.__values_container = values
        self.__axes = axes

    def view(self, index_range: slice):
        """Return view of the current variable within the desired :data:`time_range`.

        Parameters
        ----------
        index_range: slice
            index range

        Returns
        -------
        speasy.common.variable.SpeasyVariable
            view of the variable on the given range
        """
        return SpeasyVariable(axes=[axis[index_range] if axis.is_time_dependent else axis for axis in self.__axes],
                              values=self.__values_container[index_range], columns=self.columns)

    def filter_columns(self, columns: List[str]):
        indexes = list(map(lambda v: self.__columns.index(v), columns))
        return SpeasyVariable(axes=deepcopy(self.__axes),
                              values=DataContainer(
                                  is_time_dependent=self.__values_container.is_time_dependent,
                                  name=self.__values_container.name,
                                  meta=deepcopy(self.__values_container.meta),
                                  values=self.__values_container.values[:, indexes]
                              ),
                              columns=columns)

    def __eq__(self, other: 'SpeasyVariable') -> bool:
        """Check if this variable equals another.

        Parameters
        ----------
        other: speasy.common.variable.SpeasyVariable
            another SpeasyVariable object to compare with

        Returns
        -------
        bool:
            True if all attributes are equal
        """
        return type(
            other) is SpeasyVariable and self.__axes == other.__axes and self.__values_container == other.__values_container

    def __len__(self):
        return len(self.__axes[0])

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self.view(slice(_to_index(key.start, self.time), _to_index(key.stop, self.time)))
        if type(key) in (list, tuple) and all(map(lambda v: type(v) is str, key)):
            return self.filter_columns(key)
        if type(key) is str and key in self.__columns:
            return self.filter_columns([key])
        raise ValueError(f"No idea how to slice SpeasyVariable with given value: {key}")

    def __setitem__(self, k, v: 'SpeasyVariable'):
        assert type(v) is SpeasyVariable
        self.__values_container[k] = v.__values_container
        for axis, src_axis in zip(self.__axes, v.__axes):
            if axis.is_time_dependent:
                axis[k] = src_axis

    @property
    def name(self):
        return self.__values_container.name

    @property
    def values(self):
        return self.__values_container.values

    @property
    def time(self):
        return self.__axes[0].values

    @property
    def meta(self):
        return self.__values_container.meta

    @property
    def axes(self):
        return self.__axes

    @property
    def axes_labels(self):
        return [axis.name for axis in self.__axes]

    @property
    def columns(self):
        return self.__columns

    @property
    def unit(self):
        return self.__values_container.unit

    def unit_applied(self, unit: str or None = None, copy=True) -> "SpeasyVariable":
        if copy:
            axes = deepcopy(self.__axes)
            values = deepcopy(self.__values_container)
            columns = deepcopy(self.__columns)
        else:
            axes = self.__axes
            values = self.__values_container
            columns = self.__columns
        return SpeasyVariable(axes=axes, values=values.unit_applied(unit), columns=columns)

    def to_astropy_table(self) -> astropy.table.Table:
        """Convert the variable to a astropy.Table object.

        Parameters
        ----------
        datetime_index: bool
            boolean indicating that the index is datetime

        Returns
        -------
        astropy.Table:
            Variable converted to astropy.Table
        """
        try:
            units = astropy.units.Unit(self.meta["UNITS"])
        except (ValueError, KeyError):
            units = None
        df = self.to_dataframe()
        umap = {c: units for c in df.columns}
        return astropy.table.Table.from_pandas(df, units=umap, index=True)

    def to_dataframe(self) -> pds.DataFrame:
        """Convert the variable to a pandas.DataFrame object.

        Parameters
        ----------
        Returns
        -------
        pandas.DataFrame:
            Variable converted to Pandas DataFrame
        """
        if len(self.__values_container.shape) != 2:
            raise ValueError(
                f"Cant' convert a SpeasyVariable with shape {self.__values_container.shape} to DataFrame, only 1D/2D variables are accepted")
        return pds.DataFrame(index=self.time, data=self.values, columns=self.__columns, copy=True)

    @staticmethod
    def from_dataframe(df: pds.DataFrame) -> 'SpeasyVariable':
        """Load from pandas.DataFrame object.

        Parameters
        ----------
        dr: pandas.DataFrame
            Input DataFrame to convert

        Returns
        -------
        SpeasyVariable:
            Variable created from DataFrame
        """
        if df.index.dtype == np.dtype('datetime64[ns]'):
            time = np.array(df.index)
        elif hasattr(df.index[0], 'timestamp'):
            time = np.array([np.datetime64(d.timestamp() * 1e9, 'ns') for d in df.index])
        else:
            raise ValueError("Can't convert DataFrame index to datetime64[ns] array")
        return SpeasyVariable(axes=[VariableTimeAxis(values=time, meta={})],
                              values=DataContainer(values=df.values, meta={}, name='Unknown'),
                              columns=list(df.columns))

    def to_dictionary(self) -> Dict[str, object]:
        return {
            'axes': [axis.to_dictionary() for axis in self.__axes],
            'values': self.__values_container.to_dictionary(),
            'columns': deepcopy(self.__columns)
        }

    @staticmethod
    def from_dictionary(dictionary: Dict[str, object] or None) -> 'SpeasyVariable' or None:
        if dictionary is not None:
            axes = dictionary['axes']
            axes = [VariableTimeAxis.from_dictionary(axes[0])] + [VariableAxis.from_dictionary(axis) for axis in
                                                                  axes[1:]]

            return SpeasyVariable(
                values=DataContainer.from_dictionary(dictionary['values']),
                axes=axes,
                columns=dictionary.get('columns', None)
            )
        else:
            return None

    @staticmethod
    def epoch_to_datetime64(epoch_array: np.array):
        return (epoch_array * 1e9).astype('datetime64[ns]')

    @property
    def plot(self, *args, **kwargs):
        """Plot the variable.

        See https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.plot.html

        """
        return Plot(values=self.__values_container, columns_names=self.columns, axes=self.axes)

    def replace_fillval_by_nan(self, inplace=False) -> 'SpeasyVariable':
        if inplace:
            res = self
        else:
            res = deepcopy(self)
        if 'FILLVAL' in res.meta:
            res.__values_container.replace_val_by_nan(res.meta['FILLVAL'])
        return res

    @staticmethod
    def reserve_like(other: 'SpeasyVariable', length: int = 0) -> 'SpeasyVariable':
        axes = []
        for axis in other.__axes:
            if axis.is_time_dependent:
                new_axis = type(axis).reserve_like(axis, length)
                axes.append(new_axis)
            else:
                axes.append(deepcopy(axis))
        return SpeasyVariable(values=DataContainer.reserve_like(other.__values_container, length), axes=axes,
                              columns=other.columns)


def to_dictionary(var: SpeasyVariable) -> Dict[str, object]:
    return var.to_dictionary()


def from_dictionary(dictionary: Dict[str, object] or None) -> SpeasyVariable or None:
    return SpeasyVariable.from_dictionary(dictionary)


def from_dataframe(df: pds.DataFrame) -> SpeasyVariable:
    """Convert a dataframe to SpeasyVariable.

    See Also
    --------
    SpeasyVariable.from_dataframe
    """
    return SpeasyVariable.from_dataframe(df)


def to_dataframe(var: SpeasyVariable) -> pds.DataFrame:
    """Convert a :class:`~speasy.common.variable.SpeasyVariable` to pandas.DataFrame.

    See Also
    --------
    SpeasyVariable.to_dataframe
    """
    return SpeasyVariable.to_dataframe(var)


def merge(variables: List[SpeasyVariable]) -> Optional[SpeasyVariable]:
    """Merge a list of :class:`~speasy.common.variable.SpeasyVariable` objects.

    Parameters
    ----------
    variables: List[SpeasyVariable]
        Variables to merge together

    Returns
    -------
    SpeasyVariable:
        Resulting variable from merge operation
    """
    if len(variables) == 0:
        return None
    sorted_var_list = [v for v in variables if (v is not None) and (len(v.time) > 0)]
    sorted_var_list.sort(key=lambda v: v.time[0])

    # drop variables covered by previous ones
    for prev, current in zip(sorted_var_list[:-1], sorted_var_list[1:]):
        if prev.time[-1] >= current.time[-1]:
            sorted_var_list.remove(current)

    # drop variables covered by next ones
    for current, nxt in zip(sorted_var_list[:-1], sorted_var_list[1:]):
        if nxt.time[0] == current.time[0] and nxt.time[-1] >= current.time[-1]:
            sorted_var_list.remove(current)

    if len(sorted_var_list) == 0:
        return SpeasyVariable.reserve_like(variables[0], length=0)

    overlaps = [np.where(current.time >= nxt.time[0])[0][0] if current.time[-1] >= nxt.time[0] else -1 for
                current, nxt
                in
                zip(sorted_var_list[:-1], sorted_var_list[1:])]

    dest_len = int(np.sum(
        [overlap if overlap != -1 else len(r.time) for overlap, r in zip(overlaps, sorted_var_list[:-1])]))
    dest_len += len(sorted_var_list[-1].time)

    result = SpeasyVariable.reserve_like(sorted_var_list[0], dest_len)

    pos = 0

    for r, overlap in zip(sorted_var_list, overlaps + [-1]):
        frag_len = len(r.time) if overlap == -1 else overlap
        result[pos:(pos + frag_len)] = r[0:frag_len]
        pos += frag_len
    return result
