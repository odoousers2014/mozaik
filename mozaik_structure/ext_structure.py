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


class ext_assembly_category(orm.Model):

    _name = 'ext.assembly.category'
    _inherit = ['abstract.assembly.category']
    _description = 'External Assembly Category'

    _columns = {
        'power_level_id': fields.many2one('int.power.level',
                                          'Internal Power Level',
                                          track_visibility='onchange'),
    }


class ext_assembly(orm.Model):

    _name = 'ext.assembly'
    _inherit = ['abstract.assembly']
    _description = "External Assembly"

    _category_model = 'ext.assembly.category'

    def _compute_dummy(self, cursor, uid, ids, fname, arg, context=None):
        res = {}
        assemblies = self.browse(cursor, uid, ids, context=context)
        for ass in assemblies:
            fullname = "%s (%s) " % (ass.ref_partner_id.name,
                                     ass.assembly_category_id.name)
            res[ass.id] = fullname
            self.pool['res.partner'].write(cursor, uid, ass.partner_id.id,
                                           {'name': fullname}, context=context)
        return res

    _name_store_triggers = {
        'ext.assembly': (lambda self, cr, uid, ids, context=None: ids,
                         ['ref_partner_id', 'assembly_category_id', ], 10),
        'res.partner': (lambda self, cr, uid, ids, context=None:
                        self.pool['ext.assembly'].search(cr, uid,
                                            [('ref_partner_id', 'in', ids)],
                                            context=context),
                         ['lastname', ], 10),
        'ext.assembly.category': (lambda self, cr, uid, ids, context=None:
                        self.pool['ext.assembly'].search(cr, uid,
                                  [('assembly_category_id', 'in', ids)],
                                  context=context),
                                  ['name', ], 10),
    }

    _columns = {
        # dummy: define a dummy function to update the partner name associated
        #        to the assembly
        'dummy': fields.function(_compute_dummy,
                                 string="Dummy",
                                 type="char",
                                 store=_name_store_triggers,
                                 select=True),
        'assembly_category_id': fields.many2one(_category_model,
                                                'Assembly Category',
                                                select=True,
                                                required=True,
                                                track_visibility='onchange'),
        'instance_id': fields.many2one('int.instance',
                                       'Internal Instance',
                                       select=True,
                                       required=True,
                                       track_visibility='onchange'),
        'designation_int_assembly_id': fields.many2one(
                                       'int.assembly',
                                       string='Designation Assembly',
                                       select=True,
                                       track_visibility='onchange',
                                       domain=[
                                       ('is_designation_assembly', '=', True)
                                       ]),
        'ref_partner_id': fields.many2one('res.partner',
                                          string='Legal Person',
                                          select=True,
                                          required=True,
                                          ondelete='restrict',
                                          track_visibility='onchange'),
    }

    _defaults = {
        'instance_id': lambda self, cr, uid, ids, context=None:
                    self.pool.get('int.instance').get_default(cr, uid)
    }

# constraints

    _unicity_keys = 'ref_partner_id, assembly_category_id'

# orm methods

    def create(self, cr, uid, vals, context=None):
        '''
        Produce the first value of the name field.
        Next values are generated by the function _compute_dummy
        '''
        if not vals.get('name') and not vals.get('partner_id'):
            instance = ''
            if vals.get('ref_partner_id'):
                instance = self.pool['res.partner'].read(cr, uid,
                        vals.get('ref_partner_id'), ['name'], context=context)
            category = ''
            if vals.get('assembly_category_id'):
                category = self.pool['ext.assembly.category'].read(cr, uid,
                        vals.get('assembly_category_id'), ['name'],
                                 context=context)
            vals['name'] = '%s (%s)' % (instance['name'], category['name'])
        res = super(ext_assembly, self).create(cr, uid, vals, context=context)
        return res

    # view methods: onchange, button
    def onchange_assembly_category_id(self, cr, uid, ids, assembly_category_id,
                                      context=None):
        return super(ext_assembly, self).onchange_assembly_category_id(
                        cr, uid, ids, assembly_category_id, context=context)