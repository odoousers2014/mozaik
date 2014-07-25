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


class test_retrocession_process(object):

    _data_files = (
        '../../l10n_ficep/data/account_ficep.xml',
        '../../l10n_ficep/data/account_chart_template.xml',
        '../../l10n_ficep/data/account_installer.xml',
        '../../ficep_base/tests/data/res_partner_data.xml',
        '../../ficep_structure/tests/data/structure_data.xml',
        '../../ficep_mandate/tests/data/mandate_data.xml',
        'data/retrocession_data.xml',
    )

    _module_ns = 'ficep_retrocession'

    def setUp(self):
        super(test_retrocession_process, self).setUp()
        wiz_id = self.ref('%s.pcmn_ficep' % self._module_ns)
        self.registry('wizard.multi.charts.accounts').execute(self.cr, self.uid, [wiz_id])

        # members to instanciate by real test
        self.retro = None

    def test_retrocession_process(self):
        '''
            Test retrocessions
        '''
        rule_pool = self.registry('calculation.rule')
        retro_pool = self.registry('retrocession')

        fixed_rule_ids = rule_pool.search(self.cr, self.uid, [('retrocession_id', '=', self.retro.id), ('type', '=', 'fixed'), ('is_deductible', '=', False)])
        variable_rule_ids = rule_pool.search(self.cr, self.uid, [('retrocession_id', '=', self.retro.id), ('type', '=', 'variable'), ('is_deductible', '=', False)])
        deductible_rule_ids = rule_pool.search(self.cr, self.uid, [('retrocession_id', '=', self.retro.id), ('type', '=', 'variable'), ('is_deductible', '=', True)])

        '''
            Check if fixed rules have been copied from mandate to retrocession
        '''
        self.assertEqual(len(fixed_rule_ids), 2)

        '''
            Check if variable rules have been copied from method to retrocession
        '''
        rule_ids = rule_pool.search(self.cr, self.uid, [('retrocession_id', '=', self.retro.id), ('type', '=', 'variable')])
        self.assertEqual(len(rule_ids), 2)

        '''
            Setting some amounts on fixed rules should invoke retrocession calculation
        '''
        rule_pool.write(self.cr, self.uid, fixed_rule_ids, {'amount': 100})
        amounts = retro_pool.read(self.cr, self.uid, self.retro.id, ['amount_retrocession', 'amount_total'])
        self.assertEqual(amounts['amount_retrocession'], 3.40)
        self.assertEqual(amounts['amount_total'], 3.40)

        '''
            Setting some amounts on variable rules should invoke retrocession calculation
        '''
        rule_pool.write(self.cr, self.uid, variable_rule_ids, {'amount': 100})
        amounts = retro_pool.read(self.cr, self.uid, self.retro.id, ['amount_retrocession', 'amount_total'])
        self.assertEqual(amounts['amount_retrocession'], 4.15)
        self.assertEqual(amounts['amount_total'], 4.15)

        '''
            Setting some amounts on deductible rules should invoke retrocession calculation
        '''
        rule_pool.write(self.cr, self.uid, deductible_rule_ids, {'amount': 1})
        amounts = retro_pool.read(self.cr, self.uid, self.retro.id, ['amount_retrocession', 'amount_deduction', 'amount_total'])
        self.assertEqual(amounts['amount_retrocession'], 4.15)
        self.assertEqual(amounts['amount_deduction'], -1)
        self.assertEqual(amounts['amount_total'], 3.15)

        '''
            Changing percentage of fixed rules should affect retrocession computation
        '''
        rule_pool.write(self.cr, self.uid, fixed_rule_ids, {'percentage': 0.25})
        amounts = retro_pool.read(self.cr, self.uid, self.retro.id, ['amount_retrocession', 'amount_deduction', 'amount_total'])
        self.assertEqual(amounts['amount_retrocession'], 1.25)
        self.assertEqual(amounts['amount_deduction'], -1)
        self.assertEqual(amounts['amount_total'], 0.25)

        '''
            Changing percentage of variable rules should affect retrocession computation
        '''
        rule_pool.write(self.cr, self.uid, deductible_rule_ids, {'percentage': 5})
        amounts = retro_pool.read(self.cr, self.uid, self.retro.id, ['amount_retrocession', 'amount_deduction', 'amount_total'])
        self.assertEqual(amounts['amount_retrocession'], 1.25)
        self.assertEqual(amounts['amount_deduction'], -0.05)
        self.assertEqual(amounts['amount_total'], 1.20)

        '''
            Validating retrocession
        '''
        retro_pool.action_validate(self.cr, self.uid, [self.retro.id])
        retro_state = retro_pool.read(self.cr, self.uid, self.retro.id, ['state'])['state']
        self.assertEqual(retro_state, 'validated')

        '''
            No computation should occurs
        '''
        rule_pool.write(self.cr, self.uid, fixed_rule_ids, {'percentage': 0.55})
        amounts = retro_pool.read(self.cr, self.uid, self.retro.id, ['amount_total'])
        self.assertEqual(amounts['amount_total'], 1.20)

        '''
            Account move should exist
        '''
        move_id = retro_pool.read(self.cr, self.uid, self.retro.id, ['move_id'])['move_id']
        self.assertNotEqual(move_id, False)

        '''
            Account move should have 3 lines
        '''
        line_ids = self.registry('account.move.line').search(self.cr, self.uid, [('move_id', '=', move_id[0])])
        self.assertEqual(len(line_ids), 3)

        '''
            Analyse lines generated
        '''
        lines = self.registry('account.move.line').search_read(self.cr, self.uid,
                                                             [('move_id', '=', move_id[0]),
                                                              ('account_id', '=', self.retro.default_debit_account.id)],
                                                              fields=['debit', 'credit', 'name'])
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['credit'], 0)
        self.assertEqual(lines[0]['debit'], 0.05)
        self.assertEqual(lines[0]['name'], self.retro.unique_id)

        lines = self.registry('account.move.line').search_read(self.cr, self.uid,
                                                             [('move_id', '=', move_id[0]),
                                                              ('account_id', '=', self.retro.default_credit_account.id)],
                                                              fields=['debit', 'credit', 'name'])
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['credit'], 1.25)
        self.assertEqual(lines[0]['debit'], 0)
        self.assertEqual(lines[0]['name'], self.retro.unique_id)

        default_debit_account_id = self.registry('account.journal').search_read(self.cr, self.uid, [('code', '=', 'RETRO')],
                                                                                        fields=['default_debit_account_id'])[0]['default_debit_account_id']
        lines = self.registry('account.move.line').search_read(self.cr, self.uid,
                                                             [('move_id', '=', move_id[0]),
                                                              ('account_id', '=', default_debit_account_id[0])],
                                                              fields=['debit', 'credit', 'name'])
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['credit'], 0)
        self.assertEqual(lines[0]['debit'], 1.20)
        self.assertEqual(lines[0]['name'], self.retro.unique_id)

        '''
            Reset retrocession
        '''
        retro_pool.action_revalidate(self.cr, self.uid, [self.retro.id])
        retro_state = retro_pool.read(self.cr, self.uid, self.retro.id, ['state'])['state']
        self.assertEqual(retro_state, 'draft')

        '''
            Account move lines should have been unlinked
        '''
        line_ids = self.registry('account.move.line').search(self.cr, self.uid, [('move_id', '=', move_id[0])])
        self.assertEqual(len(line_ids), 0)

        '''
            Account move should have been unlinked
        '''
        move_id = retro_pool.read(self.cr, self.uid, self.retro.id, ['move_id'])['move_id']
        self.assertFalse(move_id)


class test_retrocession_ext_mandate_process(test_retrocession_process, SharedSetupTransactionCase):

    def setUp(self):
        super(test_retrocession_ext_mandate_process, self).setUp()

        self.retro = self.browse_ref('%s.retro_jacques_ag_mai_2014' % self._module_ns)


class test_retrocession_sta_mandate_process(test_retrocession_process, SharedSetupTransactionCase):

    def setUp(self):
        super(test_retrocession_sta_mandate_process, self).setUp()

        self.retro = self.browse_ref('%s.retro_jacques_bourg_mai_2014' % self._module_ns)