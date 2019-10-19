# -*- coding: utf-8 -*-

from odoo import fields, models


class Picking(models.Model):
    """Company."""

    _inherit = 'stock.picking'

    motive_id = fields.Many2one(
        'deliver.products.motive', string='Motivo', readonly=True)
