#===============================================================================
#
#  Flatmap viewer and annotation tools
#
#  Copyright (c) 2019 - 2023  David Brooks
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

import argparse

#===============================================================================

from mapmaker import MapMaker, __version__
from mapmaker.utils import log

#===============================================================================

def arg_parser():
    parser = argparse.ArgumentParser(description='Generate a flatmap from its source manifest.')

    parser.add_argument('-v', '--version', action='version', version=__version__)

    log_options = parser.add_argument_group('Logging')
    log_options.add_argument('--log', dest='logFile', metavar='LOG_FILE',
                        help="Append messages to a log file")
    log_options.add_argument('--show-deprecated', dest='showDeprecated', action='store_true',
                        help='Issue a warning for deprecated markup properties')
    log_options.add_argument('--silent', action='store_true',
                        help='Suppress all messages to screen')
    log_options.add_argument('--verbose', action='store_true',
                        help="Show progress bars")

    generation_options = parser.add_argument_group('Map generation')
    generation_options.add_argument('--clean', action='store_true',
                        help="Remove all files from generated map's directory before generating the new map")
    generation_options.add_argument('--clean-connectivity', dest='cleanConnectivity', action='store_true',
                        help='Refresh local connectivity knowledge from SciCrunch')
    generation_options.add_argument('--background-tiles',  dest='backgroundTiles', action='store_true',
                        help="Generate image tiles of map's layers (may take a while...)")
    generation_options.add_argument('--id', metavar='ID',
                        help='Set explicit ID for flatmap, overriding manifest')
    generation_options.add_argument('--ignore-git', dest='ignoreGit', action='store_true',
                        help="Don't check that sources are committed into git")
    generation_options.add_argument('--invalid-neurons', dest='invalidNeurons', action='store_true',
                        help="Include functional connectivity neurons that aren't known in SCKAN")
    generation_options.add_argument('--publish', metavar='SPARC_DATASET',
                        help="Create a SPARC Dataset containing the map's sources and the generated map")
    generation_options.add_argument('--sckan-version', dest='sckanVersion', choices=['production', 'staging'],
                        help="Overide version of SCKAN specified by map's manifest")

    debug_options = parser.add_argument_group('Diagnostics')
    debug_options.add_argument('--authoring', action='store_true',
                        help="For use when checking a new map: highlight incomplete features; show centreline network; no image tiles; no neuron paths; etc")
    debug_options.add_argument('--debug', action='store_true',
                        help='See `log.debug()` messages in log')
    debug_options.add_argument('--only-networks', dest='onlyNetworks', action='store_true',
                        help='Only output features that are part of a centreline network')
    debug_options.add_argument('--save-drawml', dest='saveDrawML', action='store_true',
                        help="Save a slide's DrawML for debugging")
    debug_options.add_argument('--save-geojson', dest='saveGeoJSON', action='store_true',
                        help='Save GeoJSON files for each layer')
    debug_options.add_argument('--tippecanoe', dest='showTippe', action='store_true',
                        help='Show command used to run Tippecanoe')

    zoom_options = parser.add_argument_group('Zoom level')
    zoom_options.add_argument('--initial-zoom', dest='initialZoom', metavar='N', type=int, default=4,
                        help='Initial zoom level (defaults to 4)')
    zoom_options.add_argument('--max-zoom', dest='maxZoom', metavar='N', type=int, default=10,
                        help='Maximum zoom level (defaults to 10)')
    zoom_options.add_argument('--min-zoom', dest='minZoom', metavar='N', type=int, default=2,
                        help='Minimum zoom level (defaults to 2)')

    misc_options = parser.add_argument_group('Miscellaneous')
    misc_options.add_argument('--export-identifiers', dest='exportIdentifiers', metavar='EXPORT_FILE',
                        help='Export identifiers and anatomical terms of features as JSON')
    misc_options.add_argument('--export-neurons', dest='exportNeurons', metavar='EXPORT_FILE',
                        help='Export details of functional connectivity neurons as JSON')
    misc_options.add_argument('--export-svg', dest='exportSVG', metavar='EXPORT_FILE',
                        help='Export Powerpoint sources as SVG')
    misc_options.add_argument('--single-file', dest='singleFile', choices=['celldl', 'svg'],
                        help='Source is a single file of the designated type, not a flatmap manifest')

    required = parser.add_argument_group('Required arguments')
    required.add_argument('--output', required=True,
                        help='Base directory for generated flatmaps')
    required.add_argument('--source', required=True,
                        help='URL or path of a flatmap manifest')
    return parser

#===============================================================================

def main():
    parser = arg_parser()
    args = parser.parse_args()
    try:
        mapmaker = MapMaker({k:v for k, v in vars(args).items() if v not in [None, False]})
        mapmaker.make()
    except Exception as error:
        msg = str(error)
        log.exception(msg)

#===============================================================================

if __name__ == '__main__':
    main()

#===============================================================================
