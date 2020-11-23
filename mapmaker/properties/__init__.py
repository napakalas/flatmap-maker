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

import json

#===============================================================================

from mapmaker.knowledgebase.labels import AnatomicalMap
from .pathways import Pathways

#===============================================================================

class JsonProperties(object):
    def __init__(self, properties_file, anatomical_map_file, label_database):
        self.__anatomical_map = AnatomicalMap(anatomical_map_file, label_database)
        self.__properties_by_class = {}
        self.__properties_by_id = {}
        properties_dict = {}
        if properties_file is not None:
            with open(properties_file) as fp:
                try:
                    properties_dict = json.loads(fp.read())
                except json.decoder.JSONDecodeError as err:
                    raise ValueError('Error in properties file, {}'.format(err))
        self.__set_properties(properties_dict.get('features', []))
        self.__pathways = Pathways(properties_dict.get('paths', []))

    def __set_properties(self, features_list):
        for feature in features_list:
            if 'class' in feature:
                cls = feature['class']
                properties = feature.get('properties', {})
                if cls in self.__properties_by_class:
                    self.__properties_by_class[cls].update(properties)
                else:
                    self.__properties_by_class[cls] = properties
            if 'id' in feature:
                id = feature['id']
                properties = feature.get('properties', {})
                if id in self.__properties_by_id:
                    self.__properties_by_id[id].update(properties)
                else:
                    self.__properties_by_id[id] = properties

    @property
    def resolved_pathways(self):
        return self.__pathways.resolved_pathways

    def resolve_pathways(self, id_map, class_map):
    #=============================================
        if self.__pathways is not None:
            self.__pathways.resolve_pathways(id_map, class_map)

    def update_properties(self, feature):
    #====================================
        properties = {}
        cls = feature.get_property('class')
        if cls is not None:
            properties.update(self.__anatomical_map.properties(cls))
            properties.update(self.__properties_by_class.get(cls, {}))
            if self.__pathways is not None:
                properties.update(self.__pathways.add_path(cls))
        id = feature.get_property('id')
        if id is not None:
            properties.update(self.__properties_by_id.get(id, {}))
            if self.__pathways is not None:
                properties.update(self.__pathways.add_path(id))
        if 'marker' in properties:
            properties['type'] = 'marker'
            if 'datasets' in properties:
                properties['kind'] = 'dataset'
            elif 'scaffolds' in properties:
                properties['kind'] = 'scaffold'
            elif 'simulations' in properties:
                properties['kind'] = 'simulation'
        if 'models' in properties and 'label' not in properties:
            properties['label'] = self.__anatomical_map.label(properties['models'])
        for key, value in properties.items():
            feature.set_property(key, value)

#===============================================================================