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
from datetime import date

from openerp.osv import orm, fields
from openerp.tools import SUPERUSER_ID
from openerp.tools.translate import _

# Constants
AVAILABLE_PARTNER_KINDS = [
    ('a', 'Assembly'),
    ('t', 'Technical'),
    ('c', 'Company'),
    ('p', 'Partner'),
    ('m', 'Member'),
]

XML_IDS = {
    'coordinates': [
        'former_phone_id_notification',
        'main_phone_id_notification',
        'former_email_notification',
        'main_email_notification',
        'former_address_id_notification',
        'main_address_id_notification',
        'membership_line_notification',
    ],
    'partners': [
        'membership_line_notification'
    ]
}


class res_partner(orm.Model):

    _inherit = 'res.partner'

    _inactive_cascade = True
    _allowed_inactive_link_models = ['res.partner']

    # ready for workflow !
    _enable_wkf = True

    def _get_subtype_ids(self, cr, uid, mode, context=None):
        subtype_ids = []
        location = 'mozaik_membership'
        for xml_id in XML_IDS[mode]:
            subtype_ids.append(
                self.pool['ir.model.data'].get_object_reference(
                    cr, uid, location, xml_id)[1])
        return subtype_ids or False

    def _update_follower(
            self, cr, uid, partner_ids, context=None):
        '''
        Update follower for each partner_ids
        '''

        p_obj = self.pool['res.partner']
        ia_obj = self.pool['int.assembly']
        for partner_id in partner_ids:
            int_instance_id = self.read(
                cr, uid, partner_id, ['int_instance_id'],
                context=context)['int_instance_id'][0]
            f_partner_ids = ia_obj.get_followers_assemblies(
                cr, uid, int_instance_id, context=context)
            # update even if f_partner_ids is void case to reset

            subtype_ids = self._get_subtype_ids(
                cr, uid, 'partners', context=context)
            p_obj.message_subscribe(
                cr, uid, [partner_id], f_partner_ids,
                subtype_ids=subtype_ids, context=context)

            subtype_ids = self._get_subtype_ids(
                cr, uid, 'coordinates', context=context)
            # partner are at least follower of their own coordinate
            domain = [('partner_id', '=', partner_id), ('is_main', '=', True)]
            prefixes = ['email', 'postal', 'phone']

            for prefix in prefixes:
                obj = self.pool['%s.coordinate' % prefix]
                res_ids = obj.search(
                    cr, uid, domain, context=context)
                if res_ids:
                    obj.message_subscribe(
                        cr, uid, res_ids, f_partner_ids,
                        subtype_ids=subtype_ids, context=context)
                    # add partner without subtype too
                    obj.message_subscribe(
                        cr, uid, res_ids, f_partner_ids, context=context)

        return True

    def _generate_membership_reference(self, cr, uid, partner_id,
                                       ref_date=None, context=None):
        """
        This method is intended to be overriden regarding
        locale conventions.
        Here is an arbitrary convention: "MS: YYYY/id"
        """
        ref_date = ref_date or date.today().year
        ref = 'MS: %s/%s' % (ref_date, partner_id)
        return ref

    def _update_user_partner(self, cr, uid, partner, vals, context=None):
        """
        When creating a user from a partner,
        give a first value to its int_instance_m2m_ids collection
        """
        vals = vals or {}
        vals['int_instance_m2m_ids'] = [(6, 0, [partner.int_instance_id.id])]
        super(res_partner, self)._update_user_partner(
            cr, uid, partner, vals, context=context)

    def _get_product_id(self, cr, uid, ids, name, arg, context=None):
        res = {}
        ml_values = self.pool['membership.line'].search_read(
            cr, uid, [('partner_id', 'in', ids), ('active', '=', True)],
            ['partner_id', 'product_id'], context=context)
        for val in ml_values:
            res[val['partner_id'][0]] = val.get('product_id') and\
                val['product_id'][0] or False,
        return res

    def _get_partner_kind(self, cr, uid, ids, name, arg, context=None):
        '''
        Compute the kind of partner, computed field used in ir.rule
        '''
        flds = [
            'is_assembly', 'is_company', 'identifier', 'membership_state_code',
        ]
        res = {}
        vals = self.read(cr, SUPERUSER_ID, ids, flds, context=context)
        for val in vals:
            if val['is_assembly']:
                k = 'a'
            elif not val['identifier']:
                k = 't'
            elif val['is_company']:
                k = 'c'
            elif val['membership_state_code'] == 'without_membership':
                k = 'p'
            else:
                k = 'm'
            res[val['id']] = k
        return res

    _track = {
        'membership_state_id': {
            'mozaik_membership.membership_line_notification':
                lambda self, cr, uid, obj, ctx=None:
                    obj.membership_state_id.code != 'without_membership',
        },
    }

    _subscription_store_trigger = {
        'membership.line': (lambda self, cr, uid, ids, context=None:
                            self.pool['membership.line'].get_linked_partners(
                                cr, uid, ids, context=context),
                            ['product_id'], 10),
    }

    _partner_kind_store_trigger = {
        'res.partner': (lambda self, cr, uid, ids, context=None: ids,
                        [
                            'is_assembly', 'is_company',
                            'identifier', 'membership_state_id'
                        ], 10),
    }
    _columns = {
        'int_instance_id': fields.many2one(
            'int.instance', 'Internal Instance', select=True,
            track_visibility='onchange'),
        'int_instance_m2m_ids': fields.many2many(
            'int.instance', 'res_partner_int_instance_rel', id1='partner_id',
            id2='int_instance_id', string='Internal Instances'),
        # membership fields: track visibility is done into membership history
        # management
        'membership_line_ids': fields.one2many(
            'membership.line', 'partner_id', 'Memberships'),
        'free_member': fields.boolean('Free Member'),
        'membership_state_id': fields.many2one('membership.state',
                                               string='Membership State'),
        'membership_state_code': fields.related('membership_state_id', 'code',
                                                string='Membership State Code',
                                                type="char", readonly=True),
        'subscription_product_id': fields.function(
            _get_product_id, type='many2one', relation="product.product",
            string='Subscription', store=_subscription_store_trigger),
        'kind': fields.function(
            _get_partner_kind, string='Partner Kind', type='selection',
            selection=AVAILABLE_PARTNER_KINDS,
            store=_partner_kind_store_trigger),
        'accepted_date': fields.date('Accepted Date'),
        'decline_payment_date': fields.date('Decline Payment Date'),
        'rejected_date': fields.date('Rejected Date'),
        'resignation_date': fields.date('Resignation Date'),
        'exclusion_date': fields.date('Exclusion Date'),

        'del_doc_date': fields.date('Welcome Documents Sent Date',
                                    track_visibility='onchange'),
        'del_mem_card_date': fields.date('Member Card Sent Date',
                                         track_visibility='onchange'),
        'reference': fields.char('Reference'),
    }

    _defaults = {
        'int_instance_id': lambda self, cr, uid, ids, context = None:
            self.pool.get('int.instance').get_default(cr, uid),
    }

# orm methods

    def copy_data(self, cr, uid, ids, default=None, context=None):
        """
        Do not copy m2m fields.
        """
        default = default or {}
        default.update({
            'int_instance_m2m_ids': [],
        })
        res = super(res_partner, self).copy_data(cr, uid, ids, default=default,
                                                 context=context)
        return res

    def create_workflow(self, cr, uid, ids, context=None):
        '''
        Create workflow only for natural persons
        '''
        dom = [('id', 'in', ids), ('is_company', '=', False)]
        pids = self.search(cr, uid, dom, context=context)
        res = super(res_partner, self).create_workflow(
            cr, uid, pids, context=context)
        return res

    def create(self, cr, uid, vals, context=None):
        '''
        If partner has an identifier then update its followers
        '''
        if not vals.get('is_company', False):
            # Force the state here to avoid a security alert
            # when creating the workflow and updating the first time
            # the state of the new partner
            state_obj = self.pool['membership.state']
            vals.update({
                'membership_state_id': state_obj._state_default_get(
                    cr, uid, context=context),
            })
        res = super(res_partner, self).create(cr, uid, vals, context=context)
        if vals.get('identifier', 0) > 0:
            # do not update followers when simulating partner workflow
            # i.e. identifier = -1 (see get_partner_preview method)
            self._update_follower(cr, SUPERUSER_ID, [res], context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        """
        Create or Delete workflow if necessary (according to the new
        is_company value)
        Invalidate some caches when changing set of instances related to
        the user
        """
        ids = isinstance(ids, (long, int)) and [ids] or ids
        if 'is_company' in vals:
            is_company = vals['is_company']
            data = self.read(cr, uid, ids, ['is_company'], context=context)
            p2d_ids = [
                # wkfs to delete
                d['id'] for d in data if not d['is_company'] and is_company
            ]
            if p2d_ids:
                ml_obj = self.pool['membership.line']
                ml_ids = ml_obj.search(
                    cr, uid, [('partner_id', 'in', p2d_ids)],
                    context=context)
                if ml_ids:
                    raise orm.except_orm(
                        _('Error'),
                        _('A natural person with membership history '
                          'cannot be transformed to a legal person')
                    )
            p2c_ids = [
                # wkfs to create
                d['id'] for d in data if d['is_company'] and not is_company
            ]
            super(res_partner, self).create_workflow(
                cr, uid, p2c_ids, context=context)
            self.delete_workflow(
                cr, uid, p2d_ids, context=context)

            if is_company:
                vals['membership_state_id'] = None

        res = super(res_partner, self).write(
            cr, uid, ids, vals, context=context)

        if 'int_instance_m2m_ids' in vals:
            rule_obj = self.pool['ir.rule']
            rule_obj.clear_cache(cr, uid)

        return res

# view methods: onchange, button

    def decline_payment(self, cr, uid, ids, context=None):
        today = fields.date.today()
        return self.write(cr, uid, ids, {'decline_payment_date': today},
                          context=context)

    def reject(self, cr, uid, ids, context=None):
        today = fields.date.today()
        return self.write(cr, uid, ids, {'rejected_date': today},
                          context=context)

    def exclude(self, cr, uid, ids, context=None):
        today = fields.date.today()
        return self.write(cr, uid, ids, {'exclusion_date': today},
                          context=context)

    def resign(self, cr, uid, ids, context=None):
        today = fields.date.today()
        return self.write(cr, uid, ids, {'resignation_date': today},
                          context=context)

    def button_modification_request(self, cr, uid, ids, context=None):
        """
        Create a `membership.request` object with the datas of the current
        partner. Launch it into the another form view
        """
        if context is None:
            context = {}
        mr_obj = self.pool['membership.request']
        mr_ids = mr_obj.search(
            cr, uid, [('partner_id', 'in', ids),
                      ('state', '=', 'draft')], context=context)
        mr_id = mr_ids and mr_ids[0] or False
        if not mr_id:
            partners = self.browse(cr, uid, ids, context=context)
            partner = partners and partners[0]
            if not partner:
                raise orm.except_orm(
                    _('Error'),
                    _('A Partner is required for a Modification Request'))
            postal_coordinate_id = partner.postal_coordinate_id or False
            mobile_coordinate_id = partner.mobile_coordinate_id or False
            fix_coordinate_id = partner.fix_coordinate_id or False
            email_coordinate_id = partner.email_coordinate_id or False
            int_instance_id = partner.int_instance_id or False
            birth_date = partner.birth_date
            day = False
            month = False
            year = False
            if partner.birth_date:
                datas = partner.birth_date.split('-')
                day = datas[2]
                month = datas[1]
                year = datas[0]

            values = {
                'membership_state_id': partner.membership_state_id and
                partner.membership_state_id.id or False,
                'identifier': partner.identifier,
                'lastname': partner.lastname,
                'firstname': partner.firstname,
                'gender': partner.gender,
                'birth_date': birth_date,
                'day': day,
                'month': month,
                'year': year,
                'is_update': True,
                # country_id is mandatory
                'country_id': postal_coordinate_id and postal_coordinate_id.
                address_id.country_id.id,
                'address_local_street_id': postal_coordinate_id and
                postal_coordinate_id.address_id.address_local_street_id.id,
                'street_man': postal_coordinate_id and postal_coordinate_id.
                address_id.street_man,
                'street2': postal_coordinate_id and postal_coordinate_id.
                address_id.street2,
                'address_local_zip_id': postal_coordinate_id and
                postal_coordinate_id.address_id.address_local_zip_id.id,
                'zip_man': postal_coordinate_id and
                postal_coordinate_id.address_id.zip_man,
                'town_man': postal_coordinate_id and
                postal_coordinate_id.address_id.town_man,
                'box': postal_coordinate_id and
                postal_coordinate_id.address_id.box,
                'number': postal_coordinate_id and
                postal_coordinate_id.address_id.number,
                'mobile': mobile_coordinate_id and
                mobile_coordinate_id.phone_id.name,
                'phone': fix_coordinate_id and fix_coordinate_id.phone_id.name,
                'mobile_id': mobile_coordinate_id and
                mobile_coordinate_id.phone_id.id,
                'phone_id': fix_coordinate_id and
                fix_coordinate_id.phone_id.id,
                'email': email_coordinate_id and email_coordinate_id.email,
                'partner_id': partner.id,
                'address_id': postal_coordinate_id and postal_coordinate_id.
                address_id.id,
                'int_instance_id': int_instance_id and int_instance_id.id,
                'interests_m2m_ids': [[6, False, partner.interests_m2m_ids and
                                       [interest.id for interest in partner.
                                        interests_m2m_ids] or []]],
                'competencies_m2m_ids': [[6, False,
                                          partner.competencies_m2m_ids and
                                          [competence.id for competence in
                                           partner.competencies_m2m_ids] or
                                          []]],
            }
            context['mode'] = 'ws'
            # create mr in sudo mode for portal user allowing to avoid create
            # rights on this model for these users
            u = 'default_open_partner_user' in context and SUPERUSER_ID or uid
            mr_id = mr_obj.create(cr, u, values, context=context)
        return mr_obj.display_object_in_form_view(
            cr, uid, mr_id, context=context)

    def button_reset_del_doc_date(self, cr, uid, ids, context=None):
        vals = {
            'del_doc_date': False,
        }
        self.write(cr, uid, ids, vals, context=context)

    def button_reset_del_mem_card_date(self, cr, uid, ids, context=None):
        vals = {
            'del_mem_card_date': False,
        }
        self.write(cr, uid, ids, vals, context=context)

# workflow

    def update_state(self, cr, uid, ids, membership_state_code, context=None):
        """
        Partner membership_state_id is updated with the `membership.state`\
        having the `code` `membership_state_code`

        :type membership_state_code: char
        :param membership_state_code: code of `membership.state`
        :raise orm.except_orm: If no membership_state_id found with \
        `membership_state_code`
        """

        membership_state_obj = self.pool['membership.state']
        membership_state_ids = membership_state_obj.search(
            cr, uid, [('code', '=', membership_state_code)], context=context)

        if not membership_state_ids:
            raise orm.except_orm(
                _('Error'),
                _('Undefined Membership State: %s') % membership_state_code)

        vals = {
            'membership_state_id': membership_state_ids[0],
            'accepted_date': False,
            'decline_payment_date': False,
            'rejected_date': False,
            'resignation_date': False,
            'exclusion_date': False,
            'customer': membership_state_code in [
                'member_candidate',
                'member_committee',
                'member',
                'former_member',
                'former_member_committee',
            ],
            'reference': False,
        }

        current_reference = self.read(
            cr, uid, ids, ['reference'], context=context)[0]['reference']
        res = self.write(cr, uid, ids, vals, context=context)
        state_id = membership_state_obj._state_default_get(
            cr, uid, context=context)
        default_code = membership_state_obj.read(
            cr, uid, state_id, ['code'], context=context)['code']

        if membership_state_code != default_code:
            self.update_membership_line(
                cr, uid, ids, ref=current_reference, context=context)

        return res

    def update_membership_line(self, cr, uid, ids, ref=False, context=None):
        """
        Search for a `membership.membership_line` for each partner
        If no membership_line exist:
        * then create one
        * else invalidate it updating its `date_to` and duplicate it
          with the right state
        """
        today = fields.date.today()
        values = {
            'date_from': today,
            'date_to': False,
        }
        membership_line_obj = self.pool['membership.line']
        membership_state_obj = self.pool['membership.state']
        def_state = membership_state_obj._state_default_get(cr, uid)
        for partner in self.browse(cr, uid, ids, context=context):
            if partner.is_company:
                continue
            values['state_id'] = partner.membership_state_id.id
            if values['state_id'] != def_state:
                values['int_instance_id'] = partner.int_instance_id and \
                    partner.int_instance_id.id or False,
                values['reference'] = ref
                current_membership_line_ids = membership_line_obj.search(
                    cr, uid, [('partner_id', '=', partner.id),
                              ('active', '=', True)],
                    context=context)
                current_membership_line_id = current_membership_line_ids and \
                    current_membership_line_ids[0] or False

                if current_membership_line_id:
                    # update and copy it
                    vals = {
                        'date_to': today,
                    }
                    membership_line_obj.action_invalidate(
                        cr, uid, [current_membership_line_id],
                        context=context, vals=vals)
                    membership_line_obj.copy(
                        cr, uid, current_membership_line_id, default=values,
                        context=context)
                else:
                    # create first membership_line
                    values.update({
                        'partner_id': partner.id,
                        'date_from': today,
                    })
                    membership_line_obj.create(
                        cr, uid, values, context=context)

    def update_membership_reference(self, cr, uid, ids, context=None):
        '''
        Update reference for each partner ids
        '''
        vals = {}
        for partner_id in ids:
            vals['reference'] = self._generate_membership_reference(
                cr, uid, partner_id, context=context)
            self.write(cr, uid, partner_id, vals, context=context)
