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
from openerp.osv import orm, fields


class allow_duplicate_wizard(orm.TransientModel):

    _inherit = "allow.duplicate.wizard"
    _name = "allow.duplicate.address.wizard"

    _columns = {
        'address_id': fields.many2one(
            'address.address', string='Co-Residency',
            readonly=True, ondelete='cascade'),
        'co_residency_id': fields.many2one(
            'co.residency', string='Co-Residency',
            readonly=True, ondelete='cascade'),
    }

    def default_get(self, cr, uid, fields, context):
        """
        To get default values for the object.
        """
        res = super(allow_duplicate_wizard, self).default_get(cr, uid, fields, context=context)
        context = context or {}

        ids = context.get('active_id') and [context.get('active_id')] or context.get('active_ids') or []
        for coord_id in ids:
            address_id = res['address_id'] = self.pool['postal.coordinate'].read(cr, uid, coord_id, ['address_id'], context=context)['address_id'][0]
            cor_ids = self.pool['co.residency'].search(cr, uid, [('address_id', '=', address_id)], context=context)
            if cor_ids:
                res['co_residency_id'] = cor_ids[0]
            break

        return res

    def button_allow_duplicate(self, cr, uid, ids, context=None, vals=None):
        """
        ======================
        button_allow_duplicate
        ======================
        Create co_residency if any.
        """
        context = context or {}

        wizard = self.browse(cr, uid, ids, context=context)[0]
        new_co = False
        if wizard.co_residency_id:
            cor_id = wizard.co_residency_id.id
        else:
            vals = {'address_id': wizard.address_id.id}
            cor_id = self.pool['co.residency'].create(cr, uid, vals, context=context)
            new_co = True

        vals = {'co_residency_id': cor_id}
        super(allow_duplicate_wizard, self).button_allow_duplicate(cr, uid, ids, context=context, vals=vals)

        if context and context.get('get_co_residency', False):
            return cor_id

        if new_co:
            # go directly to the newly created co-residency
            return self.pool['co.residency'].display_object_in_form_view(cr, uid, cor_id, context=context)