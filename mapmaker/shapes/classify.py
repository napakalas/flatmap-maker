#===============================================================================
#
#  Flatmap viewer and annotation tools
#
#  Copyright (c) 2018 - 2024  David Brooks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#===============================================================================

from collections import defaultdict
from dataclasses import dataclass
from typing import DefaultDict, Iterable, Optional

#===============================================================================

import networkx as nx
from numpy import ndarray
from shapely.geometry.base import BaseGeometry
import shapely.prepared
import shapely.strtree

#===============================================================================

from mapmaker.flatmap.layers import PATHWAYS_TILE_LAYER
from mapmaker.settings import settings
from mapmaker.shapes import Shape, SHAPE_TYPE
from mapmaker.sources.fc_powerpoint.components import VASCULAR_KINDS
from mapmaker.utils import log

from .constants import COMPONENT_BORDER_WIDTH, CONNECTION_STROKE_WIDTH, MAX_LINE_WIDTH
from .line_finder import Line, LineFinder, XYPair
from .text_finder import TextFinder

#===============================================================================

"""

Mutually exclusive shape categories:

    parent: Shape
    children: list[Shape]
    overlapping: list[Shape]
    adjacent: list[Shape]

Shape types from size (area and aspect ratio) and geometry:

*   Component
*   Container
*   Boundary
*   Connection
*   Text

"""

#===============================================================================

@dataclass
class ConnectionEnd:
    shape: Shape
    index: int

#===============================================================================

class LineString:
    def __init__(self, geometry: BaseGeometry):
        self.__coords = list(geometry.coords)

    @property
    def coords(self):
        return self.__coords

    @property
    def line_string(self):
        return shapely.LineString(self.__coords)

    def end_line(self, end: int) -> Line:
        if end == 0:
            return Line.from_coords((self.__coords[0], self.__coords[1]))
        else:
            return Line.from_coords((self.__coords[-2], self.__coords[-1]))

#===============================================================================

class ShapeClassifier:
    def __init__(self, shapes: list[Shape], map_area: float, metres_per_pixel: float):
        self.__shapes = list(shapes)
        self.__shapes_by_type: DefaultDict[SHAPE_TYPE, list[Shape]] = defaultdict(list[Shape])
        self.__geometry_to_shape: dict[int, Shape] = {}
        self.__line_finder = LineFinder(metres_per_pixel)
        self.__text_finder = TextFinder(metres_per_pixel)
        self.__connection_ends: list[shapely.Polygon] = []
        self.__connection_ends_to_shape: dict[int, ConnectionEnd] = {}
        self.__max_line_width = metres_per_pixel*MAX_LINE_WIDTH
        connection_joiners: list[Shape] = []
        geometries = []
        for n, shape in enumerate(shapes):
            geometry = shape.geometry
            area = geometry.area
            self.__bounds = geometry.bounds
            width = abs(self.__bounds[2] - self.__bounds[0])
            height = abs(self.__bounds[3] - self.__bounds[1])
            bbox_coverage = (width*height)/map_area
            if width > 0 and height > 0:
                aspect = min(width, height)/max(width, height)
                coverage = area/(width*height)
            else:
                aspect = 0
                coverage = 1
            shape.properties.update({
                'area': area,
                'aspect': aspect,
                'coverage': coverage,
                'bbox-coverage': bbox_coverage,
            })
            if shape.shape_type == SHAPE_TYPE.UNKNOWN:
                if bbox_coverage > 0.001 and geometry.geom_type == 'MultiPolygon':
                    shape.properties['shape-type'] = SHAPE_TYPE.BOUNDARY
                elif ((n < len(shapes) - 1) and shapes[n+1].shape_type == SHAPE_TYPE.TEXT
                  and coverage < 0.5 and bbox_coverage < 0.001):
                    shape.properties['exclude'] = True
                elif coverage < 0.4 or 'LineString' in geometry.geom_type:
                    if not self.__add_connection(shape):
                        log.warning('Cannot extract line from polygon', shape=shape.id)
                elif bbox_coverage > 0.001 and coverage > 0.9:
                    shape.properties['shape-type'] = SHAPE_TYPE.CONTAINER
                elif bbox_coverage < 0.0005 and aspect > 0.9 and 0.7 < coverage <= 0.85:
                    shape.properties['shape-type'] = SHAPE_TYPE.COMPONENT
                elif bbox_coverage < 0.001 and coverage > 0.85:
                    shape.properties['shape-type'] = SHAPE_TYPE.COMPONENT
                elif len(shape.geometry.boundary.coords) == 4:      # A triangle
                    connection_joiners.append(shape)
                elif not self.__add_connection(shape):
                    log.warning('Unclassifiable shape', shape=shape.id)
                    shape.properties['colour'] = 'yellow'
            if not shape.properties.get('exclude', False):
                self.__shapes_by_type[shape.shape_type].append(shape)
                if shape.shape_type != SHAPE_TYPE.CONNECTION:
                    self.__geometry_to_shape[id(shape.geometry)] = shape
                    geometries.append(shape.geometry)
                    shape.properties['stroke-width'] = COMPONENT_BORDER_WIDTH

        connection_index = shapely.strtree.STRtree(self.__connection_ends)

        joined_connection_graph = nx.Graph()
        for joiner in connection_joiners:
            ends = connection_index.query_nearest(joiner.geometry) #, max_distance=10*metres_per_pixel*MAX_LINE_WIDTH)
            if len(ends) == 2:
                joiner.properties['exclude'] = True
                (connection_0, connection_1) = self.__extend_joined_connections(ends)
                joined_connection_graph.add_edge(connection_0, connection_1)
            else:
                joiner.properties['colour'] = 'yellow'
                joiner.properties['stroke'] = 'red'
                joiner.properties['stroke-width'] = COMPONENT_BORDER_WIDTH
                joiner.geometry = joiner.geometry.buffer(self.__max_line_width)
        for joined_connection in nx.connected_components(joined_connection_graph):
            connections = list(joined_connection)
            connected_line = shapely.line_merge(shapely.unary_union([conn.geometry for conn in connections]))
            assert connected_line.geom_type == 'LineString', f'Cannot join connections: {[conn.id for conn in connections]}'
            connections[0].geometry = connected_line
            for connection in connections[1:]:
                if connection.properties.get('directional', False):
                    connections[0].properties['directional'] = True
                connection.properties['exclude'] = True

        self.__str_index = shapely.strtree.STRtree(geometries)
        geometries: list[BaseGeometry] = self.__str_index.geometries     # type: ignore
        parent_child = []
        for geometry in geometries:
            if geometry.area > 0:
                parent = self.__geometry_to_shape[id(geometry)]
                for child in [self.__geometry_to_shape[id(geometries[c])]
                                for c in self.__str_index.query(geometry, predicate='contains_properly')
                                    if geometries[c].area > 0]:
                    parent_child.append((parent, child))
        last_child_id = None
        for (parent, child) in sorted(parent_child, key=lambda s: (s[1].id, s[0].geometry.area)):
            if child.id != last_child_id:
                child.add_parent(parent)
                last_child_id = child.id

    def __add_connection(self, shape: Shape) -> bool:
    #================================================
        if 'Polygon' in shape.geometry.geom_type:
            if (line := self.__line_finder.get_line(shape)) is None:
                shape.properties['exclude'] = not settings.get('authoring', False)
                shape.properties['colour'] = 'yellow'
                return False
            shape.geometry = line
            kind = VASCULAR_KINDS.lookup(shape.properties.get('fill'))
        else:
            kind = VASCULAR_KINDS.lookup(shape.properties.get('stroke'))
        assert shape.geometry.geom_type == 'LineString', f'Connection not a LineString: {shape.id}'
        line_ends: shapely.geometry.base.GeometrySequence[shapely.MultiPoint] = shape.geometry.boundary.geoms  # type: ignore
        self.__append_connection_ends(line_ends[0], shape, 0)
        self.__append_connection_ends(line_ends[1], shape, -1)
        if kind is not None:
            shape.properties['kind'] = kind
        shape.properties['shape-type'] = SHAPE_TYPE.CONNECTION
        shape.properties['tile-layer'] = PATHWAYS_TILE_LAYER
        shape.properties['stroke-width'] = CONNECTION_STROKE_WIDTH
        shape.properties['type'] = 'line'  ## or 'line-dash'
        return True

    def __append_connection_ends(self, end: shapely.Point, shape: Shape, index: int):
    #================================================================================
        end_circle = end.buffer(self.__max_line_width)
        self.__connection_ends.append(end_circle)
        self.__connection_ends_to_shape[id(end_circle)] = ConnectionEnd(shape, index)

    def __extend_joined_connections(self, ends: ndarray) -> tuple[Shape, Shape]:
    #===========================================================================
        # Extend connection line ends so that they touch...

        c0 = self.__connection_ends_to_shape[id(self.__connection_ends[ends[0]])]
        c1 = self.__connection_ends_to_shape[id(self.__connection_ends[ends[1]])]
        l0 = LineString(c0.shape.geometry)
        l0_end = l0.end_line(c0.index)
        l1 = LineString(c1.shape.geometry)
        l1_end = l1.end_line(c1.index)
        pt = l0_end.intersection(l1_end, extend=True)
        if pt is not None:
            l0.coords[c0.index] = pt.coords
            c0.shape.geometry = l0.line_string
            l1.coords[c1.index] = pt.coords
            c1.shape.geometry = l1.line_string
        return (c0.shape, c1.shape)

    def classify(self) -> list[Shape]:
    #=================================
        for shape in self.__shapes:
            if shape.shape_type in [SHAPE_TYPE.COMPONENT, SHAPE_TYPE.CONTAINER]:
                if (label := self.__text_finder.get_text(shape)) is not None:
                    shape.properties['label'] = label
        return [s for s in self.__shapes if not s.exclude]

#===============================================================================
