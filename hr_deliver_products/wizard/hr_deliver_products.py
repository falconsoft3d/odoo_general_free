#-*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

TYPE = [
    ('retiro', 'Retiro'),
    ('translado', 'Transferencia')]


class WizardDeliverProducts(models.TransientModel):
    """Wizard deliver products."""

    _name = 'wizard.deliver.products'
    _description = "Wizard deliver products"

    def _get_default_ids(self):
        """."""
        employee_id = self._context.get('active_id', False)
        delivereds = self.env['deliver.products'].search(
            [('employee_id', '=', employee_id)])
        list_ids = [
            line.id for deliver in delivereds
            for line in deliver.product_ids if not line.retry]
        return [(6, 0, list_ids)]

    lines_ids = fields.Many2many(
        'product.line.list', 'many_location_rel',
        'many_id', 'product_line_id', 'Lineas', default=_get_default_ids)
    employee_id = fields.Many2one('hr.employee', 'Empleado')
    motive_id = fields.Many2one(
        'deliver.products.motive', 'Motivo')
    obs_text = fields.Text('Observación')
    type = fields.Selection(TYPE, string='Tipo', default='retiro')

    @api.onchange('type')
    def _onchange_type(self):
        """."""
        self.employee_id = False
        if self.type == 'retiro':
            self.employee_id = self._context.get('active_id', False)

    @api.onchange('motive_id')
    def _onchange_motive_id(self):
        """."""
        if self.motive_id:
            self.obs_text = self.motive_id.obs

    @api.multi
    def action_create_picking(self, product_ids, location_id, location_dest):
        """."""
        moves = []
        for line in product_ids:
            if not line.product_id.is_activo and line.product_id.type in ['consu', 'product']:
                moves.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                    'product_uom': line.product_id.uom_id.id,
                    'name': line.product_id.name,
                    'quantity_done': line.qty,
                }))

        if moves:

            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'outgoing'),
                 ('default_location_src_id', '=', location_id.id)])

            if not picking_type:
                raise UserError(
                    'No se a establecido un tipo de operación '
                    'para este proceso.')

            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'origin': self.employee_id.name,
                'move_lines': moves,
                'location_id': location_id.id,
                'location_dest_id': location_dest.id,
                'partner_id': self.employee_id.address_home_id.id,
                'company_id': self.env.user.company_id.id,
                'scheduled_date': fields.Date.today().strftime('%Y-%m-%d'),
                'note': self.obs_text
            })

            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()

            picking.button_validate()

    def create_deliver_product(self, type, product_ids):
        """."""
        prods = [(0, 0,
                  {'product_id': i.product_id.id, 'qty': i.qty,
                   'costo': i.costo, 'subtotal': i.subtotal})
                 for i in product_ids]
        self.env['deliver.products'].create({
            'employee_id': self.employee_id.id,
            'type': type,
            'product_ids': prods,
            'obs': self.obs_text,
            'state': 'done'
        })

    def retry_product(self):
        """."""
        products = [line.id for line in self.lines_ids if line.checked]

        if not products:
            raise UserError(
                'Se debe seleccionar algun producto de la lista.')

        product_brw = self.env['product.line.list'].browse(products)

        if self.type != 'retiro':

            if self.employee_id.id == self._context.get('active_id', False):
                raise UserError(
                    'No puedes transferir productos al mismo empleado.')

            self.create_deliver_product(self.type, product_brw)

        else:

            if not self.employee_id.address_home_id:
                raise UserError('El empleado no tiene asociado un cliente.')

            ubication_retry_id = self.env.user.company_id.ubication_retry_id
            if not ubication_retry_id:
                raise UserError('Se debe configurar ubicacion para retiros.')

            ubication_deliver_id = self.env.user.company_id.ubication_deliver_dest_id
            if not ubication_deliver_id:
                raise UserError(
                    'No existe una ubicacion virtual '
                    'de entregas para la bodega')

            self.action_create_picking(
                product_brw,
                ubication_deliver_id,
                ubication_retry_id)

            self.create_deliver_product(self.type, product_brw)

        product_brw.write({'retry': True})
        self.lines_ids.write({'checked': False})
