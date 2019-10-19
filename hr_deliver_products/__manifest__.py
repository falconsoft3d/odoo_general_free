# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2019 Marlon Falcón Hernandez
#    (<http://www.ynext.cl>).
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
    'name': 'HR Deliver Products - MFH',
    'version': '12.0.1.0.0',
    'author': 'Ynext SpA',
    'maintainer': 'Ynext SpA',
    'website': 'http://www.ynext.cl',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'summary': 'Entrega de Productos a Empleados.',
    'depends': ['hr_payroll', 'stock'],
    'data': [
        'security/deliver_products_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'views/deliver_products_view.xml',
        'views/res_company_view.xml',
        'wizard/hr_deliver_products_view.xml',
        'views/hr_employee_view.xml',
        'views/product_template_view.xml',
        'views/deliver_products_motive_view.xml',
        'views/picking_view.xml',
        'report/report.xml',
        'report/report_templates.xml',
        'data/template_email.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False
}
