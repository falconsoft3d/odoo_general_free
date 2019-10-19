# -*- coding: utf-8 -*-

from odoo import fields, models


class Company(models.Model):
    """Company."""

    _inherit = 'res.company'

    ubication_deliver_id = fields.Many2one(
        'stock.location', "Ubicación")

    ubication_deliver_dest_id = fields.Many2one(
        'stock.location', "Ubicación de entrega")

    ubication_retry_id = fields.Many2one(
        'stock.location', "Ubicación Retiro")
