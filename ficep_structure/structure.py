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
##############################################################################'''
from openerp.osv import orm, fields
from .sta_structure import sta_instance


class electoral_district(orm.Model):

    _name = 'electoral.district'
    _description = "Electoral District"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _columns = {
        'id': fields.integer('ID', readonly=True),
        'name': fields.char('Name', size=128, translate=True, select=True),
        'sta_instance_id': fields.many2one('sta.instance', 'State Instance',
                                                 required=True, ondelete='cascade'),
        'int_instance_id': fields.related('sta_instance_id', 'int_instance_id', string='Internal Instance', readonly=True,
                                          type='many2one', relation="int.instance",
                                          store={
                                             'electoral.district': (lambda self, cr, uid, ids, context=None: ids, ['sta_instance_id'], 10),
                                             'sta.instance': (sta_instance.get_linked_electoral_districts, ['int_instance_id'], 20),
                                          },
                                         ),
        'assembly_id': fields.many2one('sta.assembly', 'Assembly',
                                                 required=True, ondelete='cascade'),
        'power_level_id': fields.related('sta_instance_id', 'power_level_id', string='Power Level', readonly=True,
                                          type='many2one', relation="sta.power.level"
                                        ),
        'active': fields.boolean('Active', readonly=True),
        }

    _defaults = {
        'active': True,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: