# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of mozaik_retrocession, an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     mozaik_retrocession is free software:
#     you can redistribute it and/or
#     modify it under the terms of the GNU Affero General Public License
#     as published by the Free Software Foundation, either version 3 of
#     the License, or (at your option) any later version.
#
#     mozaik_retrocession is distributed in the hope that it will
#     be useful but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the
#     GNU Affero General Public License
#     along with mozaik_retrocession.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.tools.translate import _
from openerp.osv import orm, fields
from openerp.tools import SUPERUSER_ID
from .structure import sta_assembly, ext_assembly
from openerp.addons.mozaik_retrocession.common import \
    RETROCESSION_MODES_AVAILABLE, CALCULATION_METHOD_AVAILABLE_TYPES


class mandate_category(orm.Model):

    _name = 'mandate.category'
    _description = 'Mandate Category'
    _inherit = ['mandate.category']

    def get_linked_sta_mandate_ids(self, cr, uid, ids, context=None):
        return super(
            mandate_category,
            self).get_linked_sta_mandate_ids(
            cr,
            uid,
            ids,
            context=context)

    def get_linked_ext_mandate_ids(self, cr, uid, ids, context=None):
        return super(
            mandate_category,
            self).get_linked_ext_mandate_ids(
            cr,
            uid,
            ids,
            context=context)

    def _check_retro_instance_on_assemblies(
            self,
            cr,
            uid,
            ids,
            for_unlink=False,
            context=None):
        """
        ==============
        _check_retro_instance_on_assemblies
        ==============
        Check if a retrocession management instance is set on all impacted
        assemblie
        :rparam: True if it is the case
                 False otherwise
        :rtype: boolean
        """
        uid = SUPERUSER_ID
        for category in self.browse(cr, uid, ids, context=context):
            if category.retrocession_mode != 'none':
                if category.type == 'sta':
                    assembly_cat_id = category['sta_assembly_category_id'].id
                    assembly_model = 'sta.assembly'
                elif category.type == 'ext':
                    assembly_cat_id = category['ext_assembly_category_id'].id
                    assembly_model = 'ext.assembly'
                else:
                    continue

                assembly_ids = self.pool.get(assembly_model).search(
                    cr, uid, [
                        ('assembly_category_id', '=', assembly_cat_id),
                        ('retro_instance_id', '=', False)],
                    context=context)
                if len(assembly_ids) > 0:
                    return False

        return True

    _columns = {
        'fractionation_id': fields.many2one(
            'fractionation',
            string='Fractionation',
            select=True,
            track_visibility='onchange'),
        'calculation_method_id': fields.many2one(
            'calculation.method',
            string='Calculation Method',
            select=True,
            track_visibility='onchange'),
        'retrocession_mode': fields.selection(
            RETROCESSION_MODES_AVAILABLE,
            'Retrocession Mode',
            required=True,
            track_visibility='onchange'),
    }

    _defaults = {
        'retrocession_mode': RETROCESSION_MODES_AVAILABLE[2][0],
    }

    _constraints = [
        (_check_retro_instance_on_assemblies,
         _("Some impacted assemblies has no retrocessions management "
           "instance!"),
            ['retrocession_mode'])]


class abstract_mandate_retrocession(orm.AbstractModel):
    _name = 'abstract.mandate.retrocession'
    _description = 'Abstract Mandate for retrocession'
    _inherit = ['abstract.mandate']

    _inactive_cascade = True
    _retrocession_foreign_key = False
    _assembly_foreign_key = False
    _assembly_model = False

    _method_id_store_trigger = {}
    _retrocession_mode_store_trigger = {}

    def _get_method_id(self, cr, uid, ids, fname, arg, context=None):
        """
        =================
        _get_method_id
        =================
        Get id of calculation method
        :rparam: id of calculation method
        :rtype: integer
        """
        res = {}
        for mandate in self.browse(cr, uid, ids, context=context):
            cat_method = mandate.mandate_category_id.calculation_method_id
            ass_method = mandate[
                self._assembly_foreign_key].calculation_method_id

            if ass_method:
                method_id = ass_method.id
            elif cat_method:
                method_id = cat_method.id
            else:
                method_id = False
            res[mandate.id] = method_id
        return res

    def _has_retrocessions_linked(self, cr, uid, ids, fname, arg,
                                  context=None):
        """
        =========================
        has_retrocessions_linked
        =========================
        Return whether retrocessions are linked to mandate or not
        :rparam: True if this is the case else False
        :rtype: Boolean
        """
        res = {}
        for mandate_id in ids:
            nb_retro = len(
                self.pool.get('retrocession').search(
                    cr, uid, [
                        (self._retrocession_foreign_key, '=', mandate_id)],
                    context=context))
            res[mandate_id] = True if nb_retro > 0 else False
        return res

    def _need_account_management(self, cr, uid, ids, fname, arg, context=None):
        """
        ========================
        _need_account_management
        ========================
        Determine whether retrocession of mandate need account management or
        not
        :rparam: True if accounting management needed otherwise False
        :rtype: Boolean
        """
        res = {}
        for mandate in self.browse(cr, uid, ids, context=context):
            val = False
            if mandate.retrocession_mode != 'none':
                default = self.pool['int.instance'].get_default(
                    cr, uid, context=context)
                val = mandate.retro_instance_id.id == default
            res[mandate.id] = val

        return res

    _columns = {
        'retrocession_mode': fields.related(
            'mandate_category_id',
            'retrocession_mode',
            string='Retrocession Mode',
            type='selection',
            selection=RETROCESSION_MODES_AVAILABLE,
            store=_retrocession_mode_store_trigger),
        'calculation_method_id': fields.function(
            _get_method_id,
            string='Calculation Method',
            type='many2one',
            relation="calculation.method",
            select=True,
            store=_method_id_store_trigger),
        'method_type': fields.related(
            'calculation_method_id',
            'type',
            string='Calculation Method Type',
            type='selection',
            selection=CALCULATION_METHOD_AVAILABLE_TYPES,
            store=_method_id_store_trigger),
        'has_retrocessions_linked': fields.function(
            _has_retrocessions_linked,
            string='Has Retrocessions',
            type='boolean',
            store=False),
        'retro_instance_id': fields.many2one(
            'int.instance',
            'Retrocessions Management Instance',
            select=True,
            track_visibility='onchange'),
        'reference': fields.char(
            'Communication',
            size=64,
            help="The mandate reference for payments."),
        'email_date': fields.date('Last email Sent'),
        'need_account_management': fields.function(
            _need_account_management,
            string='Need accounting management',
            type='boolean',
            store=False),
    }

# orm methods

    def create(self, cr, uid, vals, context=None):
        context = context or {}

        if 'retrocession_mode' not in vals:
            mandate_category_id = vals['mandate_category_id']
            category = self.pool.get('mandate.category').browse(
                cr,
                uid,
                mandate_category_id)
            vals['retrocession_mode'] = category.retrocession_mode

        if ('retro_instance_id' not in vals or vals[
                'retro_instance_id']):
            assembly_id = vals[self._assembly_foreign_key]
            assembly = self.pool.get(
                self._assembly_model).browse(
                cr,
                uid,
                assembly_id)
            vals['retro_instance_id'] = assembly.retro_instance_id.id

        res = super(
            abstract_mandate_retrocession,
            self).create(
            cr,
            uid,
            vals,
            context=context)

        if res:
            reference = self.generate_mandate_reference(cr, uid, res)
            self.write(cr, uid, res, {'reference': reference}, context=context)

        if res and vals['retrocession_mode'] != 'none' \
                and vals.get('active', True):
            mandate = self.browse(cr, uid, res, context=context)
            if mandate.calculation_method_id:
                self.pool['calculation.method'].copy_fixed_rules_on_mandate(
                    cr, uid, mandate.calculation_method_id.id,
                    mandate.id, self._retrocession_foreign_key,
                    context=context)

            if not context.get('install_mode', False):
                # do not send mails during mass loading (e.g. migration)
                self.send_email_for_reference(cr, uid, [res], context=context)

        return res

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]

        if self._assembly_foreign_key in vals or 'mandate_category_id' in vals:
            dataset = self.read(
                cr,
                uid,
                ids,
                ['calculation_method_id'],
                context=context)
            method_dict = {}
            for value in dataset:
                method_dict[
                    value['id']] = value[
                        'calculation_method_id'][0] if isinstance(
                    value['calculation_method_id'],
                    tuple) else False

        res = super(
            abstract_mandate_retrocession,
            self).write(
            cr,
            uid,
            ids,
            vals,
            context=context)
        if self._assembly_foreign_key in vals or 'mandate_category_id' in vals:
            for mandate in self.browse(cr, uid, ids, context=context):
                calculation_method = mandate.calculation_method_id
                mandate_method_id = False
                if calculation_method:
                    mandate_method_id = calculation_method.id
                if mandate.id in method_dict and method_dict[
                        mandate.id] != mandate_method_id:
                    self.pool[
                        'calculation.method'].copy_fixed_rules_on_mandate(
                        cr,
                        uid,
                        mandate.calculation_method_id.id,
                        mandate.id,
                        self._retrocession_foreign_key,
                        context=context)
        return res

# public methods

    def need_mail_for_payment_reference(self, cr, uid, mandate_id,
                                        context=None):
        """
        This method is intended to be overriden regarding
        locale conventions.
        It returns a boolean indicating whether a mail is send
        to representative containing its mandate payment reference
        Here is an arbitrary convention: True
        """
        return True

    def generate_mandate_reference(self, cr, uid, mandate_id, context=None):
        """
        This method is intended to be overriden regarding
        locale conventions.
        It builds the reference for payment (i.e. structured communication)
        related to the mandate
        Here is an arbitrary convention: "RC: <mandate_unique_id>"
        """
        unique_id = self.read(
            cr, uid, mandate_id, ['unique_id'], context=context)['unique_id']
        ref = 'RC: %s' % unique_id
        return ref

    def get_retro_instance_id(self, cr, uid, assembly_id, context=None):
        if assembly_id:
            assembly = self.pool.get(
                self._assembly_model).browse(
                cr,
                uid,
                assembly_id)
            return assembly.retro_instance_id.id

        return False

    def send_email_for_reference(self, cr, uid, ids, context=None):
        """
        Send an email to partner to communicate reference for payments
        """
        ir_model_data = self.pool['ir.model.data']
        template_ref = False
        if self._assembly_model == 'sta.assembly':
            template_ref = 'email_template_sta_mandate_reference'
        else:
            template_ref = 'email_template_ext_mandate_reference'

        try:
            template_id = ir_model_data.get_object_reference(
                cr, uid, 'mozaik_retrocession', template_ref)[1]
        except ValueError:
            raise orm.except_orm(
                _('Error'),
                _('Email template %s not found!') % template_ref)

        # Remove navigation history: maybe we're coming from partner
        ctx = dict(context or {})
        ctx.pop('active_model', None)
        ctx.pop('active_id', None)
        ctx.pop('active_ids', None)
        for mandate in self.browse(cr, uid, ids, context=ctx):
            if not self.need_mail_for_payment_reference(
               cr, uid, mandate.id, context=ctx):
                continue
            composer = self.pool['mail.compose.message']
            mail_composer_vals = {'parent_id': False,
                                  'use_active_domain': False,
                                  'composition_mode': 'mass_mail',
                                  'partner_ids': [[6, False,
                                                   [mandate.partner_id.id]]],
                                  'notify': False,
                                  'template_id': template_id,
                                  'model': self._name,
                                  'record_name': mandate.display_name,
                                  'res_id': mandate.id,
                                  }
            value = composer.onchange_template_id(
                cr, uid, mandate.id, template_id, 'mass_mail',
                False, False,
                context=ctx)['value']
            value['email_from'] = composer._get_default_from(
                cr, uid, context=ctx)
            mail_composer_vals.update(value)
            mail_composer_id = composer.create(
                cr, uid, mail_composer_vals, context=ctx)
            composer.send_mail(cr, uid, [mail_composer_id], context=ctx)
            self.write(cr, uid, mandate.id,
                       {'email_date': fields.date.today()}, context=ctx)


class sta_mandate(orm.Model):
    _name = 'sta.mandate'
    _description = 'State Mandate'
    _inherit = ['sta.mandate', 'abstract.mandate.retrocession']

    _retrocession_foreign_key = 'sta_mandate_id'
    _assembly_foreign_key = 'sta_assembly_id'
    _assembly_model = 'sta.assembly'

    def _get_method_id(self, cr, uid, ids, fname, arg, context=None):
        return super(
            sta_mandate,
            self)._get_method_id(
            cr,
            uid,
            ids,
            fname,
            arg,
            context=context)

    def _has_retrocessions_linked(self, cr, uid, ids, fname, arg,
                                  context=None):
        return super(
            sta_mandate,
            self)._has_retrocessions_linked(
            cr,
            uid,
            ids,
            fname,
            arg,
            context=context)

    _method_id_store_trigger = {
        'sta.mandate': (
            lambda self, cr, uid, ids, context=None: ids, [
                'sta_assembly_id', 'mandate_category_id'], 20),
        'mandate.category': (
            mandate_category.get_linked_sta_mandate_ids,
            ['calculation_method_id'], 20),
        'sta.assembly': (
            sta_assembly.get_linked_sta_mandate_ids,
            ['calculation_method_id'], 20), }

    _retrocession_mode_store_trigger = {
        'sta.mandate': (
            lambda self,
            cr,
            uid,
            ids,
            context=None: ids,
            ['mandate_category_id'],
            20),
        'mandate.category': (
            mandate_category.get_linked_sta_mandate_ids,
            ['retrocession_mode'],
            20),
    }

    _columns = {
        'retrocession_mode': fields.related(
            'mandate_category_id',
            'retrocession_mode',
            string='Retrocession Mode',
            type='selection',
            selection=RETROCESSION_MODES_AVAILABLE,
            store=_retrocession_mode_store_trigger),
        'calculation_method_id': fields.function(
            _get_method_id,
            string='Calculation Method',
            type='many2one',
            relation="calculation.method",
            select=True,
            store=_method_id_store_trigger),
        'method_type': fields.related(
            'calculation_method_id',
            'type',
            string='Calculation Method Type',
            type='selection',
            selection=CALCULATION_METHOD_AVAILABLE_TYPES,
            store=_method_id_store_trigger),
        'rule_ids': fields.one2many(
            'calculation.rule',
            'sta_mandate_id',
            'Imputable Fixed Rules',
            domain=[
                ('active',
                 '=',
                 True),
                ('is_deductible',
                 '=',
                 False)]),
        'rule_inactive_ids': fields.one2many(
            'calculation.rule',
            'sta_mandate_id',
            'Imputable Fixed Rules',
            domain=[
                ('active',
                 '=',
                 False),
                ('is_deductible',
                 '=',
                 False)]),
        'deductible_rule_ids': fields.one2many(
            'calculation.rule',
            'sta_mandate_id',
            'Deductible Fixed Rules',
            domain=[
                ('active',
                 '=',
                 True),
                ('is_deductible',
                 '=',
                 True)]),
        'deductible_rule_inactive_ids': fields.one2many(
            'calculation.rule',
            'sta_mandate_id',
            'Fixed Calculation Rules',
            domain=[
                ('active',
                 '=',
                 False),
                ('is_deductible',
                 '=',
                 True)]),
    }

    def onchange_sta_assembly_id(
            self,
            cr,
            uid,
            ids,
            sta_assembly_id,
            context=None):
        res = super(
            sta_mandate,
            self).onchange_sta_assembly_id(
            cr,
            uid,
            ids,
            sta_assembly_id,
            context=context)
        res['value']['retro_instance_id'] = self.get_retro_instance_id(
            cr,
            uid,
            sta_assembly_id,
            context=context)

        return res

    def onchange_mandate_category_id(
            self,
            cr,
            uid,
            ids,
            mandate_category_id,
            context=None):
        res = super(
            sta_mandate,
            self).onchange_mandate_category_id(
            cr,
            uid,
            ids,
            mandate_category_id,
            context=context)

        if mandate_category_id:
            category_data = self.pool.get('mandate.category').read(
                cr,
                uid,
                mandate_category_id,
                ['retrocession_mode'],
                context)
            retrocession_mode = category_data['retrocession_mode'] or False

            res['value']['retrocession_mode'] = retrocession_mode
        return res


class ext_mandate(orm.Model):
    _name = 'ext.mandate'
    _description = 'External Mandate'
    _inherit = ['ext.mandate', 'abstract.mandate.retrocession']

    _inactive_cascade = True
    _retrocession_foreign_key = 'ext_mandate_id'
    _assembly_foreign_key = 'ext_assembly_id'
    _assembly_model = 'ext.assembly'

    def _get_method_id(self, cr, uid, ids, fname, arg, context=None):
        return super(
            ext_mandate,
            self)._get_method_id(
            cr,
            uid,
            ids,
            fname,
            arg,
            context=context)

    def _has_retrocessions_linked(self, cr, uid, ids, fname, arg,
                                  context=None):
        return super(
            ext_mandate,
            self)._has_retrocessions_linked(
            cr,
            uid,
            ids,
            fname,
            arg,
            context=context)

    _method_id_store_trigger = {
        'ext.mandate': (
            lambda self, cr, uid, ids, context=None: ids, [
                'ext_assembly_id', 'mandate_category_id'], 20),
        'mandate.category': (
            mandate_category.get_linked_ext_mandate_ids,
            ['calculation_method_id'], 20),
        'ext.assembly': (
            ext_assembly.get_linked_ext_mandate_ids,
            ['calculation_method_id'], 20), }

    _retrocession_mode_store_trigger = {
        'ext.mandate': (
            lambda self,
            cr,
            uid,
            ids,
            context=None: ids,
            ['mandate_category_id'],
            20),
        'mandate.category': (
            mandate_category.get_linked_ext_mandate_ids,
            ['retrocession_mode'],
            20),
    }

    _columns = {
        'retrocession_mode': fields.related(
            'mandate_category_id',
            'retrocession_mode',
            string='Retrocession Mode',
            type='selection',
            selection=RETROCESSION_MODES_AVAILABLE,
            store=_retrocession_mode_store_trigger),
        'calculation_method_id': fields.function(
            _get_method_id,
            string='Calculation Method',
            type='many2one',
            relation="calculation.method",
            select=True,
            store=_method_id_store_trigger),
        'method_type': fields.related(
            'calculation_method_id',
            'type',
            string='Calculation Method Type',
            type='selection',
            selection=CALCULATION_METHOD_AVAILABLE_TYPES,
            store=_method_id_store_trigger),
        'rule_ids': fields.one2many(
            'calculation.rule',
            'ext_mandate_id',
            'Imputable Fixed Rules',
            domain=[
                ('active',
                 '=',
                 True),
                ('is_deductible',
                 '=',
                 False)]),
        'rule_inactive_ids': fields.one2many(
            'calculation.rule',
            'ext_mandate_id',
            'Imputable Fixed Rules',
            domain=[
                ('active',
                 '=',
                 False),
                ('is_deductible',
                 '=',
                 False)]),
        'deductible_rule_ids': fields.one2many(
            'calculation.rule',
            'ext_mandate_id',
            'Deductible Fixed Rules',
            domain=[
                ('active',
                 '=',
                 True),
                ('is_deductible',
                 '=',
                 True)]),
        'deductible_rule_inactive_ids': fields.one2many(
            'calculation.rule',
            'ext_mandate_id',
            'Fixed Calculation Rules',
            domain=[
                ('active',
                 '=',
                 False),
                ('is_deductible',
                 '=',
                 True)]),
    }

    def onchange_ext_assembly_id(
            self,
            cr,
            uid,
            ids,
            ext_assembly_id,
            context=None):
        res = super(
            ext_mandate,
            self).onchange_ext_assembly_id(
            cr,
            uid,
            ids,
            ext_assembly_id,
            context=context)
        res['value']['retro_instance_id'] = self.get_retro_instance_id(
            cr,
            uid,
            ext_assembly_id,
            context=context)

        return res

    def onchange_mandate_category_id(
            self,
            cr,
            uid,
            ids,
            mandate_category_id,
            context=None):
        res = super(
            ext_mandate,
            self).onchange_mandate_category_id(
            cr,
            uid,
            ids,
            mandate_category_id,
            context=context)

        if mandate_category_id:
            category_data = self.pool.get('mandate.category').read(
                cr,
                uid,
                mandate_category_id,
                ['retrocession_mode'],
                context)
            retrocession_mode = category_data['retrocession_mode'] or False

            res['value']['retrocession_mode'] = retrocession_mode
        return res
