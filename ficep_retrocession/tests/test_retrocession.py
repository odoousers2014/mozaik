# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import psycopg2
import logging
from openerp.osv import orm
from anybox.testing.openerp import SharedSetupTransactionCase

from openerp.addons.ficep_base import testtool

_logger = logging.getLogger(__name__)


class test_retrocession(SharedSetupTransactionCase):

    _data_files = (
        '../../ficep_base/tests/data/res_partner_data.xml',
        '../../ficep_structure/tests/data/structure_data.xml',
        'data/retrocession_data.xml',
    )

    _module_ns = 'ficep_retrocession'

    def setUp(self):
        super(test_retrocession, self).setUp()

    def test_fractionation_invalidate(self):
        '''
            Test automatic invalidation of lines of a given fractionation
        '''
        fractionation_pool = self.registry('fractionation')
        fractionation_01 = self.browse_ref('%s.f_sample_01' % self._module_ns)

        fractionation_pool.action_invalidate(self.cr, self.uid, [fractionation_01.id])

        for line in fractionation_01.fractionation_line_ids:
            self.assertFalse(line.active)

    def test_fractionation_compute_total_percentage(self):
        '''
            Test compute total percentage of all lines
        '''
        fractionation_01 = self.browse_ref('%s.f_sample_01' % self._module_ns)
        self.assertEqual(fractionation_01.total_percentage, 100)

    def test_fractionation_line_percentage(self):
        '''
            Test percentage of line must be lower or equal to 100
        '''
        fractionation_02_id = self.ref('%s.f_sample_02' % self._module_ns)
        int_power_level_02_id = self.ref('%s.int_power_level_02' % self._module_ns)
        data = dict(fractionation_id=fractionation_02_id,
                    power_level_id=int_power_level_02_id,
                    percentage=142)

        self.assertRaises(orm.except_orm, self.registry('fractionation.line').create, self.cr, self.uid, data)

    def test_unicity_fractionation_line(self):
        '''
            Test reference to a power level must unique within a fractionation
        '''
        fractionation_02_id = self.ref('%s.f_sample_02' % self._module_ns)
        int_power_level_01_id = self.ref('ficep_structure.int_power_level_01')
        data = dict(fractionation_id=fractionation_02_id,
                    power_level_id=int_power_level_01_id,
                    percentage=20)
        with testtool.disable_log_error(self.cr):
            self.assertRaises(psycopg2.IntegrityError,
                              self.registry('fractionation.line').create,
                              self.cr, self.uid, data)

    def test_calculation_method_invalidate(self):
        '''
            Test automatic invalidation of rules of a given calculation method
        '''
        method_pool = self.registry('calculation.method')
        method_01 = self.browse_ref('%s.cm_sample_01' % self._module_ns)

        method_pool.action_invalidate(self.cr, self.uid, [method_01.id])

        for rule in method_01.calculation_rule_ids:
            self.assertFalse(rule.active)

    def test_calculation_method_type(self):
        '''
            Test automatic computation of type
        '''
        rule_pool = self.registry('calculation.rule')
        method_01 = self.browse_ref('%s.cm_sample_01' % self._module_ns)

        data = dict(name="Calculation rule test sample",
                    calculation_method_id=method_01.id,
                    type='variable',
                    percentage=2)

        rule_pool.create(self.cr, self.uid, data)

        self.assertEqual(method_01.type, 'mixed')