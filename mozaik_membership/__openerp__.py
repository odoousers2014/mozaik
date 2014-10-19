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
{
    'name': 'MOZAIK: Membership',
    'version': '1.0',
    "author": "ACSONE SA/NV",
    "maintainer": "ACSONE SA/NV",
    "website": "http://www.acsone.eu",
    'category': 'Political Association',
    'depends': [
        'mozaik_account',
        'mozaik_person_coordinate',
        'mozaik_structure',
    ],
    'description': """
MOZAIK Membership
=================
Add models
* Membership
* Membership History
* Membership Request
It defines a required m2o to Internal Instance on local zip.
It replicates this instance on partner which main address is related to this
local zip, default instance otherwise. This field is added to all views
(search, tree and form) of a partner.
""",
    'images': [
    ],
    'data': [
        'data/membership_state_data.xml',
        'data/abstract_coordinate_data.xml',
        'security/membership_security.xml',
        'security/ir.model.access.csv',
        'data/ir_config_parameter_data.xml',
        'data/product_data.xml',
        'data/ir_cron_membership.xml',
        'membership_workflow.xml',
        'product_view.xml',
        'membership_request_view.xml',
        'membership_view.xml',
        'address_local_zip_view.xml',
        'res_partner_view.xml',
        'wizard/change_main_address.xml',
        'wizard/force_int_instance.xml',
        'wizard/generate_reference.xml',
        'wizard/pass_former_member.xml',
        'report/waiting_member_report_view.xml',
    ],
    'qweb': [
    ],
    'demo': [
    ],
    'test': [
    ],
    'sequence': 150,
    'auto_install': False,
    'installable': True,
}