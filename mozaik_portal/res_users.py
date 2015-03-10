# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of mozaik_portal, an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     mozaik_portal is free software:
#     you can redistribute it and/or
#     modify it under the terms of the GNU Affero General Public License
#     as published by the Free Software Foundation, either version 3 of
#     the License, or (at your option) any later version.
#
#     mozaik_portal is distributed in the hope that it will
#     be useful but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the
#     GNU Affero General Public License
#     along with mozaik_portal.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm


class res_users(orm.Model):

    _inherit = 'res.users',

    def get_partner_user(self, cr, uid, context=None):
        '''
        :rtype: Intger
        :raparam: partner_id of the current user
        '''
        return self.read(
            cr, uid, uid, ['partner_id'], context=context)['partner_id'][0]