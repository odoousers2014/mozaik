# -*- coding: utf-8 -*-
import time
from openerp.osv import osv
from openerp.report import report_sxw


class report_postal_coordinate_label(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_postal_coordinate_label, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'getrow': self._getrow,
            'getpage': self._getpage,
            'closediv': self._closediv,
        })

    def _getrow(self):
        return "<div class='row'>"

    def _getpage(self):
        return "<div class='page'>"

    def _closediv(self):
        return "</div>"


class report_postal_coordinate_label_wrapper(osv.AbstractModel):
    _name = 'report.report_postal_coordinate_label'
    _inherit = 'report.abstract_report'
    _template = 'ficep_address.postal_coordinate_label_report_template'
    _wrapped_report_class = report_postal_coordinate_label

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
