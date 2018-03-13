t=QToolBar('Redistricting')

interactive_redistrict_action=QAction(QIcon('/home/nyall/dev/redistricting/images/interactive_redistrict.svg'),'Interactive Redistrict')
t.addAction(interactive_redistrict_action)
redistrict_selected_action=QAction(QIcon('/home/nyall/dev/redistricting/images/redistrict_selected.svg'),'Redistrict Selected Mesh Blocks')
t.addAction(redistrict_selected_action)
stats_tool_action=QAction(QIcon('/home/nyall/dev/redistricting/images/stats_tool.svg'),'District Statistics')
t.addAction(stats_tool_action)

themes_tool_button = QToolButton()
themes_tool_button.setAutoRaise(True)
themes_tool_button.setToolTip('Map Themes')
themes_tool_button.setIcon(QIcon('/home/nyall/dev/redistricting/images/themes.svg'))
themes_tool_button.setPopupMode(QToolButton.InstantPopup)

themes_menu = QMenu()
general_theme_action = QAction('General Electorates')
themes_menu.addAction(general_theme_action)
general_change_action = QAction('General Electorate Changes')
themes_menu.addAction(general_change_action)
general_invalid_action = QAction('General Electorate Invalid Districts')
themes_menu.addAction(general_invalid_action)

themes_menu.addSeparator()
maori_theme_action = QAction('Maori Electorates')
themes_menu.addAction(maori_theme_action)
maori_change_action = QAction('Maori Electorate Changes')
themes_menu.addAction(maori_change_action)
maori_invalid_action = QAction('Maori Electorate Invalid Districts')
themes_menu.addAction(maori_invalid_action)

themes_tool_button.setMenu(themes_menu)
t.addWidget(themes_tool_button)

new_map_themes_tool_button = QToolButton()
new_map_themes_tool_button.setAutoRaise(True)
new_map_themes_tool_button.setToolTip('New Themed Map View')
new_map_themes_tool_button.setIcon(QIcon('/home/nyall/dev/redistricting/images/new_themed_map.svg'))
new_map_themes_tool_button.setPopupMode(QToolButton.InstantPopup)

new_map_theme_menu = QMenu()
for a in themes_menu.actions():
    new_map_theme_menu.addAction(a)
new_map_themes_tool_button.setMenu(new_map_theme_menu)
t.addWidget(new_map_themes_tool_button)

iface.addToolBar(t)

p = iface.mapCanvas().mapToGlobal(QtCore.QPoint(0, 0))
t.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)

t.move(p.x() + 30, p.y() + 50)
t.adjustSize()

t.show()
