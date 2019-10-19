# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    """Product Template."""

    _inherit = 'product.template'

    is_activo = fields.Boolean('Activo Fijo')

    expiration_days = fields.Integer('Días de Vencimientos')
