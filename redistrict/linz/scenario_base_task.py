"""
LINZ Redistricting Plugin - Scenario base task
"""
import gc

from typing import (
    Optional,
    List
)
from qgis.PyQt.QtCore import (
    QObject,
    QRunnable,
    QThreadPool,
    pyqtSlot,
    pyqtSignal,
    QEventLoop
)

from qgis.core import (QgsTask,
                       QgsFeatureRequest,
                       QgsVectorLayer,
                       QgsGeometry)
from redistrict.core import CoreUtils
from redistrict.linz.scenario_registry import ScenarioRegistry


class CanceledException(Exception):
    """
    Triggered when task is canceled
    """


class MergedGeometryWorkerSignals(QObject):
    """
    QObject for safe cross-thread communication
    for MergedGeometryWorker
    """
    finished = pyqtSignal(int, QgsGeometry)


class MergedGeometryWorker(QRunnable):
    """
    Worker thread which performs geometry merging
    """

    def __init__(self, worker_id: int, geometries: List[QgsGeometry]):
        super().__init__()
        self.worker_id = worker_id
        self.geometries = geometries
        self.output: Optional[QgsGeometry] = None
        self.signals = MergedGeometryWorkerSignals()

    @pyqtSlot()
    def run(self):
        """
        Performs the expensive geometry merging.

        We can do this in a Python thread with great performance benefits,
        because the vast bulk of this task is performed in c++...
        """
        self.output = CoreUtils.union_geometries(
            self.geometries
        )
        self.output.makeValid()
        if self.output.isEmpty():
            self.output = QgsGeometry()
        self.signals.finished.emit(
            self.worker_id, self.output)


class ScenarioBaseTask(QgsTask):
    """
    Base class for scenario related tasks
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
    EXPECTED_REGIONS = 'EXPECTED_REGIONS'
    DEPRECATED = 'DEPRECATED'
    STATS_NZ_POP = 'STATS_NZ_POP'

    def __init__(self,  # pylint: disable=too-many-locals, too-many-statements
                 task_name: str, electorate_layer: QgsVectorLayer, meshblock_layer: QgsVectorLayer,
                 meshblock_number_field_name: str, scenario_registry: ScenarioRegistry, scenario,
                 task: Optional[str] = None):
        """
        Constructor for ScenarioSwitchTask
        :param task_name: user-visible, translated name for task
        :param electorate_layer: electorate layer
        :param meshblock_layer: meshblock layer
        :param meshblock_number_field_name: name of meshblock number field
        :param scenario_registry: scenario registry
        :param scenario: target scenario id to switch to
        :param task: current redistricting task
        """
        super().__init__(task_name)

        gc.disable()
        self.scenario = scenario
        self.electorate_layer = electorate_layer
        self.electorate_geometries = {}
        self.task = task

        self.type_idx = electorate_layer.fields().lookupField('type')
        assert self.type_idx >= 0
        self.scenario_id_idx = electorate_layer.fields().lookupField('scenario_id')
        assert self.scenario_id_idx >= 0
        self.estimated_pop_idx = electorate_layer.fields().lookupField('estimated_pop')
        assert self.estimated_pop_idx >= 0
        self.mb_number_idx = scenario_registry.meshblock_electorate_layer.fields().lookupField('meshblock_number')
        assert self.mb_number_idx >= 0
        self.mb_off_pop_m_idx = meshblock_layer.fields().lookupField('offline_pop_m')
        assert self.mb_off_pop_m_idx >= 0
        self.mb_off_pop_ni_idx = meshblock_layer.fields().lookupField('offline_pop_gn')
        assert self.mb_off_pop_ni_idx >= 0
        self.mb_off_pop_si_idx = meshblock_layer.fields().lookupField('offline_pop_gs')
        assert self.mb_off_pop_si_idx >= 0
        self.mb_offshore_idx = meshblock_layer.fields().lookupField('offshore')
        assert self.mb_offshore_idx >= 0

        self.stats_nz_pop_idx = electorate_layer.fields().lookupField('stats_nz_pop')
        assert self.stats_nz_pop_idx >= 0

        self.invalid_reason_idx = self.electorate_layer.fields().lookupField('invalid_reason')
        assert self.invalid_reason_idx >= 0
        self.invalid_idx = self.electorate_layer.fields().lookupField('invalid')
        assert self.invalid_idx >= 0

        electorate_id_idx = electorate_layer.fields().lookupField('electorate_id')
        assert electorate_id_idx >= 0
        self.code_idx = electorate_layer.fields().lookupField('code')
        assert self.code_idx >= 0
        self.name_idx = electorate_layer.fields().lookupField('name')
        assert self.name_idx >= 0
        self.meshblock_number_idx = meshblock_layer.fields().lookupField(meshblock_number_field_name)
        assert self.meshblock_number_idx >= 0
        self.expected_regions_idx = electorate_layer.fields().lookupField('expected_regions')
        assert self.expected_regions_idx >= 0
        self.deprecated_idx = electorate_layer.fields().lookupField('deprecated')
        assert self.deprecated_idx >= 0

        # do a bit of preparatory processing on the main thread for safety

        # dict of meshblock number to feature
        meshblocks = {}
        for m in meshblock_layer.getFeatures():
            meshblocks[int(m[self.meshblock_number_idx])] = m

        # dict of electorates to process (by id)
        self.electorates_to_process = {}
        request = QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([electorate_id_idx, self.type_idx, self.code_idx, self.name_idx, self.expected_regions_idx, self.deprecated_idx, self.stats_nz_pop_idx])
        for electorate in electorate_layer.getFeatures(request):
            # get meshblocks for this electorate in the target scenario
            electorate_id = electorate[electorate_id_idx]
            electorate_type = electorate[self.type_idx]
            electorate_code = electorate[self.code_idx]
            electorate_name = electorate[self.name_idx]
            expected_regions = electorate[self.expected_regions_idx]
            deprecated = electorate[self.deprecated_idx]
            stats_nz_pop = electorate[self.stats_nz_pop_idx]
            if self.task and electorate_type != self.task:
                continue

            electorate_meshblocks = scenario_registry.electorate_meshblocks(electorate_id=electorate_id,
                                                                            electorate_type=electorate_type,
                                                                            scenario_id=scenario)
            assigned_meshblock_numbers = [m[self.mb_number_idx] for m in electorate_meshblocks]
            matching_meshblocks = [meshblocks[m] for m in assigned_meshblock_numbers]
            offshore_meshblocks = [m for m in matching_meshblocks if m[self.mb_offshore_idx]]
            non_offshore_meshblocks = [m for m in matching_meshblocks if not m[self.mb_offshore_idx]]

            self.electorates_to_process[electorate_id] = {self.ELECTORATE_FEATURE_ID: electorate.id(),
                                                          self.ELECTORATE_TYPE: electorate_type,
                                                          self.ELECTORATE_CODE: electorate_code,
                                                          self.ELECTORATE_NAME: electorate_name,
                                                          self.EXPECTED_REGIONS: expected_regions,
                                                          self.DEPRECATED: deprecated,
                                                          self.MESHBLOCKS: matching_meshblocks,
                                                          self.OFFSHORE_MESHBLOCKS: offshore_meshblocks,
                                                          self.NON_OFFSHORE_MESHBLOCKS: non_offshore_meshblocks,
                                                          self.STATS_NZ_POP: stats_nz_pop}

        self.setDependentLayers([electorate_layer])
        gc.enable()

    def store_electorate_geometry(self,
                                  electorate_id: int,
                                  geometry: QgsGeometry):
        """
        Stores the result of MergedGeometryWorker
        """
        self.electorate_geometries[electorate_id] = geometry

    def calculate_new_electorates(self):
        """
        Calculates the new electorate geometry and populations for the associated scenario
        """
        gc.disable()
        self.electorate_geometries = {}
        electorate_attributes = {}
        i = 0

        merging_thread_pool = QThreadPool()

        workers = []
        remaining_worker_ids = set()
        for electorate_id, params in self.electorates_to_process.items():
            if self.isCanceled():
                raise CanceledException

            self.setProgress(100 * i / len(self.electorates_to_process))

            electorate_feature_id = params[self.ELECTORATE_FEATURE_ID]
            electorate_type = params[self.ELECTORATE_TYPE]
            matching_meshblocks = params[self.MESHBLOCKS]
            offshore_meshblocks = params[self.OFFSHORE_MESHBLOCKS]
            non_offshore_meshblocks = params[self.NON_OFFSHORE_MESHBLOCKS]

            if electorate_type == 'M':
                estimated_pop = sum(
                    mbf[self.mb_off_pop_m_idx] for mbf in matching_meshblocks if mbf[self.mb_off_pop_m_idx])
            elif electorate_type == 'GN':
                estimated_pop = sum(
                    mbf[self.mb_off_pop_ni_idx] for mbf in matching_meshblocks if mbf[self.mb_off_pop_ni_idx])
            else:
                estimated_pop = sum(
                    mbf[self.mb_off_pop_si_idx] for mbf in matching_meshblocks if mbf[self.mb_off_pop_si_idx])

            electorate_attributes[electorate_feature_id] = {self.ESTIMATED_POP: estimated_pop,
                                                            self.ELECTORATE_ID: electorate_id,
                                                            self.ELECTORATE_TYPE: electorate_type,
                                                            self.ELECTORATE_NAME: params[self.ELECTORATE_NAME],
                                                            self.ELECTORATE_CODE: params[self.ELECTORATE_CODE],
                                                            self.EXPECTED_REGIONS: params[self.EXPECTED_REGIONS],
                                                            self.DEPRECATED: params[self.DEPRECATED],
                                                            self.MESHBLOCKS: matching_meshblocks,
                                                            self.OFFSHORE_MESHBLOCKS: offshore_meshblocks,
                                                            self.NON_OFFSHORE_MESHBLOCKS: non_offshore_meshblocks,
                                                            self.STATS_NZ_POP: params[self.STATS_NZ_POP]}

            meshblock_parts = [m.geometry() for m in matching_meshblocks]

            remaining_worker_ids.add(electorate_feature_id)
            merging_worker = MergedGeometryWorker(electorate_feature_id, meshblock_parts)
            workers.append(merging_worker)
            merging_worker.signals.finished.connect(self.store_electorate_geometry)
            merging_thread_pool.start(merging_worker)

            i += 1

        merging_thread_pool.waitForDone()
        loop = QEventLoop()

        while True:
            if not remaining_worker_ids:
                break

            loop.processEvents()
            remaining_worker_ids = set(r for r in remaining_worker_ids
                                       if r not in self.electorate_geometries)
        loop.quit()

        gc.enable()
        return self.electorate_geometries, electorate_attributes
