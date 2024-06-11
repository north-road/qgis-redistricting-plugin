"""
LINZ Redistricting Plugin - Staged electorate updating task
"""

from qgis.core import (
    NULL,
    QgsTask,
    QgsFeatureRequest,
    QgsVectorLayer,
    QgsExpression
)
from redistrict.linz.scenario_registry import ScenarioRegistry


class UpdateStagedElectoratesTask(QgsTask):
    """
    A background task for updating staged electorates
    """

    def __init__(self, task_name: str, meshblock_layer: QgsVectorLayer,  # pylint: disable=too-many-locals
                 meshblock_number_field_name: str, scenario_registry: ScenarioRegistry, scenario, task: str):
        """
        Constructor for ScenarioSwitchTask
        :param task_name: user-visible, translated name for task
        :param electorate_layer: electorate layer
        :param meshblock_layer: meshblock layer
        :param meshblock_number_field_name: name of meshblock number field
        :param scenario_registry: scenario registry
        :param scenario: target scenario id to switch to
        :param task: current task
        """
        super().__init__(task_name)

        self.scenario = scenario

        self.mb_number_idx = scenario_registry.meshblock_electorate_layer.fields().lookupField('meshblock_number')

        electorate_field_name = f'{task.lower()}_id'
        self.electorate_field_idx = scenario_registry.meshblock_electorate_layer.fields().lookupField(
            electorate_field_name)
        assert self.electorate_field_idx >= 0
        self.scenario_id_field_idx = scenario_registry.meshblock_electorate_layer.fields().lookupField('scenario_id')
        assert self.scenario_id_field_idx >= 0
        self.staged_electorate_field_idx = meshblock_layer.fields().lookupField('staged_electorate')
        assert self.staged_electorate_field_idx >= 0
        self.meshblock_number_idx = meshblock_layer.fields().lookupField(meshblock_number_field_name)
        assert self.meshblock_number_idx >= 0
        self.meshblock_layer = meshblock_layer

        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression('scenario_id', scenario))
        request.setSubsetOfAttributes([self.mb_number_idx, self.electorate_field_idx])
        self.meshblocks_for_scenario = scenario_registry.meshblock_electorate_layer.getFeatures(request)

        self.setDependentLayers([meshblock_layer])

    def run(self):  # pylint: disable=missing-docstring
        # build dictionary of meshblock number to electorate field
        meshblock_electorate = {m[self.mb_number_idx]: m[self.electorate_field_idx] for m in
                                self.meshblocks_for_scenario}

        attribute_change_map = {}
        request = QgsFeatureRequest()
        request.setSubsetOfAttributes([self.meshblock_number_idx])
        request.setFlags(QgsFeatureRequest.NoGeometry)
        to_process = self.meshblock_layer.featureCount()
        for i, m in enumerate(self.meshblock_layer.getFeatures(request)):
            self.setProgress(80 * i / to_process)
            if not int(m[self.meshblock_number_idx]) in meshblock_electorate:
                electorate = NULL
            else:
                electorate = meshblock_electorate[int(m[self.meshblock_number_idx])]
            attribute_change_map[m.id()] = {self.staged_electorate_field_idx: electorate}

        # commit changes
        if not self.meshblock_layer.dataProvider().changeAttributeValues(attribute_change_map):
            return False

        return True
