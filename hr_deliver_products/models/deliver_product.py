# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import timedelta
from datetime import date

STATE = [
    ('draft', 'Borrador'),
    ('solicitud', 'Solicitado'),
    ('aprobado', 'Aprobado'),
    ('done', 'Finalizado'),
    ('cancel', 'Cancelado')]

TYPE = [
    ('entrega', 'Entrega'),
    ('retiro', 'Retiro'),
    ('translado', 'Transferencia')]

RO_STATES = {'done': [('readonly', True)], 'aprobado': [('readonly', True)]}


class DeliverProductsMotive(models.Model):
    """Deliver Products Motive."""

    _name = 'deliver.products.motive'
    _description = 'Deliver Products Motive'

    name = fields.Char('Motivo', copy=False)
    obs = fields.Text('Descripción')


class DeliverProducts(models.Model):
    """Deliver Products."""

    _name = 'deliver.products'
    _description = 'Deliver Products'
    _inherit = "mail.thread"
    _order = 'id desc'

    name = fields.Char(
        'Deliver Products', states={'draft': [('readonly', False)]},
        required=True, copy=False, readonly=True, index=True,
        default=lambda self: 'Nuevo')

    entry_date = fields.Date('Fecha', default=fields.Date.today, states=RO_STATES)

    user_id = fields.Many2one(
        'res.users', string='Usuario', track_visibility='always', states=RO_STATES,
        default=lambda self: self.env.user)

    employee_id = fields.Many2one(
        'hr.employee', string='Empleado', track_visibility='always', states=RO_STATES)

    picking_id = fields.Many2one(
        'stock.picking', string='Transferencia')

    obs = fields.Text('Observaciones')

    state = fields.Selection(
        STATE, string='Estado', index=True, readonly=True,
        track_visibility='always', default='draft', copy=False)

    product_ids = fields.One2many(
        'product.line.list', 'product_deliver_id', string='Listado Productos', states=RO_STATES)

    type = fields.Selection(
        TYPE, string='Tipo', index=True, default='entrega', copy=False, states=RO_STATES)

    @api.multi
    def action_send_email(self):
        """."""
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                'hr_deliver_products', 'email_template_deliver_products2')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'deliver.products',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_create_picking(self, deliver_id, location_id, location_dest):
        """."""
        moves = []

        for line in deliver_id.product_ids:

            if not line.product_id.is_activo and line.product_id.type in [
                    'consu', 'product']:
                moves.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                    'product_uom': line.product_id.uom_id.id,
                    'name': line.product_id.name,
                    'quantity_done': line.qty,
                }))

        if moves:

            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'internal'),
                 ('default_location_src_id', '=', location_id.id)])

            if not picking_type:
                raise UserError(
                    'No se a establecido un tipo de operación '
                    'para este proceso.')

            values = {
                'picking_type_id': picking_type.id,
                'origin': deliver_id.name,
                'move_lines': moves,
                'location_id': location_id.id or picking_type.location_id.id,
                'location_dest_id': location_dest.id or picking_type.location_dest_id.id,
                'partner_id': deliver_id.employee_id.address_home_id.id,
                'company_id': self.env.user.company_id.id,
                'scheduled_date': deliver_id.entry_date.strftime('%Y-%m-%d')
            }

            picking = self.env['stock.picking'].create(values)

            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()

            picking.button_validate()
            self.picking_id = picking.id

    @api.multi
    def exe_cancel(self):
        """."""
        self.state = 'cancel'

    @api.multi
    def exe_solicitado(self):
        """."""
        self.state = 'solicitud'

    @api.multi
    def exe_aprobar(self):
        """."""
        if not self.product_ids:
            raise UserError('Se deben agregar productos.')
        self.state = 'aprobado'

    @api.multi
    def exe_deliver(self):
        """."""
        if not self.product_ids:
            raise UserError('Se deben agregar productos.')

        partner_id = self.employee_id.address_home_id
        if not partner_id:
            raise UserError('El empleado no tiene asociado un cliente.')

        if self.type == 'entrega':

            ubication_deliver_id = self.env.user.company_id.ubication_deliver_id
            ubication_deliver_dest_id = self.env.user.company_id.ubication_deliver_dest_id

            if not ubication_deliver_id or not ubication_deliver_dest_id:
                raise UserError('Se debe configurar ubicacion para entregas.')

            self.action_create_picking(
                self.browse(self.id), ubication_deliver_id,
                ubication_deliver_dest_id)

        if self.type == 'retiro':
            ubication_retry_id = self.env.user.company_id.ubication_retry_id
            if not ubication_retry_id:
                raise UserError('Se debe configurar ubicacion para retiros.')

        self.state = 'done'

    @api.multi
    def exe_return_draft(self):
        """."""
        self.state = 'draft'

    @api.model
    def create(self, vals):
        """."""
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'deliver.products') or 'Nuevo'
        return super().create(vals)


class ProductLineList(models.Model):
    """Lista de Productos."""

    _name = 'product.line.list'
    _description = "Lista de Productos"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='Producto')
    qty = fields.Float('Cantidad')
    costo = fields.Float('Costo')
    subtotal = fields.Float('Subtotal')
    product_deliver_id = fields.Many2one(
        'deliver.products', string="Entrega",
        ondelete='cascade')
    checked = fields.Boolean('Seleccionar')
    retry = fields.Boolean('Retirado/Transferido')

    expiration_date = fields.Date('Fecha Vencimiento', compute='_compute_giveme_expired')

    expiration_days = fields.Integer('Días de Vencimientos', related='product_id.expiration_days')

    expired = fields.Boolean('Vencido', compute='_compute_giveme_expired')

    note = fields.Char('Notas')

    @api.one
    def _compute_giveme_expired(self):
        if self.expiration_days != 0:
            if self.type == 'retiro':
                self.expired = False
            else:
                self.expiration_date = fields.Date.from_string(self.date) + timedelta(days=self.expiration_days)
                today = date.today()
                if today > self.expiration_date:
                    self.expired = True
                else:
                    self.expired = False


    employee_id = fields.Many2one(
        'hr.employee', related='product_deliver_id.employee_id', store=True,
        readonly=True)

    partner_id = fields.Many2one(
        'res.partner', related='product_deliver_id.employee_id.address_home_id',
        store=True, readonly=True)

    date = fields.Date(
        related='product_deliver_id.entry_date', store=True, readonly=True)

    type = fields.Selection(
        TYPE, related='product_deliver_id.type',
        store=True, readonly=True)

    user_id = fields.Many2one(
        'res.users', related='product_deliver_id.user_id',
        store=True, readonly=True)

    stock_product = fields.Float(
        related='product_id.qty_available', readonly=True)

    categ_id = fields.Many2one(
        'product.category', related='product_id.product_tmpl_id.categ_id',
        store=True, readonly=True)

    @api.onchange('product_id')
    def onchange_product_id(self):
        """."""
        self.costo = self.product_id.standard_price

    @api.onchange('qty', 'costo')
    def onchange_product_cost_id(self):
        """."""
        self.subtotal = self.qty * self.costo
