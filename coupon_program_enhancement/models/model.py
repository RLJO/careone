# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError

class SaleCoupon(models.Model):

    _inherit = 'sale.coupon'

    validity_duration = fields.Integer(string="Validity Duration", compute = '_compute_validity_duration', store = True)

    @api.model
    def create(self, vals):
        self.ensure_one()
        rec = super(SaleCoupon, self).create(vals)
        self.validity_duration = self.program_id.validity_duration
        return rec

    # @api.model
    # def _compute_validity_duration(self):
    #     for this in self:
    #         raise ValidationError('The coupon is not applicable by this customer')
    #         # if this.validity_duration == 0:
    #         this.validity_duration = this.program_id.validity_duration