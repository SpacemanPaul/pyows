from datetime import datetime, date, timedelta
from typing import List, Union
from dataclasses import dataclass

from ows.xml import ElementMaker, NameSpace, NameSpaceMap
from ows.util import isoformat
from ows.swe.v20 import Field, encode_data_record


PositionType = Union[str, int, float, datetime, date]
ResolutionType = Union[str, int, float, timedelta]


@dataclass
class RegularAxis:
    label: str
    index_label: str
    lower_bound: PositionType
    upper_bound: PositionType
    resolution: ResolutionType
    uom: str
    size: int


@dataclass
class IrregularAxis:
    label: str
    index_label: str
    positions: List[PositionType]
    uom: str

    @property
    def size(self):
        return len(self.positions)


AxisType = Union[RegularAxis, IrregularAxis]


@dataclass
class Grid:
    axes: List[AxisType]
    srs: str


ns_cis = NameSpace('http://www.opengis.net/cis/1.1/gml', 'cis')
nsmap = NameSpaceMap(ns_cis)

CIS = ElementMaker(namespace=ns_cis.uri, nsmap=nsmap)


def encode_position_value(value: PositionType):
    if isinstance(value, str):
        return value

    elif isinstance(value, datetime):
        return isoformat(value)

    return str(value)


def encode_axis_extent(axis: AxisType):
    return CIS('AxisExtent',
        axisLabel=axis.label,
        uomLabel=axis.uom,
        lowerBound=encode_position_value(
            axis.lower_bound
            if isinstance(axis, RegularAxis) else
            axis.positions[0]
        ),
        upperBound=encode_position_value(
            axis.upper_bound
            if isinstance(axis, RegularAxis) else
            axis.positions[-1]
        ),
    )


def encode_envelope(grid: Grid):
    return CIS('Envelope',
        *[
            encode_axis_extent(axis)
            for axis in grid.axes
        ],
        srsName=grid.srs,
        axisLabels=' '.join(axis.label for axis in grid.axes),
        srsDimension=str(len(grid.axes)),
    )


def encode_axis(axis: AxisType):
    if isinstance(axis, RegularAxis):
        return CIS('RegularAxis',
            axisLabel=axis.label,
            uomLabel=axis.uom,
            lowerBound=encode_position_value(axis.lower_bound),
            upperBound=encode_position_value(axis.upper_bound),
        )
    else:
        return CIS('IrregularAxis',
            *[
                CIS('C', encode_position_value(position))
                for position in axis.positions
            ],
            axisLabel=axis.label,
            uomLabel=axis.uom,
        )


def encode_domain_set(grid: Grid):
    return CIS('DomainSet',
        CIS('GeneralGrid',
            *([
                encode_axis(axis)
                for axis in grid.axes
            ] + [
                CIS('GridLimits',
                    *[
                        CIS('IndexAxis',
                            axisLabel=axis.index_label,
                            lowerBound=str(0),
                            upperBound=str(axis.size - 1)
                        )
                        for axis in grid.axes
                    ],
                    axisLabels=' '.join(
                        axis.index_label for axis in grid.axes
                    ),
                    srsName=f'http://www.opengis.net/def/crs/OGC/0/Index{len(grid.axes)}D'
                )
            ]),
            srsName=grid.srs,
            axisLabels=' '.join(
                axis.label for axis in grid.axes
            )
        )
    )

def encode_range_type(range_type: List[Field]):
    return CIS('RangeType',
        encode_data_record(range_type)
    )
