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
from uuid import uuid4
from anybox.testing.openerp import SharedSetupTransactionCase

from openerp.addons.mozaik_address.address_address import COUNTRY_CODE


class test_membership(SharedSetupTransactionCase):

    _data_files = (
        # load the partner
        '../../mozaik_base/tests/data/res_partner_data.xml',
        # load structures
        '../../mozaik_structure/tests/data/structure_data.xml',
        # load address of this partner
        '../../mozaik_address/tests/data/reference_data.xml',
        # load postal_coordinate of this partner
        '../../mozaik_address/tests/data/address_data.xml',
        # load phone_coordinate of this partner
        '../../mozaik_phone/tests/data/phone_data.xml',
        # load terms and requests
        '../../mozaik_thesaurus/tests/data/thesaurus_data.xml',
        'data/membership_request_data.xml',
    )

    _module_ns = 'mozaik_membership'

    def setUp(self):
        super(test_membership, self).setUp()
        self.partner_obj = self.registry['res.partner']

        self.mro = self.registry('membership.request')
        self.mrco = self.registry('membership.request.change')
        self.mrs = self.registry('membership.state')

        self.rec_partner = self.browse_ref(
            '%s.res_partner_thierry' % self._module_ns)
        self.rec_partner_pauline = self.browse_ref(
            '%s.res_partner_pauline' % self._module_ns)
        self.rec_postal = self.browse_ref(
            '%s.postal_coordinate_2_duplicate_2' % self._module_ns)
        self.rec_phone = self.browse_ref(
            '%s.main_mobile_coordinate_two' % self._module_ns)

        self.rec_mr_update = self.browse_ref(
            '%s.membership_request_mp' % self._module_ns)
        self.rec_mr_create = self.browse_ref(
            '%s.membership_request_eh' % self._module_ns)

    def test_pre_process(self):
        """
        Test that input values to create a ``membership.request``
        are found and matched with existing data
        """
        cr, uid, context = self.cr, self.uid, {}

        base_values = {
            'lastname': self.rec_partner.lastname,
            'firstname': self.rec_partner.firstname,
            'gender': self.rec_partner.gender,
            'day': 1,
            'month': 04,
            'year': 1985,

            'request_type': 's',
            'mobile': self.rec_phone.phone_id.name,
        }
        all_values = {
            'street':
            self.rec_postal.address_id.address_local_street_id.local_street,
            'zip_man':
            self.rec_postal.address_id.address_local_zip_id.local_zip,
            'address_local_street_id':
            self.rec_postal.address_id.address_local_street_id.id,
            'box': self.rec_postal.address_id.box,
            'number': self.rec_postal.address_id.number,
            'town_man': self.rec_postal.address_id.address_local_zip_id.town,
        }
        all_values.update(base_values)

        output_values = self.mro.pre_process(
            cr, uid, all_values, context=context)
        self.assertEqual(output_values.get('mobile_id', False),
                         self.rec_phone.phone_id.id,
                         'Should have the same phone that the phone of the \
                         phone coordinate')
        self.assertEqual(output_values.get('address_id', False),
                         self.rec_postal.address_id.id,
                         'Should be the same address')
        self.assertEqual(output_values.get('partner_id', False),
                         self.rec_partner.id, 'Should have the same partner')
        self.assertEqual(
            output_values.get('int_instance_id', False),
            self.rec_postal.address_id.address_local_zip_id.int_instance_id.id,
            'Instance should be the instance of the address local zip')
        output_values = self.mro.pre_process(
            cr, uid, base_values, context=context)
        self.assertEqual(
            output_values.get('int_instance_id', False),
            self.rec_partner.int_instance_id.id,
            'Instance should be the instance of the partner')

    def test_get_address_id(self):
        cr, uid = self.cr, self.uid
        adrs = self.browse_ref('%s.address_3' % self._module_ns)
        address_local_street_id = adrs.address_local_street_id and \
            adrs.address_local_street_id.id
        address_local_zip_id = adrs.address_local_zip_id and \
            adrs.address_local_zip_id.id
        country_id = adrs.country_id and adrs.country_id.id
        technical_name = self.mro.get_technical_name(
            cr, uid, address_local_street_id, address_local_zip_id,
            adrs.number, adrs.box, adrs.town_man, adrs.street_man,
            adrs.zip_man, country_id)
        waiting_adrs_ids = self.registry['address.address'].search(
            cr, uid, [('technical_name', '=', technical_name)])
        waiting_adrs_id = -1
        if waiting_adrs_ids:
            waiting_adrs_id = waiting_adrs_ids[0]
        self.assertEqual(adrs.id, waiting_adrs_id,
                         'Address id Should be the same')

    def test_validate_request(self):
        """
        =====================
        test_validate_request
        =====================
        * Test the validate process with an update and check that
        ** firstname
        ** email_coordinate
        ** new mobile
        * Test the validate process with a create and check that
            relations are created
        """
        cr, uid, context = self.cr, self.uid, {'no_notify': True}
        partner_obj = self.registry['res.partner']

        to_update_partner_id = self.rec_mr_update.partner_id.id

        # validate the membership request
        self.mro.validate_request(
            cr, uid, [self.rec_mr_update.id], context=context)
        modified_partner = partner_obj.browse(cr, uid, to_update_partner_id)

        self.assertEqual(self.rec_mr_update.firstname, modified_partner.
                         firstname, "First name should be updated with same \
                         value of the membership request")
        self.assertEqual(self.rec_mr_update.email, modified_partner.
                         email_coordinate_id.email, "Email should be updated \
                         with same value of the membership request")
        self.assertEqual(self.rec_mr_update.mobile, modified_partner.
                         mobile_coordinate_id.phone_id.name, "Mobile should \
                         be created with same value of the membership request")
        # validation to create
        self.mro.write(
            cr, uid, [self.rec_mr_create.id],
            {'country_id': self.registry('res.country').
             _country_default_get(cr, uid, COUNTRY_CODE)})
        self.mro.validate_request(
            cr, uid, [self.rec_mr_create.id], context=context)
        created_partner_ids = partner_obj.search(
            cr, uid, [('firstname', '=', self.rec_mr_create.firstname),
                      ('lastname', '=', self.rec_mr_create.lastname),
                      ('birth_date', '=', self.rec_mr_create.birth_date), ])
        self.assertEqual(len(created_partner_ids), 1, "Should have one and \
            only one partner")
        created_partner_id = created_partner_ids[0]
        # now test relations
        address_ids = self.registry['address.address'].search(
            cr, uid, [('technical_name', '=',
                       self.rec_mr_create.technical_name)])
        phone_ids = self.registry['phone.phone'].search(
            cr, uid, [('name', '=', self.rec_mr_create.phone),
                      ('type', '=', 'fix')])
        # test address and a phone
        self.assertEqual(len(address_ids), 1, "Should have one and only one \
            address id")
        self.assertEqual(len(phone_ids), 1, "Should have one and only one \
            phone id")

        phone_coordinate_ids = self.registry['phone.coordinate'].search(
            cr, uid, [('partner_id', '=', created_partner_id),
                      ('phone_id', '=', phone_ids[0])])
        # test that we have as well a phone.coordinate
        self.assertEqual(len(phone_coordinate_ids), 1,
                         "Should have one and only one phone_coordinate_id id")

    def test_state_default_get(self):
        """
        Test the default state of `membership.state`
        'without_membership' is used as technical state

        Test default state with another default_state
        """
        mrs, cr, uid, context = self.mrs, self.cr, self.uid, {}

        without_membership_id = mrs._state_default_get(
            cr, uid, context=context)
        uniq_code_membership = mrs.browse(
            cr, uid, without_membership_id, context=context)
        self.assertEqual('without_membership', uniq_code_membership.code,
                         "Code should be without_membership")

        code = '%s' % uuid4()
        mrs.create(
            cr, uid, {'name': 'test_state', 'code': code}, context=context)
        uniq_code_membership_id = mrs._state_default_get(
            cr, uid, default_state=code, context=context)
        uniq_code_membership = mrs.browse(cr, uid, uniq_code_membership_id,
                                          context=context)
        self.assertEqual(code, uniq_code_membership.code,
                         "Code should be %s" % code)

    def test_track_changes(self):
        '''
            Test to valid tracks changes method to detect differences
            between modification request and partner data
        '''
        cr, uid, context = self.cr, self.uid, {}

        request = self.rec_mr_update

        def get_changes():
            changes = {}
            for change in request.change_ids:
                changes[change.field_name] = (change.old_value,
                                              change.new_value)
            return changes

        changes = get_changes()
        self.assertIn('Firstname', changes)
        self.assertIn('Mobile', changes)
        self.assertIn('Gender', changes)
        self.assertIn('Email', changes)
        self.assertIn('Birth Date', changes)

        self.assertEquals(changes['Firstname'][0], 'Pauline')
        self.assertEquals(changes['Firstname'][1], 'Paulinne')
        self.assertFalse(changes['Mobile'][0])
        self.assertEquals(changes['Mobile'][1], '+32 475 45 12 32')
        self.assertFalse(changes['Gender'][0])
        self.assertEquals(changes['Gender'][1], 'Female')
        self.assertFalse(changes['Email'][0])
        self.assertEquals(changes['Email'][1], 'pauline_marois@gmail.com')
        self.assertFalse(changes['Birth Date'][0])
        self.assertEquals(changes['Birth Date'][1], '1949-03-29')

        address_id = request.partner_id.postal_coordinate_id.address_id.id

        self.registry['address.address'].write(cr, uid, address_id,
                                               {'address_local_zip_id': False,
                                                'street_man': 'Street Sample',
                                                'town_man': 'Test Valley'},
                                               context=context)
        changes = get_changes()
        self.assertIn('City', changes)
        self.assertIn('Reference Street', changes)
        self.assertEquals(changes['City'][0], 'Test Valley')
        self.assertEquals(changes['City'][1], 'Oreye')
        self.assertEquals(changes['Reference Street'][0], 'Street Sample')
        self.assertEquals(changes['Reference Street'][1],
                          u'Rue Louis Maréchal')
