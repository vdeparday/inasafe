# -*- coding: utf-8 -*-
"""**Postprocessors package.**

"""

__author__ = 'Marco Bernasocchi <marco@opengis.ch>'
__revision__ = '$Format:%H$'
__date__ = '10/10/2012'
__license__ = "GPL"
__copyright__ = 'Copyright 2012, Australia Indonesia Facility for '
__copyright__ += 'Disaster Reduction'


from safe.postprocessors.abstract_postprocessor import (
    AbstractPostprocessor)

from safe.common.utilities import (get_defaults,
                                   ugettext as tr)


class AggregationPostprocessor(AbstractPostprocessor):
    """
    Postprocessor that calculates age related statistics.
    see the _calculate_* methods to see indicator specific documentation

    see :mod:`safe.defaults` for default values information
    """

    def __init__(self):
        """
        Constructor for AgePostprocessor postprocessor class,
        It takes care of defining self.impact_total
        """
        AbstractPostprocessor.__init__(self)
        self.impact_total = None

    def setup(self, params):
        """concrete implementation it takes care of the needed parameters being
         initialized

        Args:
            params: dict of parameters to pass to the post processor
        Returns:
            None
        Raises:
            None
        """
        AbstractPostprocessor.setup(self, None)
        if self.impact_total is not None:
            self._raise_error('clear needs to be called before setup')

        self.impact_total = params['impact_total']
        self.target_field = params['target_field']

    def process(self):
        """concrete implementation it takes care of the needed parameters being
         available and performs all the indicators calculations

        Args:
            None
        Returns:
            None
        Raises:
            None
        """
        AbstractPostprocessor.process(self)
        if self.impact_total is None:
            self._raise_error('setup needs to be called before process')
        self._calculate_total()

    def clear(self):
        """concrete implementation it takes care of the needed parameters being
         properly cleared

        Args:
            None
        Returns:
            None
        Raises:
            None
        """
        AbstractPostprocessor.clear(self)
        self.impact_total = None

    def _calculate_total(self):
        """Indicator that shows total population.

        this indicator reports the total population

        Args:
            None
        Returns:
            None
        Raises:
            None
        """
        if self.target_field is None:
            myName = tr('Total')
        else:
            myName = tr(self.target_field).capitalize()

        #FIXME (MB) Shameless hack to deal with issue #368
        if self.impact_total > 8000000000 or self.impact_total < 0:
            self._append_result(myName, self.NO_DATA_TEXT)
            return

        myResult = self.impact_total
        try:
            myResult = int(round(myResult))
        except ValueError:
            myResult = self.NO_DATA_TEXT
        self._append_result(myName, myResult)
