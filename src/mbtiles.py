#===============================================================================
#
#  Flatmap viewer and annotation tools
#
#  Copyright (c) 2019  David Brooks
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

import io
import os
import sqlite3

#===============================================================================

import mbutil as mb
from PIL import Image

#===============================================================================

class ExtractionError(Exception):
    pass

#===============================================================================

class MBTiles(object):
    def __init__(self, filepath, force=False, silent=False):
        self._silent = silent
        if force and os.path.exists(filepath):
            os.remove(filepath)
        self._connnection = mb.mbtiles_connect(filepath, self._silent)
        self._cursor = self._connnection.cursor()
        mb.optimize_connection(self._cursor)
        mb.mbtiles_setup(self._cursor)

    def close(self, compress=False):
        if compress:
            mb.compression_prepare(self._cursor, self._silent)
            mb.compression_do(self._cursor, self._connnection, 256, self._silent)
            mb.compression_finalize(self._cursor, self._connnection, self._silent)
        mb.optimize_database(self._connnection, self._silent)

    def save_metadata(self, **metadata):
        for name, value in metadata.items():
            self._cursor.execute('insert into metadata (name, value) values (?, ?)',
                                 (name, value))

    def get_tile(self, zoom, x, y):
        rows = self._cursor.execute("""select tile_data from tiles
                                          where zoom_level=? and tile_column=? and tile_row=?;""",
                                             (zoom, x, mb.flip_y(zoom, y)))
        data = rows.fetchone()
        if not data: raise ExtractionError()
        return Image.open(io.BytesIO(data[0]))

    def save_tile(self, zoom, x, y, image):
        output = io.BytesIO()
        image.save(output, format='PNG')
        self._cursor.execute("""insert into tiles (zoom_level, tile_column, tile_row, tile_data)
                                           values (?, ?, ?, ?);""",
                                                  (zoom, x, mb.flip_y(zoom, y), sqlite3.Binary(output.getvalue()))
                            )

#===============================================================================
