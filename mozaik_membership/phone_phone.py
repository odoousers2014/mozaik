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


class phone_coordinate(orm.Model):

    # _inherit = 'phone.coordinate'
    _name = 'phone.coordinate'
    _inherit = ['sub.abstract.coordinate', 'phone.coordinate']

    _update_track = {
        'is_main': {
            'mozaik_membership.main_phone_id_notification':
                lambda self, cr, uid, obj, ctx=None: obj.is_main,
            'mozaik_membership.old_phone_id_notification':
                lambda self, cr, uid, obj, ctx=None: not obj.is_main,
        },
        'expire_date': {
            'mozaik_membership.old_phone_id_notification':
                lambda self, cr, uid, obj, ctx=None: obj.expire_date,
        },
    }