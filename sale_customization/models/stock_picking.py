from odoo import fields, models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    scheduled_date = fields.Datetime(
        'Scheduled Date', compute='_compute_scheduled_date', store=True,
        index=True, default=fields.Datetime.now, tracking=True, readonly=False,
        help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")

    date_done = fields.Datetime('Date of Transfer', copy=False, readonly=False,
                                help="Date at which the transfer has been processed or cancelled.")

    def _set_scheduled_date(self):
        for picking in self:
            # if picking.state in ('done', 'cancel'):
            #     raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))
            picking.move_lines.write({'date_expected': picking.scheduled_date})
