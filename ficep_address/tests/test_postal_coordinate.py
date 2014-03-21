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
from openerp.osv import orm
from anybox.testing.openerp import SharedSetupTransactionCase
import openerp.tests.common as common
import logging

_logger = logging.getLogger(__name__)

DB = common.DB
ADMIN_USER_ID = common.ADMIN_USER_ID


class test_postal_coordinate(SharedSetupTransactionCase):

    _data_files = ('data/address_data.xml',)

    _module_ns = 'ficep_address'

    def setUp(self):
        super(test_postal_coordinate, self).setUp()

        self.registry('ir.model').clear_caches()
        self.registry('ir.model.data').clear_caches()

    def test_check_co_residency_consistency(self):
        postal_coo_2 = self.ref("ficep_address.postal_coordinate_2")
        postal_coo_3 = self.ref("ficep_address.postal_coordinate_3")
        co_residency = self.ref("ficep_address.co_residency_id_1")
        self.assertRaises(orm.except_orm, self.registry('postal.coordinate').write,
                                          self.cr, ADMIN_USER_ID,
                                          [postal_coo_3, postal_coo_2],
                                          {'co_residency_id': co_residency})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: