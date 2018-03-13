class UniqueFeatureEdgeMatchCollectingFilter(QgsPointLocator.MatchFilter):
    
    def __init__(self):
        super().__init__()
        self.matches = []
        
    def acceptMatch(self, match):
        if match.type() not in (QgsPointLocator.Area, QgsPointLocator.Edge):
            return False
        
        if match.distance() > 1000:
            return False

        existing_matches = [m for m in self.matches if m.layer()==match.layer() and m.featureId()==match.featureId()]
        if not existing_matches:
            self.matches.append(match)
            return True
        else:
            return False

    def get_matches(self):
        return self.matches


class InteractiveRedistrictingTool(QgsMapTool):
    
    def __init__(self, canvas, meshblock_layer, district_layer):
        super().__init__(canvas)
        self.meshblock_layer = meshblock_layer
        self.district_layer = district_layer
        
        self.snap_indicator = QgsSnapIndicator(self.canvas())
        self.pop_decorator = None
        
        
        self.is_active = False
        
    def get_matches(self, event):
        point = event.mapPoint()
        match_filter = UniqueFeatureEdgeMatchCollectingFilter()
        match = self.canvas().snappingUtils().snapToMap(point, match_filter)
        return match_filter.matches
        
    def check_valid_matches(self, matches):
        feature_ids = [match.featureId() for match in matches]
        features = [f for f in self.meshblock_layer.getFeatures(QgsFeatureRequest().setFilterFids(feature_ids))]
        districts = set([f['GeneralConstituencyCode'] for f in features])
        return len(districts)==2
        
    def canvasMoveEvent(self, event):
        # snapping tool - show indicator
        matches = self.get_matches(event)
        if self.check_valid_matches(matches):
            # we require exactly 2 matches from different districts -- cursor must be over a border
            # of two features
            self.snap_indicator.setMatch(matches[0])
        else:
            self.snap_indicator.setMatch(QgsPointLocator.Match())
        
    def canvasPressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            return
        
        if self.is_active or event.button() == Qt.RightButton:
            if self.pop_decorator is not None:
                self.canvas().scene().removeItem(self.pop_decorator)
                self.pop_decorator = None
                self.canvas().update()
            self.is_active = False
        else:
            matches = self.get_matches(event)
            if self.check_valid_matches(matches):
                self.is_active = True
                self.pop_decorator = CentroidDecorator(self.canvas(), self.district_layer)
                self.canvas().update()
           

            

class CentroidDecorator(QgsMapCanvasItem):
    
    def __init__(self, canvas, layer):
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer
        self.text_format = QgsTextFormat()
        self.text_format.shadow().setEnabled(True)
        self.text_format.background().setEnabled(True)
        self.text_format.background().setSize(QSizeF(1,0))
        self.text_format.background().setOffset(QPointF(0,-0.7))
        self.text_format.background().setRadii(QSizeF(1,1))
        
        
    def paint(self, painter, option, widget):
        image_size = self.canvas.mapSettings().outputSize()
        image = QImage(image_size.width(), image_size.height(), QImage.Format_ARGB32 )
        image.fill(0)
        image_painter = QPainter(image)
        render_context = QgsRenderContext.fromQPainter(image_painter)
        if True:
            image_painter.setRenderHint( QPainter.Antialiasing, True )
            
            rect = self.canvas.mapSettings().visibleExtent()
            line_height = QFontMetrics(painter.font()).height()
            for f in self.layer.getFeatures(QgsFeatureRequest().setFilterRect(rect)):
                pole, dist = f.geometry().clipped(rect).poleOfInaccessibility(3000)
                pixel = self.toCanvasCoordinates(pole.asPoint())
                
                text_string = [f['GeneralConstituencyCode'],f['MaoriConstituencyCode'],f['GeneralElectoralDistrictCode_2007']]
                #print(pixel.toPoint())
                QgsTextRenderer().drawText(QPointF(pixel.x(), pixel.y()),0,QgsTextRenderer.AlignCenter,
                    text_string, render_context,self.text_format)
        #finally:
        image_painter.end()
        
        painter.drawImage(0, 0, image)
                    
meshblock_layer = QgsProject.instance().mapLayersByName('meshblock')[0]       
district_layer = QgsProject.instance().mapLayersByName('general')[0]
       
tool = InteractiveRedistrictingTool(iface.mapCanvas(), meshblock_layer, district_layer)
iface.mapCanvas().setMapTool(tool)
