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

from lxml import etree as ET


class ir_model_data(orm.Model):

    _inherit = 'ir.model.data'

    def _update(self, cr, uid, model, module, values, xml_id=False, store=True,
                noupdate=False, mode='init', res_id=False, context=None):

        if model == 'ir.ui.view' and module == 'ficep_help':
            xml_str = self.manageImageReferences(cr, uid,
                                            values['arch'], context=context)
            values['arch'] = xml_str

        return super(ir_model_data, self)._update(cr,
                                                  uid,
                                                  model,
                                                  module,
                                                  values,
                                                  xml_id=xml_id,
                                                  store=store,
                noupdate=noupdate, mode=mode, res_id=res_id, context=context)

    def manageImageReferences(self, cr, uid, xml_str, context=None):
        parser = ET.XMLParser(remove_blank_text=True)
        root = ET.XML(xml_str, parser=parser)
        img_model = 'ir.attachment'
        for img_elem in root.iter('img'):
            if img_model in img_elem.get('src'):
                img_src = img_elem.get('src')
                try:
                    id_pos = img_src.index('id=') + 3
                    xml_id = img_elem.get('src')[id_pos:]
                    img_id = self.get_object_reference(cr,
                                                       uid,
                                                       'ficep_help',
                                                       xml_id)
                    id_pos = img_src.index('id=')
                    attach_id = img_elem.get('src')[id_pos:]
                    img_elem.attrib['src'] = img_src.replace(attach_id,
                                                             "id=" \
                                                             + str(img_id[1]))
                except:
                    continue
        return ET.tostring(root, encoding='utf-8', xml_declaration=False)
