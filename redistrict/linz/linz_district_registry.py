"""
LINZ Redistricting Plugin - LINZ Specific District registry
"""

from typing import Optional
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    NULL,
    QgsFeatureRequest,
    QgsFeature,
    QgsExpression,
    QgsVectorLayer,
    QgsFields
)
from redistrict.core.district_registry import VectorLayerDistrictRegistry
from redistrict.linz.linz_redistricting_context import LinzRedistrictingContext


class LinzElectoralDistrictRegistry(VectorLayerDistrictRegistry):
    """
    A LINZ specific registry for NZ electoral districts based off field
    values from a vector layer
    """

    def __init__(self, source_layer: QgsVectorLayer,
                 source_field: str,
                 title_field: str,
                 electorate_type: str,
                 quota_layer: QgsVectorLayer,
                 name='districts',
                 type_string_title='Electorate'):
        """
        Constructor for District Registry
        :param source_layer: vector layer to retrieve districts from
        :param source_field: source field (name) to retrieve districts
        from
        :param title_field: field name for district titles
        :param electorate_type: electorate types to show, e.g. "GN"
        :param quota_layer: layer containing quota for district types
        :param name: unique identifying name for registry
        :param type_string_title: title case string for district
        types
        """
        super().__init__(source_layer=source_layer,
                         source_field=source_field,
                         title_field=title_field,
                         name=name,
                         type_string_title=type_string_title,
                         type_string_sentence='electorate',
                         type_string_sentence_plural='electorates')
        self.electorate_type = electorate_type
        self.type_field = 'type'
        self.estimated_population_field = 'estimated_pop'
        self.deprecated_field = 'deprecated'
        self.stats_nz_pop_field = 'stats_nz_pop'
        self.stats_nz_var_20_field = 'stats_nz_var_20'
        self.stats_nz_var_23_field = 'stats_nz_var_23'
        self.scenario_id_field = 'scenario_id'
        self.electorate_stats_id = 'electorate_id_stats'
        self.expected_regions_field = 'expected_regions'

        self.source_field_index = self.source_layer.fields().lookupField(self.source_field)
        assert self.source_field_index >= 0
        self.type_field_index = self.source_layer.fields().lookupField(self.type_field)
        assert self.type_field_index >= 0
        self.estimated_pop_field_index = self.source_layer.fields().lookupField(self.estimated_population_field)
        assert self.estimated_pop_field_index >= 0
        self.deprecated_field_index = self.source_layer.fields().lookupField(self.deprecated_field)
        assert self.deprecated_field_index >= 0

        self.stats_nz_pop_field_index = self.source_layer.fields().lookupField(self.stats_nz_pop_field)
        assert self.stats_nz_pop_field_index >= 0
        self.stats_nz_var_20_field_index = self.source_layer.fields().lookupField(self.stats_nz_var_20_field)
        assert self.stats_nz_var_20_field_index >= 0
        self.stats_nz_var_23_field_index = self.source_layer.fields().lookupField(self.stats_nz_var_23_field)
        assert self.stats_nz_var_23_field_index >= 0
        self.scenario_id_field_index = self.source_layer.fields().lookupField(self.scenario_id_field)
        assert self.scenario_id_field_index >= 0
        self.electorate_stats_id_field_index = self.source_layer.fields().lookupField(self.electorate_stats_id)
        assert self.electorate_stats_id_field_index >= 0
        self.expected_regions_field_index = self.source_layer.fields().lookupField(self.expected_regions_field)
        assert self.expected_regions_field_index >= 0

        self.quota_layer = quota_layer

    # noinspection PyMethodMayBeStatic
    def modify_district_request(self, request):
        """
        Allows subclasses to modify the request used to fetch available
        districts from the source layer, e.g. to add filtering
        or sorting to the request.
        :param request: base feature request to modify
        :return: modified feature request
        """
        request.addOrderBy(self.source_field)
        if self.electorate_type:
            request.setFilterExpression(
                QgsExpression.createFieldEqualityExpression(self.type_field, self.electorate_type))
        request.combineFilterExpression(f'"{self.deprecated_field}" is null or not "{self.deprecated_field}"')
        return request

    def get_district_type(self, electorate_id) -> str:
        """
        Returns the district type (GN/GS/M) for the specified district
        :param electorate_id: electorate id
        """
        # lookup matching feature
        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.source_field, electorate_id))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([self.type_field_index])
        request.setLimit(1)
        f = next(self.source_layer.getFeatures(request))
        return f[self.type_field_index]

    @staticmethod
    def district_type_title(district_type: str) -> str:  # pylint: disable=inconsistent-return-statements
        """
        Returns a user-friendly display title for the specified district type.
        :param district_type: district type to retrieve title for
        """
        if district_type == 'GN':
            return QCoreApplication.translate('LinzRedistrict', 'General North Island')
        elif district_type == 'GS':
            return QCoreApplication.translate('LinzRedistrict', 'General South Island')
        elif district_type == 'M':
            return QCoreApplication.translate('LinzRedistrict', 'Māori')

        # should never happen
        assert False

    def get_quota_for_district_type(self, district_type: str) -> int:
        """
        Returns the quota for the specified district type
        :param district_type: district type, e.g. "GS"
        """
        quota_field_index = self.quota_layer.fields().lookupField('quota')
        assert quota_field_index >= 0

        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression('type', district_type))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([quota_field_index])
        request.setLimit(1)
        f = next(self.quota_layer.getFeatures(request))
        return f[quota_field_index]

    def get_quota_for_district(self, electorate_id) -> int:
        """
        Returns the quota for the given electorate
        :param electorate_id: electorate id
        """
        district_type = self.get_district_type(electorate_id)
        return self.get_quota_for_district_type(district_type)

    def get_code_for_electorate(self, electorate_id):
        """
        Returns the electorate code for a given electorate_id
        :param electorate_id: electorate id
        """
        code_field_index = self.source_layer.fields().lookupField('code')
        assert code_field_index >= 0

        request = QgsFeatureRequest()
        request.setFilterFid(electorate_id)
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([code_field_index])
        request.setLimit(1)
        f = next(self.source_layer.getFeatures(request))
        return f[code_field_index]

    def get_estimated_population(self, electorate_id) -> int:
        """
        Returns the estimated (offline) population for the district
        :param electorate_id: electorate code/id
        """
        # lookup matching feature
        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.source_field, electorate_id))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([self.estimated_pop_field_index])
        request.setLimit(1)
        f = next(self.source_layer.getFeatures(request))
        return f[self.estimated_pop_field_index]

    def get_stats_nz_calculations(self, electorate_id) -> dict:
        """
        Returns a dictionary of Stats NZ calculations for the district
        :param electorate_id: electorate code/id
        """
        # lookup matching feature
        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.source_field, electorate_id))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes(
            [self.stats_nz_var_23_field_index, self.stats_nz_var_20_field_index, self.stats_nz_pop_field_index])
        request.setLimit(1)
        f = next(self.source_layer.getFeatures(request))
        return {'currentPopulation': f[self.stats_nz_pop_field_index],
                'varianceYear1': f[self.stats_nz_var_20_field_index],
                'varianceYear2': f[self.stats_nz_var_23_field_index]}

    @staticmethod
    def get_variation_from_quota_percent(quota: int, population: int) -> Optional[float]:
        """
        Returns the % variation from the quota for an electorate's population
        :param quota: electorate quota
        :param population: actual population
        :return: percentage as int (e.g. 4, -3, etc)
        """
        if population == NULL:
            return None
        return round(1000 * (population - quota) / quota) / 10

    @staticmethod
    def variation_exceeds_allowance(quota: int, population: int) -> bool:
        """
        Returns true if a variation (in percent) exceeds the acceptable tolerance
        :param quota: electorate quota
        :param: population: actual population
        """
        if population == NULL:
            return False

        return abs((population - quota) / quota) >= 0.05

    def create_electorate(self, new_electorate_code, new_electorate_name: str, initial_scenario: int) -> (bool, str):
        """
        Creates a new electorate
        :param new_electorate_code: code for new electorate
        :param new_electorate_name: name for name electorate
        :return: boolean representing success or failure of creation, and error string
        """
        if self.district_name_exists(new_electorate_name):
            return False, QCoreApplication.translate('LinzRedistrict', 'An electorate with this name already exists')

        code_field_idx = self.source_layer.fields().lookupField('code')
        new_id = int(self.source_layer.maximumValue(self.source_field_index)) + 1

        f = QgsFeature()
        f.initAttributes(len([n for n in range(len(self.source_layer.fields())) if self.source_layer.fields().fieldOrigin(n) == QgsFields.OriginProvider]))
        f[self.source_layer.fields().lookupField(self.title_field)] = new_electorate_name
        f[self.type_field_index] = self.electorate_type
        f[self.source_field_index] = new_id
        f[self.deprecated_field_index] = 0
        f[self.scenario_id_field_index] = initial_scenario
        f[code_field_idx] = new_electorate_code
        stats_code = ''
        if self.electorate_type == LinzRedistrictingContext.TASK_GN:
            stats_code = f'N{new_electorate_code}'
        elif self.electorate_type == LinzRedistrictingContext.TASK_GS:
            stats_code = f'S{new_electorate_code}'
        elif self.electorate_type == LinzRedistrictingContext.TASK_M:
            stats_code = f'M{new_electorate_code}'
        f[self.electorate_stats_id_field_index] = stats_code
        f[self.expected_regions_field_index] = 1

        if not self.source_layer.dataProvider().addFeatures([f]):
            return False, QCoreApplication.translate('LinzRedistrict', 'Could not create new electorate')

        return True, None

    def toggle_electorate_deprecation(self, electorate):
        """
        Toggles the deprecation flag for an electorate
        :param electorate: electorate id
        """
        request = QgsFeatureRequest()
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([self.deprecated_field_index])
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.source_field, electorate))
        f = next(self.source_layer.getFeatures(request))

        is_deprecated = f[self.deprecated_field_index]
        if is_deprecated == NULL:
            is_deprecated = False

        new_status = 0 if is_deprecated else 1
        self.source_layer.dataProvider().changeAttributeValues({f.id(): {self.deprecated_field_index: new_status}})

    def update_stats_nz_values(self, electorate_id, results: dict):
        """
        Updates an electorate's stored Statistics NZ api calculations
        :param electorate_id: electorate to update
        :param results: results dictionary from stats API
        """

        # get feature ID
        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.source_field, electorate_id))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([])
        request.setLimit(1)
        f = next(self.source_layer.getFeatures(request))

        self.source_layer.dataProvider().changeAttributeValues(
            {f.id(): {self.stats_nz_pop_field_index: results['currentPopulation'],
                      self.stats_nz_var_20_field_index: results['varianceYear1'],
                      self.stats_nz_var_23_field_index: results['varianceYear2']}})

    def flag_stats_nz_updating(self, electorate_id):
        """
        Flags an electorate's Statistics NZ api calculations as being currently updated
        :param electorate_id: electorate to update
        """

        # get feature ID
        request = QgsFeatureRequest()
        request.setFilterExpression(QgsExpression.createFieldEqualityExpression(self.source_field, electorate_id))
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request.setSubsetOfAttributes([])
        request.setLimit(1)
        f = next(self.source_layer.getFeatures(request))

        self.source_layer.dataProvider().changeAttributeValues({f.id(): {self.stats_nz_pop_field_index: -1,
                                                                         self.stats_nz_var_20_field_index: NULL,
                                                                         self.stats_nz_var_23_field_index: NULL}})
