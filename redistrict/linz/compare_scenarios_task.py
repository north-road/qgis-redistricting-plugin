"""
Compare scenarios task
"""
from typing import Optional

from qgis.PyQt.QtCore import QVariant

from qgis.core import (
    QgsTask,
    QgsVectorLayer,
    QgsVectorLayerFeatureSource,
    QgsFeatureRequest,
    QgsMemoryProviderUtils,
    QgsFields,
    QgsField,
    QgsFeatureSink,
    QgsFeature
)
from redistrict.linz.scenario_registry import ScenarioRegistry
from redistrict.linz.nz_electoral_api import ConcordanceItem


class CanceledException(Exception):
    """
    Triggered when task is canceled
    """


class CompareScenariosTask(QgsTask):
    """
    Task for comparing scenarios
    """

    ELECTORATE_FEATURE_ID = 'ELECTORATE_FEATURE_ID'
    ELECTORATE_ID = 'ELECTORATE_ID'
    ELECTORATE_TYPE = 'ELECTORATE_TYPE'
    ELECTORATE_CODE = 'ELECTORATE_CODE'
    ELECTORATE_NAME = 'ELECTORATE_NAME'
    MESHBLOCKS = 'MESHBLOCKS'
    OFFSHORE_MESHBLOCKS = 'OFFSHORE_MESHBLOCKS'
    NON_OFFSHORE_MESHBLOCKS = 'NON_OFFSHORE_MESHBLOCKS'
    ESTIMATED_POP = 'ESTIMATED_POP'

    def __init__(self,  # pylint: disable=too-many-locals, too-many-statements
                 task_name: str,
                 scenario_registry: ScenarioRegistry,
                 meshblock_layer: QgsVectorLayer,
                 meshblock_number_field_name: str,
                 task: str,
                 base_scenario_id: int,
                 secondary_scenario_id: int):
        """
        Constructor for CompareScenariosTask
        :param task_name: user-visible, translated name for task
        :param scenario_registry: scenario registry
        :param task: target task
        :param base_scenario_id: base ("original") scenario ID
        :param secondary_scenario_id: secondary ("new") scenario ID
        """
        super().__init__(task_name)

        self._task: str = task
        self._base_scenario_id: int = base_scenario_id
        self._secondary_scenario_id: int = secondary_scenario_id

        self.mb_number_idx = scenario_registry.meshblock_electorate_layer.fields().lookupField('meshblock_number')
        assert self.mb_number_idx >= 0

        self._electorate_field = scenario_registry.electorate_field(task)
        self._electorate_field_index = scenario_registry.meshblock_electorate_layer.fields().lookupField(
            self._electorate_field)
        assert self._electorate_field_index >= 0

        self._meshblock_scenario_field = scenario_registry.MESHBLOCK_SCENARIO_ID_FIELD_NAME
        self._meshblock_scenario_field_index = scenario_registry.meshblock_electorate_layer.fields().lookupField(
            self._meshblock_scenario_field)
        assert self._meshblock_scenario_field_index >= 0

        self._meshblock_number_field_name = meshblock_number_field_name
        self._meshblock_number_field_index = meshblock_layer.fields().lookupField(
            self._meshblock_number_field_name)
        assert self._meshblock_number_field_index >= 0

        # do a bit of preparatory processing on the main thread for safety
        self._meshblock_features = scenario_registry.meshblocks_for_scenarios([
            self._base_scenario_id, self._secondary_scenario_id
        ])

        self.changed_meshblocks = set()
        self.base_electorates = {}
        self.secondary_electorates = {}
        self._meshblock_layer_source = QgsVectorLayerFeatureSource(meshblock_layer)
        self._meshblock_layer_fields = meshblock_layer.fields()
        self._meshblock_layer_geometry_type = meshblock_layer.wkbType()
        self._meshblock_layer_crs = meshblock_layer.crs()

        self._base_scenario_name = scenario_registry.get_scenario_name(self._base_scenario_id)
        self._secondary_scenario_name = scenario_registry.get_scenario_name(self._secondary_scenario_id)
        self.changed_meshblocks_layer: Optional[QgsVectorLayer] = None

    def run(self):  # pylint: disable=missing-docstring

        for meshblock in self._meshblock_features:
            meshblock_id = meshblock[self.mb_number_idx]

            scenario = meshblock[self._meshblock_scenario_field_index]
            if scenario == self._base_scenario_id:
                self.base_electorates[meshblock_id] = meshblock[self._electorate_field]
            elif scenario == self._secondary_scenario_id:
                self.secondary_electorates[meshblock_id] = meshblock[self._electorate_field]
            else:
                assert False

        for meshblock_id, _base_electorate in self.base_electorates.items():
            if self.secondary_electorates[meshblock_id] == _base_electorate:
                continue

            self.changed_meshblocks.add(meshblock_id)

        changed_meshblocks_str = ','.join(f"'{ConcordanceItem.format_meshblock_number(_id)}'" for _id in self.changed_meshblocks)
        changed_meshblock_request = QgsFeatureRequest()
        changed_meshblock_request.setFilterExpression(
            f'{self._meshblock_number_field_name} in ({changed_meshblocks_str})')

        changed_layer_name = f'Meshblock changes - {self._task} ({self._secondary_scenario_name} vs {self._base_scenario_name})'

        changed_meshblock_fields = QgsFields(self._meshblock_layer_fields)
        changed_meshblock_fields.append(
            QgsField('previous_electorate_id', QVariant.Int)
        )
        changed_meshblock_fields.append(
            QgsField('new_electorate_id', QVariant.Int)
        )

        self.changed_meshblocks_layer = QgsMemoryProviderUtils.createMemoryLayer(
            changed_layer_name,
            changed_meshblock_fields,
            self._meshblock_layer_geometry_type,
            self._meshblock_layer_crs,
            False
        )

        for changed_meshblock in self._meshblock_layer_source.getFeatures(changed_meshblock_request):
            meshblock_id = int(changed_meshblock[self._meshblock_number_field_index])
            out_feature = QgsFeature(changed_meshblock_fields)
            attributes = changed_meshblock.attributes()
            attributes.extend(
                [self.base_electorates[meshblock_id], self.secondary_electorates[meshblock_id]]
            )
            out_feature.setAttributes(attributes)
            out_feature.setGeometry(changed_meshblock.geometry())

            assert self.changed_meshblocks_layer.dataProvider().addFeature(out_feature, QgsFeatureSink.FastInsert)

        self.changed_meshblocks_layer.moveToThread(None)

        return True
