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
from openerp.tools.translate import _

MAIN_COORDINATE_ERROR = _('Exactly one main coordinate must exist for a given partner')


class ficep_coordinate(orm.AbstractModel):

    _name = 'ficep.coordinate'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    _coordinate_field = None

    _columns = {
        'id': fields.integer('ID', readonly=True),

        'partner_id': fields.many2one('res.partner', 'Contact', readonly=True, required=True, select=True),
        'coordinate_category_id': fields.many2one('coordinate.category', 'Coordinate Category', select=True, track_visibility='onchange'),

        'is_main': fields.boolean('Is Main', readonly=True, select=True),
        'unauthorized': fields.boolean('Unauthorized', track_visibility='onchange'),
        'vip': fields.boolean('VIP', track_visibility='onchange'),

        'is_duplicate_detected': fields.boolean('Is Duplicate Detected', track_visibility='onchange', readonly=True),
        'is_duplicate_allowed': fields.boolean('Is Duplicate Allowed', track_visibility='onchange', readonly=True),

        'create_date': fields.datetime('Creation Date', readonly=True),
        'expire_date': fields.datetime('Expiration Date', readonly=True, track_visibility='onchange'),
        'active': fields.boolean('Active', readonly=True),
    }

# constraints

    def _check_one_main_coordinate(self, cr, uid, ids, for_unlink=False, context=None):
        """
        ==========================
        _check_one_main_coordinate
        ==========================
        Check if associated partner has exactly one main coordinate
        :rparam: True if it is the case
                 False otherwise
        :rtype: boolean
        """
        coordinates = self.browse(cr, uid, ids, context=context)
        for coordinate in coordinates:
            if for_unlink and not coordinate.is_main:
                continue

            coordinate_ids = self.search(cr, uid, [('partner_id', '=', coordinate.partner_id.id)], context=context)

            if for_unlink and len(coordinate_ids) > 1 and coordinate.is_main:
                return False

            if not coordinate_ids:
                continue

            coordinate_ids = self.search(cr, uid, [('partner_id', '=', coordinate.partner_id.id),
                                                   ('is_main', '=', True)], context=context)
            if len(coordinate_ids) != 1:
                return False

        return True

    def _check_unicity(self, cr, uid, ids, context=None):
        """
        ==============
        _check_unicity
        ==============
        :rparam: False if coordinate already exists with (self._coordinate_field,partner_id,expire_date)
                 Else True
        :rtype: Boolean
        """
        pc_rec = self.browse(cr, uid, ids, context=context)[0]
        res_ids = self.search(cr, uid, [('id', '!=', pc_rec.id),
                                        ('partner_id', '=', pc_rec.partner_id.id),
                                        (self._coordinate_field, '=', pc_rec[self._coordinate_field].id),
                                        ('expire_date', '=', False)], context=context)
        return len(res_ids) == 0

    _constraints = [
        (_check_unicity, _('This coordinate already exists for this contact'), ['related_field', 'partner_id', 'expire_date']),
        (_check_one_main_coordinate, MAIN_COORDINATE_ERROR, ['partner_id'])
    ]

# view methods: onchange, button

    def button_invalidate(self, cr, uid, ids, context=None):
        """
        =================
        button_invalidate
        =================
        This method invalidate a ficep_coordinate by setting
        * active to False
        * expire_date to current date
        :rparam: True
        :rtype: boolean

        **Note**
        :raise: Error if the coordinate is main
                and another coordinate of the same type exists
                (ref phone_phone._check_one_main_coordinate)
        """
        self.write(cr, uid, ids,
                   {'active': False, 'expire_date': fields.datetime.now(),
                    'is_duplicate_detected': False,
                    'is_duplicate_allowed': False},
                   context=context)
        return True

# orm methods

    def name_get(self, cr, uid, ids, context=None):
        """
        ========
        name_get
        ========
        :rparam: list of tuple (id, name to display)
                 where id is the id of the object into the relation
                 and display_name, the name of this object.
        :rtype: [(id,name)] list of tuple
        """
        if not ids:
            return []

        if isinstance(ids, (long, int)):
            ids = [ids]

        res = []
        for record in self.read(cr, uid, ids, [self._coordinate_field], context=context):
            display_name = record[self._coordinate_field][1]
            res.append((record['id'], display_name))
        return res

    def unlink(self, cr, uid, ids, context=None):
        """
        =======================
        unlink phone.coordinate
        =======================
        :rparam: True
        :rtype: boolean
        :raise: Error if the coordinate is main
                and another coordinate of the same type exists
        """
        coordinate_ids = self.search(cr, uid, [('id', 'in', ids), ('is_main', '=', False)], context=context)
        read_phone_ids = self.read(cr, uid, ids, [self._coordinate_field], context=context)
        super(ficep_coordinate, self).unlink(cr, uid, coordinate_ids, context=context)
        coordinate_ids = list(set(ids).difference(coordinate_ids))
        if not self._check_one_main_coordinate(cr, uid, coordinate_ids, for_unlink=True, context=context):
            raise orm.except_orm(_('Error'), MAIN_COORDINATE_ERROR)
        res = super(ficep_coordinate, self).unlink(cr, uid, coordinate_ids, context=context)
        phone_ids = []
        for read_phone_id in read_phone_ids:
            phone_ids.append(read_phone_id[self._coordinate_field][0])
        self.management_of_duplicate(cr, uid, phone_ids, context)
        return res

    def copy_data(self, cr, uid, ids, default=None, context=None):
        res = super(ficep_coordinate, self).copy_data(cr, uid, ids, default=default, context=context)
        if res.get('active', True):
            raise orm.except_orm(_('Error'), _('An active coordinate cannot be duplicated!'))
        res.update({
                    'active': True,
                    'expire_date': False,
                   })
        return res

# public methods

    def get_linked_partners(self, cr, uid, ids, context=None):
        """
        ===================
        get_linked_partners
        ===================
        Returns partner ids linked to coordinate ids
        Path to partner must be object.partner_id
        :rparam: partner_ids
        :rtype: list of ids
        """
        model_rds = self.browse(cr, uid, ids, context=context)
        partner_ids = []
        for record in model_rds:
            partner_ids.append(record.partner_id.id)
        return partner_ids

    def change_main_coordinate(self, cr, uid, partner_ids, field_id, context=None):
        """
        ========================
        change_main_coordinate
        ========================
        :param partner_ids: list of partner id
        :type partner_ids: [integer]
        :param field_id: id of the new main object selected
        :type field_id: integer
        :rparam: list of ficep.coordinate ids created
        :rtype: list of integer
        """
        return_ids = []
        for partner_id in partner_ids:
            res_ids = self.search(cr, uid, [('partner_id', '=', partner_id),
                                            (self._coordinate_field, '=', field_id)], context=context)
            if not res_ids:
                # must be create
                return_ids.append(self.create(cr, uid, {'partner_id': partner_id,
                                                        self._coordinate_field: field_id,
                                                        'is_main': True,
                                                        }, context=context))
            else:
                # If the coordinate is not already ``main``, set it as main
                if not self.read(cr, uid, res_ids[0], ['is_main'], context=context)['is_main']:
                    self.set_as_main(cr, uid, res_ids, context=context)
        return return_ids

    def search_and_update(self, cr, uid, target_domain, fields_to_update, as_super_user=None, context=None):
        """
        ==================
        search_and_update
        ==================
        :param  target_domain: A domain used into a search
        :type target_domain: list of tuples
        :param fields_to_update: contain the field to be updated
        :type fields_to_update: dictionary
        :rparam: True some objects are found otherwise False
        :rparam: boolean
        **Note**
        1) Search with self on ``target_domain``
        2) Update self with ``fields_to_update``
        """
        res_ids = self.search(cr, uid, target_domain, context=context)
        save_constraints, self._constraints = self._constraints, []
        self.write(cr, uid, res_ids, fields_to_update, context=context)
        self._constraints = save_constraints
        return len(res_ids) != 0

    def management_of_duplicate(self, cr, uid, field_ids, context=None):
        """
        :param field_ids: ids of related object coordinate field
        :type field_ids: list integer
        This method will update the duplicate attribute of ficep coordinate
        depending if other are found.
        """
        for field_id in field_ids:
            coordinate_ids = self.search(cr, uid, [(self._coordinate_field, \
                                 '=', field_id)], context=context)
            if coordinate_ids:
                fields_to_update = {'is_duplicate_allowed': False, }
                if len(coordinate_ids) > 1:
                    fields_to_update['is_duplicate_detected'] = True
                else:
                    fields_to_update['is_duplicate_detected'] = False
                super(ficep_coordinate, self).write(cr, uid, coordinate_ids,
                               fields_to_update, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
