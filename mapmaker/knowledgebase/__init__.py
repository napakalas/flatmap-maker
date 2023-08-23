#===============================================================================
#
#  Flatmap viewer and annotation tools
#
#  Copyright (c) 2019-21  David Brooks
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

from typing import Any, Optional

#===============================================================================

# Exports
from flatmapknowledge import KnowledgeStore

from npoexplorer import NPOExplorer, ENDPOINT_BLAZEGRAPH, ENDPOINT_STARDOG, NPO_TO_SCKAN_MODEL
class NPOKnowledgeStore(NPOExplorer):
    def __init__(self):
        super().__init__(endpoint=ENDPOINT_STARDOG)

    def add_flatmap(self, flatmap):
        pass

#===============================================================================

from mapmaker.settings import settings

#===============================================================================

class AnatomicalNode(tuple):
    def __new__ (cls, termlist: list):
        return super().__new__(cls, (termlist[0], tuple(termlist[1])))

    @property
    def name(self) -> str:
        return '/'.join(reversed((self[0],) + self[1]))

    @property
    def full_name(self) -> str:
        if len(self[1]) == 0:
            return entity_name(self[0])
        else:
            layer_names = ', '.join([entity_name(entity) for entity in self[1] if entity is not None])
            return f'{entity_name(self[0])} in {layer_names}'

    def normalised(self):
        return (self[0], *self[1])

    ## We need to get the label for each anatomical term in the list of nodes
    ## as they may be looked up by the viewer in upstream/downstream code...

#===============================================================================

def connectivity_models():
    models = settings['KNOWLEDGE_STORE'].connectivity_models()
    if isinstance(settings['KNOWLEDGE_STORE'], NPOKnowledgeStore):
        models = {NPO_TO_SCKAN_MODEL[model]:val for model, val in models.items()}
    return models


def get_label(entity: str) -> str:
    return get_knowledge(entity).get('label', entity)

def get_knowledge(entity: str) -> dict[str, Any]:
    return settings['KNOWLEDGE_STORE'].entity_knowledge(entity)

def sckan_build() -> Optional[dict]:
    if isinstance(settings['KNOWLEDGE_STORE'], KnowledgeStore):
        if (scicrunch := settings['KNOWLEDGE_STORE'].scicrunch) is not None:
            return scicrunch.sckan_build()
    elif isinstance(settings['KNOWLEDGE_STORE'], NPOKnowledgeStore):
        build = {'created': settings['KNOWLEDGE_STORE'].metadata('NPO')}
        return build

#===============================================================================

def entity_name(entity: Optional[str]) -> str:
    if entity is None:
        return 'None'
    return get_label(entity)

#===============================================================================
