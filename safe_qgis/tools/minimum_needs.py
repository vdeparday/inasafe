# coding=utf-8
"""**Minimum Needs Implementation.**

.. tip:: Provides minimum needs assessment for a polygon layer containing
    counts of people affected per polygon.

"""

__author__ = 'tim@linfiniti.com, ole.moller.nielsen@gmail.com'
__revision__ = '$Format:%H$'
__date__ = '20/1/2013'
__license__ = "GPL"
__copyright__ = 'Copyright 2013, Australia Indonesia Facility for '
__copyright__ += 'Disaster Reduction'

import logging

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignature

from qgis.core import QgsMapLayerRegistry, QgsVectorLayer

from safe_qgis.safe_interface import get_version, safe_read_layer, Vector
from safe_qgis.ui.minimum_needs_base import Ui_MinimumNeedsBase
from safe_qgis.utilities.utilities import (
    add_ordered_combo_item,
    is_polygon_layer,
    is_point_layer,
    html_footer,
    html_header)
from safe_qgis.utilities.help import show_context_help
from safe_qgis.safe_interface import evacuated_population_weekly_needs
from safe_qgis.safe_interface import messaging as m
from safe_qgis.safe_interface import styles

INFO_STYLE = styles.INFO_STYLE
LOGGER = logging.getLogger('InaSAFE')


class MinimumNeeds(QtGui.QDialog, Ui_MinimumNeedsBase):
    """Dialog implementation class for the InaSAFE minimum needs dialog.
    """

    def __init__(self, parent=None):
        """Constructor for the minimum needs dialog.

        :param parent: Parent widget of this dialog.
        :type parent: QWidget
        """

        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(self.tr(
            'InaSAFE %s Minimum Needs Tool') % (get_version()))
        self.polygon_layers_to_combo()
        self.show_info()
        helpButton = self.button_box.button(QtGui.QDialogButtonBox.Help)
        QtCore.QObject.connect(helpButton, QtCore.SIGNAL('clicked()'),
                               self.show_help)

    def show_info(self):
        """Show basic usage instructions."""
        header = html_header()
        footer = html_footer()
        string = header

        heading = m.Heading(self.tr('Minimum Needs Calculator'), **INFO_STYLE)
        body = self.tr(
            'This tool will calculated minimum needs for evacuated people. To '
            'use this tool effectively:'
        )
        tips = m.BulletedList()
        tips.add(self.tr(
            'Load a polygon layer in QGIS. Typically the layer will '
            'represent administrative districts where people have gone to an '
            'evacuation center.'))
        tips.add(self.tr(
            'Ensure that the layer has an INTEGER attribute for the number of '
            'displaced people associated with each feature.'
        ))
        tips.add(self.tr(
            'Use the pick lists below to select the layer and the population '
            'field and then press \'OK\'.'
        ))
        tips.add(self.tr(
            'A new layer will be added to QGIS after the calculation is '
            'complete. The layer will contain the minimum needs per district '
            '/ administrative boundary.'))
        message = m.Message()
        message.add(heading)
        message.add(body)
        message.add(tips)
        string += message.to_html()
        string += footer

        self.webView.setHtml(string)

    def minimum_needs(self, input_layer, population_name):
        """Compute minimum needs given a layer and a column containing pop.

        :param input_layer: InaSAFE layer object assumed to contain
            population counts
        :type input_layer: read_layer

        :param population_name: Attribute name that holds population count
        :type population_name: str

        :returns: Layer with attributes for minimum needs as per Perka 7
        :rtype: read_layer
        """

        all_attributes = []
        for attributes in input_layer.get_data():
            # Get population count
            population = attributes[population_name]
            # Clean up and turn into integer
            if population in ['-', None]:
                displaced = 0
            else:
                if type(population) is basestring:
                    population = str(population).replace(',', '')

                try:
                    displaced = int(population)
                except ValueError:
                    # noinspection PyTypeChecker,PyArgumentList
                    QtGui.QMessageBox.information(
                        None,
                        self.tr('Format error'),
                        self.tr(
                            'Please change the value of %1 in attribute '
                            '%1 to integer format').arg(population).arg(
                                population_name))
                    raise ValueError

            # Calculate estimated needs based on BNPB Perka 7/2008
            # minimum needs
            # weekly_needs = {
            #     'rice': int(ceil(population * min_rice)),
            #     'drinking_water': int(ceil(population * min_drinking_water)),
            #     'water': int(ceil(population * min_water)),
            #     'family_kits': int(ceil(population * min_family_kits)),
            #     'toilets': int(ceil(population * min_toilets))}

            # Add to attributes
            weekly_needs = evacuated_population_weekly_needs(displaced)

            # Record attributes for this feature
            all_attributes.append(weekly_needs)

        output_layer = Vector(
            geometry=input_layer.get_geometry(),
            data=all_attributes,
            projection=input_layer.get_projection())
        return output_layer

    def polygon_layers_to_combo(self):
        """Populate the combo with all polygon layers loaded in QGIS."""

        # noinspection PyArgumentList
        myRegistry = QgsMapLayerRegistry.instance()
        myLayers = myRegistry.mapLayers().values()
        myFoundFlag = False
        for myLayer in myLayers:
            myName = myLayer.name()
            mySource = str(myLayer.id())
            # check if layer is a vector polygon layer
            if is_polygon_layer(myLayer) or is_point_layer(myLayer):
                myFoundFlag = True
                add_ordered_combo_item(self.cboPolygonLayers, myName, mySource)
        if myFoundFlag:
            self.cboPolygonLayers.setCurrentIndex(0)

    @pyqtSignature('int')
    def on_cboPolygonLayers_currentIndexChanged(self, theIndex=None):
        """Automatic slot executed when the layer is changed to update fields.

        :param theIndex: Passed by the signal that triggers this slot.
        :type theIndex: int
        """
        myLayerId = self.cboPolygonLayers.itemData(
            theIndex, QtCore.Qt.UserRole)
        # noinspection PyArgumentList
        myLayer = QgsMapLayerRegistry.instance().mapLayer(myLayerId)
        myFields = myLayer.dataProvider().fieldNameMap().keys()
        self.cboFields.clear()
        for myField in myFields:
            add_ordered_combo_item(self.cboFields, myField, myField)

    def accept(self):
        """Process the layer and field and generate a new layer.

        .. note:: This is called on OK click.

        """
        myIndex = self.cboFields.currentIndex()
        myFieldName = self.cboFields.itemData(
            myIndex, QtCore.Qt.UserRole)

        myIndex = self.cboPolygonLayers.currentIndex()
        myLayerId = self.cboPolygonLayers.itemData(
            myIndex, QtCore.Qt.UserRole)
        # noinspection PyArgumentList
        myLayer = QgsMapLayerRegistry.instance().mapLayer(myLayerId)

        myFileName = str(myLayer.source())

        myInputLayer = safe_read_layer(myFileName)

        try:
            myOutputLayer = self.minimum_needs(myInputLayer, str(myFieldName))
        except ValueError:
            return

        myNewFile = myFileName[:-4] + '_perka7' + '.shp'

        myOutputLayer.write_to_file(myNewFile)

        myNewLayer = QgsVectorLayer(myNewFile, 'Minimum Needs', 'ogr')
        # noinspection PyArgumentList
        QgsMapLayerRegistry.instance().addMapLayers([myNewLayer])
        self.done(QtGui.QDialog.Accepted)

    def show_help(self):
        """Load the help text for the minimum needs dialog."""
        show_context_help('minimum_needs')
