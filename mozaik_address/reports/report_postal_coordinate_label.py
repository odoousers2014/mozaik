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

from openerp.osv import osv
from openerp.report import report_sxw


class report_postal_coordinate_label(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_postal_coordinate_label, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'modulo': self._modulo,
        })

    def _modulo(self, number, modulo):
        return number % modulo


class report_postal_coordinate_label_wrapper(osv.AbstractModel):
    _name = 'report.mozaik_address.report_postal_coordinate_label'
    _inherit = 'report.abstract_report'
    _template = 'mozaik_address.report_postal_coordinate_label'
    _wrapped_report_class = report_postal_coordinate_label

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: