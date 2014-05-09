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
import logging
from anybox.testing.openerp import SharedSetupTransactionCase

_logger = logging.getLogger(__name__)


class test_copy_mandate_wizard(SharedSetupTransactionCase):
    _data_files = (
        '../../ficep_base/tests/data/res_partner_data.xml',
        '../../ficep_structure/tests/data/structure_data.xml',
        'data/mandate_data.xml',
    )

    _module_ns = 'ficep_mandate'

    def setUp(self):
        super(test_copy_mandate_wizard, self).setUp()
        candidature_pool = self.registry('sta.candidature')
        committee_pool = self.registry('sta.selection.committee')
        sta_paul_communal_id = self.ref('%s.sta_paul_communal' % self._module_ns)
        sta_pauline_communal_id = self.ref('%s.sta_pauline_communal' % self._module_ns)
        sta_marc_communal_id = self.ref('%s.sta_marc_communal' % self._module_ns)
        sta_thierry_communal_id = self.ref('%s.sta_thierry_communal' % self._module_ns)
        selection_committee_id = self.ref('%s.sc_tete_huy_communale' % self._module_ns)

        accepted_ids = [sta_thierry_communal_id]
        rejected_ids = [sta_pauline_communal_id, sta_marc_communal_id, sta_paul_communal_id]
        candidature_pool.signal_button_suggest(self.cr, self.uid, accepted_ids)
        candidature_pool.signal_button_reject(self.cr, self.uid, rejected_ids)
        committee_pool.button_accept_candidatures(self.cr, self.uid, [selection_committee_id])
        candidature_pool.signal_button_elected(self.cr, self.uid, accepted_ids)
        candidature_pool.button_create_mandate(self.cr, self.uid, accepted_ids)

    def test_renew_legislative_state_mandate(self):
        '''
        Try to renew a legislative state mandate which is not allowed
        '''
        stam_thierry_communal_2012_id = self.ref('%s.stam_thierry_communal_2012' % self._module_ns)

        context = {
            'active_ids': [stam_thierry_communal_2012_id],
            'active_model': 'sta.mandate',
        }
        wizard_pool = self.registry('copy.sta.mandate.wizard')
        wiz_id = wizard_pool.create(self.cr, self.uid, {}, context=context)
        wizard = wizard_pool.browse(self.cr, self.uid, wiz_id)
        self.assertEqual(wizard.action, 'renew')
        self.assertNotEqual(wizard.message, False, wizard.message)

    def test_renew_non_legislative_state_mandate(self):
        '''
        Renew a non-legislative state mandate
        '''
        stam_thierry_bourgmestre_2012_id = self.ref('%s.stam_thierry_bourgmestre_2012' % self._module_ns)
        legislature_01_id = self.ref('%s.legislature_01' % self._module_ns)
        mandate_pool = self.registry('sta.mandate')

        context = {
            'active_ids': [stam_thierry_bourgmestre_2012_id],
            'active_model': 'sta.mandate',
        }
        wizard_pool = self.registry('copy.sta.mandate.wizard')
        wiz_id = wizard_pool.create(self.cr, self.uid, {}, context=context)
        wizard = wizard_pool.browse(self.cr, self.uid, wiz_id)
        self.assertEqual(wizard.action, 'renew')
        self.assertEqual(wizard.message, False)
        self.assertEqual(wizard.legislature_id.id, legislature_01_id)
        data = wizard_pool.onchange_legislature_id(self.cr, self.uid, [wiz_id], wizard.legislature_id.id, context=context)
        values = dict(start_date=data['value']['start_date'],
                      deadline_date=data['value']['deadline_date'])
        wizard_pool.write(self.cr, self.uid, wiz_id, values)
        res = wizard_pool.renew_mandate(self.cr, self.uid, [wiz_id], context=context)
        new_mandate_id = res['res_id']
        self.assertNotEqual(new_mandate_id, False)

        base_mandate = mandate_pool.browse(self.cr, self.uid, stam_thierry_bourgmestre_2012_id)
        new_mandate = mandate_pool.browse(self.cr, self.uid, new_mandate_id)

        self.assertEqual(base_mandate.partner_id, new_mandate.partner_id)
        self.assertEqual(base_mandate.mandate_category_id, new_mandate.mandate_category_id)
        self.assertNotEqual(base_mandate.legislature_id, new_mandate.legislature_id)
        self.assertEqual(base_mandate.sta_assembly_id, new_mandate.sta_assembly_id)
        self.assertEqual(base_mandate.is_submission_mandate, new_mandate.is_submission_mandate)
        self.assertEqual(base_mandate.is_submission_assets, new_mandate.is_submission_assets)
        self.assertEqual(base_mandate.is_replacement, new_mandate.is_replacement)
        self.assertNotEqual(base_mandate.candidature_id, new_mandate.candidature_id)

    def test_create_complementary_state_mandate(self):
        '''
        Create complementary mandate from an existing
        '''
        mandate_pool = self.registry('sta.mandate')
        sta_thierry_communal_id = self.ref('%s.sta_thierry_communal' % self._module_ns)
        mc_bourgmestre_id = self.ref('%s.mc_bourgmestre' % self._module_ns)
        college_assembly_id = self.ref('%s.sta_assembly_03' % self._module_ns)
        mandate_id = mandate_pool.search(self.cr, self.uid, [('candidature_id', '=', sta_thierry_communal_id)])[0]

        context = {
            'active_ids': [mandate_id],
            'active_model': 'sta.mandate',
        }

        wizard_pool = self.registry('copy.sta.mandate.wizard')
        wiz_id = wizard_pool.create(self.cr, self.uid, {}, context=context)
        wizard = wizard_pool.browse(self.cr, self.uid, wiz_id)
        self.assertEqual(wizard.action, 'add')
        self.assertEqual(wizard.message, False)

        data = wizard_pool.onchange_legislature_id(self.cr, self.uid, [wiz_id], wizard.legislature_id.id, context=context)
        values = dict(start_date=data['value']['start_date'],
                      deadline_date=data['value']['deadline_date'],
                      new_mandate_category_id=mc_bourgmestre_id,
                      new_assembly_id=college_assembly_id)
        wizard_pool.write(self.cr, self.uid, wiz_id, values)

        res = wizard_pool.add_mandate(self.cr, self.uid, [wiz_id], context=context)
        new_mandate_id = res['res_id']
        self.assertNotEqual(new_mandate_id, False)

        base_mandate = mandate_pool.browse(self.cr, self.uid, mandate_id)
        new_mandate = mandate_pool.browse(self.cr, self.uid, new_mandate_id)

        self.assertEqual(base_mandate.partner_id, new_mandate.partner_id)
        self.assertNotEqual(base_mandate.mandate_category_id, new_mandate.mandate_category_id)
        self.assertEqual(base_mandate.legislature_id, new_mandate.legislature_id)
        self.assertNotEqual(base_mandate.sta_assembly_id, new_mandate.sta_assembly_id)
        self.assertEqual(base_mandate.is_submission_mandate, new_mandate.is_submission_mandate)
        self.assertEqual(base_mandate.is_submission_assets, new_mandate.is_submission_assets)
        self.assertEqual(base_mandate.is_replacement, new_mandate.is_replacement)
        self.assertNotEqual(base_mandate.candidature_id, new_mandate.candidature_id)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: