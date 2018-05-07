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
    
def import_scenario():
    dlg = ScenarioSelectionDialog(iface.mainWindow())
    dlg.setWindowTitle('Import Scenario from Database')
    if dlg.exec_():
        new_name_dlg = QgsNewNameDialog('Scenario 5', 'Scenario 5', parent=iface.mainWindow())
        new_name_dlg.setWindowTitle('Import Scenario from Database')
        new_name_dlg.setHintString('Enter name for imported scenario')
        new_name_dlg.show()
    
scenarios_menu = QMenu()
switch_scenario_action = QAction('Switch to Existing Scenario...')
switch_scenario_action.triggered.connect(select_current_scenario)
scenarios_menu.addAction(switch_scenario_action)

scenarios_menu.addSeparator()
update_scenario_action = QAction('Update Statistics for Scenario...')
#update_scenario_action.triggered.connect(update_scenario)
scenarios_menu.addAction(update_scenario_action)

scenarios_menu.addSeparator()

store_scenario_action = QAction('Branch to New Scenario...')
store_scenario_action.triggered.connect(branch_scenario)
scenarios_menu.addAction(store_scenario_action)
import_scenario_action = QAction('Import Scenario from Database...')
import_scenario_action.triggered.connect(import_scenario)
scenarios_menu.addAction(import_scenario_action)



scenarios_tool_button.setMenu(scenarios_menu)

dock_toolbar.addWidget(scenarios_tool_button)

def validate():
    table=QTableWidget()
    table.setColumnCount(3)
    table.setRowCount(2)
    table.setHorizontalHeaderLabels(['','Electorate','Error'])
    table.setItem(0,1,QTableWidgetItem('General Electorate 1'))
    table.setItem(0,2,QTableWidgetItem('Electorate is non-contiguous'))
    table.setItem(1,1,QTableWidgetItem('Māori Electorate 4'))
    table.setItem(1,2,QTableWidgetItem('Exceeds population tolerance'))
    
    def create_zoom_button():
        button = QToolButton()
        button.setToolTip('Zoom to Electorate')
        button.setIcon(QIcon('/home/nyall/dev/redistricting/images/zoom_selected.svg'))
        return button
        
    table.setCellWidget(0,0,create_zoom_button())
    table.setCellWidget(1,0,create_zoom_button())
    grid.addWidget(table,1,0,1,1)

    

validate_action=QAction(QIcon('/home/nyall/dev/redistricting/images/validate.svg'),'Validate Districts')
validate_action.triggered.connect(validate)
dock_toolbar.addAction(validate_action)

options_button = QToolButton()
options_button.setAutoRaise(True)
options_button.setToolTip('Options')
options_button.setIcon(QIcon('/home/nyall/dev/redistricting/images/options.svg'))
options_button.setPopupMode(QToolButton.InstantPopup)

class CreateElectorateDialog(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle('Create New Māori Electorate')
        
        l = QVBoxLayout()
        label = QLabel('Enter name for new Māori electorate:')
        l.addWidget(label)
        
        name = QLineEdit()
        name.setPlaceholderText('Electorate name')
        l.addWidget(name)
                
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        l.addWidget(bb)
        bb.rejected.connect(self.reject)
        bb.accepted.connect(self.accept)
            
        self.setLayout(l)
        
        
def create_electorate():
    dlg = CreateElectorateDialog(iface.mainWindow())
    dlg.setWindowTitle('Create New Māori Electorate')
    dlg.show()
    
    
def deprecate_electorate():
    dlg = ElectorateSelectionDialog(iface.mainWindow())
    dlg.setWindowTitle('Deprecate Electorate')
    dlg.exec_()
    
options_menu = QMenu()

electorate_menu = QMenu('Manage Electorates')

new_electorate_action = QAction('Create New Electorate...')
new_electorate_action.triggered.connect(create_electorate)
#new_general_electorate = QAction('General Electorate...')
#new_general_electorate.triggered.connect(create_electorate)
#new_electorate_menu.addAction(new_general_electorate )
#new_maori_electorate = QAction('Maori Electorate...')
#new_electorate_menu.addAction(new_maori_electorate )
electorate_menu.addAction(new_electorate_action)

deprecate_electorate_action = QAction('Deprecate Electorate...')
deprecate_electorate_action.triggered.connect(deprecate_electorate)
electorate_menu.addAction(deprecate_electorate_action)


options_menu.addMenu(electorate_menu)
options_menu.addSeparator()


master_db_menu = QMenu('Database')
export_master_action = QAction('Export Database...')
master_db_menu.addAction(export_master_action )

def import_database():
    dlg = QgsNewNameDialog('', '', parent=iface.mainWindow())
    dlg.setWindowTitle('Import Master Database')
    dlg.setHintString('Importing a new master database will completely replace the existing district database.\n\nThis action cannot be reversed!\n\nEnter \'I ACCEPT\' to continue.')
    dlg.show()

import_master_action = QAction('Import Master Database...')
import_master_action.triggered.connect(import_database)
master_db_menu.addAction(import_master_action )
options_menu.addMenu(master_db_menu)

meshblock_action = QAction('Update Meshblock Table...')
options_menu.addAction(meshblock_action )

export_action = QAction('Export Districts...')
options_menu.addAction(export_action)

options_menu.addSeparator()
log_action = QAction('View Log...')
options_menu.addAction(log_action)

options_button.setMenu(options_menu)

dock_toolbar.addWidget(options_button)

help_action=QAction(QIcon('/home/nyall/dev/redistricting/images/help.svg'),'Help')
dock_toolbar.addAction(help_action)

frame=QTextBrowser()
frame.setHtml("""<h1>Nelson</h1>
<h2>General North Island</h2>
<p>Quota: <span style="font-weight:bold">55555</span></p>
<p>Population: <span style="font-weight:bold;">54382*</span> <span style="color: red; font-weight: bold">(+6%)</span><br>
<span style="font-style:italic">* Only estimated population available</span></p>
<p>Quota Variation 2020: <span style="font-weight:bold">unknown</span><br>
Quota Variation 2023: <span style="font-weight:bold">unknown</span></p>
<p><a href="xxx">Request population from Statistics NZ</a></p>
""")
if False:
    # updating
    frame.setHtml("""<h1>Nelson</h1>
    <h2>General North Island</h2>
    <p>Quota: <span style="font-weight:bold">55555</span></p>
    <p>Population: <span style="font-weight:bold; font-style: italic">updating</span></p>
    <p>Quota Variation 2020: <span style="font-weight:bold; font-style: italic">updating</span><br>
    Quota Variation 2023: <span style="font-weight:bold; font-style: italic">updating</span></p>
    <p><a href="xxx">Request population from Statistics NZ</a></p>
    """)
    # actual

    frame.setHtml("""<h1>Nelson</h1>
    <h2>General North Island</h2>
    <p>Quota: <span style="font-weight:bold">55555</span></p>
    <p>Population: <span style="font-weight:bold;">54382</span> <span style="">(-1%)</span></p>
    <p>Quota Variation 2020: <span style="font-weight:bold">+2%</span><br>
    Quota Variation 2023: <span style="font-weight:bold">+3%</span></p>
    <p><a href="xxx">Request population from Statistics NZ</a></p>
    """)

    frame.setHtml('')
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
        
table=QTableWidget()
