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
from openerp import http
from openerp.addons.web.controllers import main

from openerp.addons.ficep_base.abstract_ficep import format_email
from openerp.addons.ficep_person.res_partner import available_genders,\
    available_civil_status, available_tongues


class Mobile(main.Home):

    # partner per page
    _PPG = 10

    @http.route(['/partner_mobile',
                '/partner_mobile/page/<int:page>'],
                auth='public', website=True)
    def index_ficep_mobile(self, page=1, **kw):
        """
        Index provides the list of partner
        Manage a pager too
        """
        cr, uid = http.request.cr, http.request.uid,
        context = http.request.context
        partner_obj = http.request.registry['res.partner']

        partner_count = partner_obj.search_count(cr, uid, [], context=context)
        url = "/partner_mobile"
        pager = http.request.website.pager(
            url=url, total=partner_count, page=page, step=self._PPG, scope=4,
            url_args=kw)
        partner_ids = partner_obj.search(
            cr, uid, [], offset=pager['offset'], limit=self._PPG,
            context=context)
        partners = partner_obj.browse(cr, uid, partner_ids, context=context)
        return http.request.render(
            'ficep_mobile.mobile_index', {
                "pager": pager,
                "partners": partners,
            })

    @http.route('/partner_view/<model("res.partner"):partner>/',
                auth='public', website=True)
    def show_partner(self, partner, **kw):
        """
        :type partner: browse record of partner
        :rparam: render of qweb with all main informations of a partner
        """
        cr, uid, = http.request.cr, http.request.uid
        context = http.request.context
        # get email_coordinate records
        email_coordinate_obj = http.request.registry['email.coordinate']
        email_coordinate_ids = email_coordinate_obj.search(
            cr, uid, [('partner_id', '=', partner.id)], context=context)
        email_coordinate_records = email_coordinate_obj.browse(
            cr, uid, email_coordinate_ids, context=context)
        # get phone_coordinate records
        phone_coordinate_obj = http.request.registry['phone.coordinate']
        phone_coordinate_ids = phone_coordinate_obj.search(
            cr, uid, [('partner_id', '=', partner.id)], context=context)
        phone_coordinate_records = phone_coordinate_obj.browse(
            cr, uid, phone_coordinate_ids, context=context)
        # get postal_coordinate records
        postal_coordinate_obj = http.request.registry['postal.coordinate']
        postal_coordinate_ids = postal_coordinate_obj.search(
            cr, uid, [('partner_id', '=', partner.id)], context=context)
        postal_coordinate_records = postal_coordinate_obj.browse(
            cr, uid, postal_coordinate_ids, context=context)
        # get state_mandate records
        sta_mandate_obj = http.request.registry['sta.mandate']
        sta_mandate_ids = sta_mandate_obj.search(
            cr, uid, [('partner_id', '=', partner.id)], context=context)
        sta_mandate_records = sta_mandate_obj.browse(
            cr, uid, sta_mandate_ids, context=context)
        # get internal_mandate records
        int_mandate_obj = http.request.registry['int.mandate']
        int_mandate_ids = int_mandate_obj.search(
            cr, uid, [('partner_id', '=', partner.id)], context=context)
        int_mandate_records = int_mandate_obj.browse(
            cr, uid, int_mandate_ids, context=context)
        # get state_mandate records
        ext_mandate_obj = http.request.registry['ext.mandate']
        ext_mandate_ids = ext_mandate_obj.search(
            cr, uid, [('partner_id', '=', partner.id)], context=context)
        ext_mandate_records = ext_mandate_obj.browse(
            cr, uid, ext_mandate_ids, context=context)
        # relation
        relation_obj = http.request.registry['partner.relation']
        # subject relation
        subject_relation_ids = relation_obj.search(
            cr, uid, [('subject_partner_id', '=', partner.id)],
            context=context)
        subject_relation_records = relation_obj.browse(
            cr, uid, subject_relation_ids, context=context)
        # object relation
        object_relation_ids = relation_obj.search(
            cr, uid, [('object_partner_id', '=', partner.id)], context=context)
        object_relation_records = relation_obj.browse(
            cr, uid, object_relation_ids, context=context)

        to_show_phone_coo = False
        for phone_coo in phone_coordinate_records:
            if not phone_coo.is_main:
                to_show_phone_coo = True
                break
        vals = {
            'partner': partner,
            'to_show_phone_coo': to_show_phone_coo,
            'email_coordinates': email_coordinate_records,
            'postal_coordinates': postal_coordinate_records,
            'phone_coordinates': phone_coordinate_records,
            'available_genders': available_genders,
            'available_tongues': available_tongues,
            'available_civil_status': available_civil_status,
            'subject_relation_records': subject_relation_records,
            'object_relation_records': object_relation_records,
            'sta_mandate_records': sta_mandate_records,
            'int_mandate_records': int_mandate_records,
            'ext_mandate_records': ext_mandate_records,
        }
        return http.request.render('ficep_mobile.show_partner', vals)

    @http.route('/partner_search_form/', auth='public', website=True)
    def partner_search_form(self, **kw):
        """
        Get qweb form to make a search
        """
        return http.request.render('ficep_mobile.partner_search_form')

    @http.route('/partner_search_action/', type='http', auth='public',
                website=True)
    def partner_search_action(self, **kw):
        """
        Make a specific search with the passing value into the form
        :param http.request.params: contain search criteria and the value to
        search on
        Call the qweb index with the resulting list of partner records
        """
        cr, uid = http.request.cr, http.request.uid
        context = http.request.context
        partner_ids = []
        form = http.request.params
        if form:
            domain = "[('%s', 'ilike', '%s')]" % (form['search_on'],
                                                  form['search_value'])
            partner_obj = http.request.registry['res.partner']
            if form['search_on'] == 'name':
                # search on partner
                partner_ids = partner_obj.search(
                    cr, uid, eval(domain), context=context)
            else:
                model = '%s.coordinate' % form['search_on']
                coordinate_obj = http.request.registry[model]
                if form['search_on'] == 'email':
                    form['search_value'] = format_email(form['search_value'])
                if form['search_on'] == 'phone':
                    s_val = form['search_value']
                    domain = "[('phone_id.name', 'ilike', '%s')]" % (s_val)

                coordinate_ids = coordinate_obj.search(
                    cr, uid, eval(domain), context=context)
                for coordinate in coordinate_obj.browse(
                        cr, uid, coordinate_ids, context=context):
                    partner_ids.append(coordinate.partner_id.id)

            partners = partner_obj.browse(
                cr, uid, partner_ids, context=context)

        return http.request.render('ficep_mobile.mobile_index',
                                   {"partners": partners})
