# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Company(models.Model):
    """Company."""

    _inherit = 'hr.employee'

    partner_id = fields.Many2one('res.partner', 'Cliente')
    deliveries_count = fields.Char(
        compute='_compute_deliveries_count', string='Total')
    deliver_count = fields.Char(
        compute='_compute_deliver_count', string='Entregas')
    retry_count = fields.Char(
        compute='_compute_retry_count', string='Retiros')

    def _compute_deliveries_count(self):
        """."""
        obj = self.env['deliver.products']
        for employee in self:
            products = []
            products_sum = []
            delivers = obj.search(
                [('employee_id', '=', employee.id), ('state', '=', 'done'),
                 ('type', 'in', ('entrega', 'translado'))])
            for deliver in delivers:
                for line in deliver.product_ids:
                    if not line.retry:
                        products.append(line)
                        products_sum.append(line.subtotal)
            employee.deliveries_count = '{} / {}'.format(
                len(products), sum(products_sum))

    def _compute_deliver_count(self):
        """."""
        obj = self.env['deliver.products']
        for employee in self:
            products = []
            products_sum = []
            delivers = obj.search(
                [('employee_id', '=', employee.id), ('state', '=', 'done'),
                 ('type', 'in', ('entrega', 'translado'))])
            for deliver in delivers:
                for line in deliver.product_ids:
                    products.append(line)
                    products_sum.append(line.subtotal)
            employee.deliver_count = '{} / {}'.format(
                len(products), sum(products_sum))

    def _compute_retry_count(self):
        """."""
        obj = self.env['deliver.products']
        for employee in self:
            products = []
            products_sum = []
            delivers = obj.search(
                [('employee_id', '=', employee.id), ('state', '=', 'done'),
                 ('type', 'in', ('retiro',))])

            for deliver in delivers:
                for line in deliver.product_ids:
                    products.append(line)
                    products_sum.append(line.subtotal)

            employee.retry_count = '{} / {}'.format(
                len(products), sum(products_sum))

    def get_deliveries(self, employee_id):
        """."""
        delivery_obj = self.env['deliver.products']
        return delivery_obj.search(
            [('employee_id', '=', employee_id)])

    def action_view_deliveries(self):
        """."""
        retries = self.env['deliver.products'].search(
            [('employee_id', '=', self.id), ('state', '=', 'done'),
             ('type', 'in', ('entrega', 'translado'))])

        lines = []
        for retry in retries:
            for line in retry.product_ids:
                if not line.retry:
                    lines.append(line.id)

        context = self.env.context.copy()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Productos Actuales',
            'res_model': 'product.line.list',
            'views': [[False, 'tree'], [False, 'form']],
            'domain': [('id', 'in', lines)],
            'context': context}
        """
        deliveries = self.get_deliveries(self.id)
        context = self.env.context.copy()
        context.update(
            {'search_default_employee_id': [self.id],
             'search_default_state': 'done'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Entrega Productos',
            'res_model': 'deliver.products',
            'views': [[False, 'tree'], [False, 'form']],
            'domain': [('id', 'in', deliveries.ids)],
            'context': context}
        """

    def action_view_deliver(self):
        """."""
        retries = self.env['deliver.products'].search(
            [('employee_id', '=', self.id), ('state', '=', 'done'),
             ('type', 'in', ('entrega', 'translado'))])

        lines = []
        for retry in retries:
            for line in retry.product_ids:
                lines.append(line.id)

        context = self.env.context.copy()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Costos de Retiros',
            'res_model': 'product.line.list',
            'views': [[False, 'tree'], [False, 'form']],
            'domain': [('id', 'in', lines)],
            'context': context}

    def action_view_retry(self):
        """."""
        retries = self.env['deliver.products'].search(
            [('employee_id', '=', self.id), ('state', '=', 'done'),
             ('type', 'in', ('retiro',))])

        lines = []
        for retry in retries:
            for line in retry.product_ids:
                lines.append(line.id)

        context = self.env.context.copy()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Costos de Entregas',
            'res_model': 'product.line.list',
            'views': [[False, 'tree'], [False, 'form']],
            'domain': [('id', 'in', lines)],
            'context': context}
