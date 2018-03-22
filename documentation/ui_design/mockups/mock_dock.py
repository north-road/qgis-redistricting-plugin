dock=QgsDockWidget('Redistricting - Scenario 1')
dock_contents = QWidget()
grid=QGridLayout(dock_contents)
grid.setContentsMargins(0,0,0,0)

dock_toolbar = QToolBar(dock_contents)
dock_toolbar.setFloatable(False)
grid.addWidget(dock_toolbar,0,0,1,1)

dock_toolbar.setIconSize(iface.iconSize(True))

scenarios_tool_button = QToolButton()
scenarios_tool_button.setAutoRaise(True)
scenarios_tool_button.setToolTip('Scenarios')
scenarios_tool_button.setIcon(QIcon('/home/nyall/dev/redistricting/images/scenarios.svg'))
scenarios_tool_button.setPopupMode(QToolButton.InstantPopup)

def select_current_scenario():
    dlg = ScenarioSelectionDialog(iface.mainWindow())
    dlg.exec_()        
    
def branch_scenario():
    dlg = QgsNewNameDialog('Scenario 1', 'Scenario 1 Copy', parent=iface.mainWindow())
    dlg.setWindowTitle('Branch to New Scenario')
    dlg.setHintString('Enter name for new scenario')
    dlg.show()
    
scenarios_menu = QMenu()
switch_scenario_action = QAction('Switch to Existing Scenario...')
switch_scenario_action.triggered.connect(select_current_scenario)
scenarios_menu.addAction(switch_scenario_action)
store_scenario_action = QAction('Branch to New Scenario...')
store_scenario_action.triggered.connect(branch_scenario)
scenarios_menu.addAction(store_scenario_action)
import_scenario_action = QAction('Import Scenario from Database...')
scenarios_menu.addAction(import_scenario_action)
scenarios_tool_button.setMenu(scenarios_menu)

dock_toolbar.addWidget(scenarios_tool_button)

validate_action=QAction(QIcon('/home/nyall/dev/redistricting/images/validate.svg'),'Validate Districts')
dock_toolbar.addAction(validate_action)

options_button = QToolButton()
options_button.setAutoRaise(True)
options_button.setToolTip('Options')
options_button.setIcon(QIcon('/home/nyall/dev/redistricting/images/options.svg'))
options_button.setPopupMode(QToolButton.InstantPopup)

options_menu = QMenu()
new_electorate_action = QAction('New Electorate...')
options_menu.addAction(new_electorate_action)
options_menu.addSeparator()


master_db_menu = QMenu('Master Database')
export_master_action = QAction('Export Master Database...')
master_db_menu.addAction(export_master_action )
import_master_action = QAction('Import Master Database...')
master_db_menu.addAction(import_master_action )
options_menu.addMenu(master_db_menu)

options_button.setMenu(options_menu)

dock_toolbar.addWidget(options_button)

help_action=QAction(QIcon('/home/nyall/dev/redistricting/images/help.svg'),'Help')
dock_toolbar.addAction(help_action)

frame=QTextBrowser()
frame.setHtml('<h1>Scenario 1</h1><h3>Estimated Count</h3>')
grid.addWidget(frame,1,0,1,1)

dock.setWidget(dock_contents)

iface.addDockWidget(Qt.RightDockWidgetArea, dock)

class ScenarioSelectionDialog(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle('Select Current Scenario')
        
        l = QVBoxLayout()
        
        search = QgsFilterLineEdit()
        search.setShowSearchIcon(True)
        search.setPlaceholderText('Search for scenario')
        l.addWidget(search)
        
        list = QListWidget()
        for i in range(10):
            list.addItem( 'Scenario {}'.format(i))
            
        l.addWidget(list)
        
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        l.addWidget(bb)
        bb.rejected.connect(self.reject)
        bb.accepted.connect(self.accept)
            
        self.setLayout(l)
        
