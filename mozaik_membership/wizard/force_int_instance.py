# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of mozaik_membership, an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     mozaik_membership is free software:
#     you can redistribute it and/or
#     modify it under the terms of the GNU Affero General Public License
#     as published by the Free Software Foundation, either version 3 of
#     the License, or (at your option) any later version.
#
#     mozaik_membership is distributed in the hope that it will
#     be useful but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the
#     GNU Affero General Public License
#     along with mozaik_membership.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm, fields
from openerp.tools import SUPERUSER_ID


class force_int_instance(orm.TransientModel):

    _name = 'force.int.instance'
    _description = 'Change Internal Instance'

    _columns = {
        'int_instance_id': fields.many2one(
            'int.instance', string='Internal Instance',
            required=True, select=True),
        'partner_id': fields.many2one('res.partner',
                                      'Partner', select=True),
    }
    _defaults = {
        'partner_id': lambda self, cr, uid, context:
            context.get('active_id', False)
    }

    def force_int_instance_action(self, cr, uid, ids, context=None):
        '''
        update partner internal instance
        '''
        for wiz in self.browse(cr, uid, ids, context=context):
            if wiz.int_instance_id.id != wiz.partner_id.int_instance_id.id:
                vals = {
                    'int_instance_id': wiz.int_instance_id.id
                }
                wiz.partner_id.write(vals)
                partner_id = wiz.partner_id.id
                partner_obj = self.pool['res.partner']
                partner_obj._update_follower(
                    cr, SUPERUSER_ID, [partner_id], context=context)
                partner_obj.update_membership_line(
                    cr, uid, [partner_id], context=context)

        return True
