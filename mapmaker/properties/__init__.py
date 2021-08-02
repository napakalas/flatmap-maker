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

from collections import defaultdict

#===============================================================================

from mapmaker.sources.apinatomy import ApiNATOMY
from mapmaker.utils import FilePath

from .anatomicalmap import AnatomicalMap
from .pathways import Pathways

#===============================================================================

class ManifestProperties(object):
    def __init__(self, flatmap, manifest):
        self.__anatomical_map = AnatomicalMap(manifest.anatomical_map)
        self.__properties_by_class = {}
        self.__properties_by_id = {}
        if manifest.properties is None:
            properties_dict = {}
        else:
            properties_dict = FilePath(manifest.properties).get_json()
        self.__set_properties(properties_dict.get('features', []))
        self.__model_to_features = defaultdict(set)

        # Load path definitions
        self.__pathways = Pathways(flatmap, properties_dict.get('paths', []))
        for connectivity_source in manifest.connectivity:
            connectivity = FilePath(connectivity_source).get_json()
            self.__pathways.add_connectivity(connectivity)

        # Load routes from ApiNATOMY
        if manifest.soma_processes is not None:
            soma_processes = FilePath(manifest.soma_processes['href']).get_json()
            for model in manifest.soma_processes['models']:
                self.__pathways.add_apinatomy_routes(ApiNATOMY(soma_processes, model))

    @property
    def anatomical_ids(self):
        anatomical_ids = set()
        for ids in self.__features_by_model.values():
            anatomical_ids.update(ids)
        return list(anatomical_ids)

    @property
    def resolved_pathways(self):
        return self.__pathways.resolved_pathways

    def __set_properties(self, features_list):
    #=========================================
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

    def add_nerve_tracks(self, nerve_tracks):
    #========================================
        if self.__pathways is not None:
            self.__pathways.add_nerve_tracks(nerve_tracks)

    def resolve_pathways(self, id_map, class_map):
    #=============================================
        if self.__pathways is not None:
            self.__pathways.resolve_pathways(id_map, class_map, self.__model_to_features)

    def update_properties(self, properties):
    #=======================================
        cls = properties.get('class')
        if cls is not None:
            properties.update(self.__anatomical_map.properties(cls))
            properties.update(self.__properties_by_class.get(cls, {}))
            if self.__pathways is not None:
                properties.update(self.__pathways.add_line_or_nerve(cls))
        id = properties.get('id')
        if id is not None:
            properties.update(self.__properties_by_id.get(id, {}))
            if self.__pathways is not None:
                properties.update(self.__pathways.add_line_or_nerve(id))
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
        return properties

    def update_feature_properties(self, feature):
    #============================================
        self.update_properties(feature.properties)
        if feature.models is not None:
            self.__model_to_features[feature.models].add(feature)

#===============================================================================
