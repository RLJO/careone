# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PromotionProgramInherit(models.Model):
    _inherit = 'sale.coupon.program'

    rule_date_from = fields.Date(string="Start Date", help="Coupon program start date")
    rule_date_to = fields.Date(string="End Date", help="Coupon program end date")
    start_hour_use_promotion = fields.Float(string="From", required=False, )
    end_hour_use_promotion = fields.Float(string="To", required=False, )
    is_str_promotion = fields.Boolean(string="Saturday", )
    is_sun_promotion = fields.Boolean(string="Sunday", )
    is_mon_promotion = fields.Boolean(string="Monday", )
    is_tus_promotion = fields.Boolean(string="Tuesday", )
    is_wen_promotion = fields.Boolean(string="Wednesday", )
    is_thur_promotion = fields.Boolean(string="Thursday", )
    is_fri_promotion = fields.Boolean(string="Friday", )

    def _check_promo_code(self, order, coupon_code):
        message = {}
        applicable_programs = order._get_applicable_programs()
        today = datetime.today() + timedelta(hours=2)
        real_time = datetime.now() + timedelta(hours=2)
        current_time = real_time.time()
        today_week_day = today.strftime("%A")
        is_applicable_programs_today = False
        if today_week_day == 'Saturday' and applicable_programs.is_str_promotion == True:
            is_applicable_programs_today = True
        elif today_week_day == 'Sunday' and applicable_programs.is_sun_promotion == True:
            is_applicable_programs_today = True
        elif today_week_day == 'Monday' and applicable_programs.is_mon_promotion == True:
            is_applicable_programs_today = True
        elif today_week_day == 'Tuesday' and applicable_programs.is_tus_promotion == True:
            is_applicable_programs_today = True
        elif today_week_day == 'Wednesday' and applicable_programs.is_wen_promotion == True:
            is_applicable_programs_today = True
        elif today_week_day == 'Thursday' and applicable_programs.is_thur_promotion == True:
            is_applicable_programs_today = True
        elif today_week_day == 'Friday' and applicable_programs.is_fri_promotion == True:
            is_applicable_programs_today = True
        if applicable_programs.end_hour_use_promotion < (
                current_time.hour + current_time.minute / 60) or applicable_programs.start_hour_use_promotion > (
                current_time.hour + current_time.minute / 60) or applicable_programs.rule_date_from > today.date() or applicable_programs.rule_date_to < today.date() or is_applicable_programs_today != True:
            message = {'error': _("The Promo Code isn't Available Now !")}
        elif self.maximum_use_number != 0 and self.order_count >= self.maximum_use_number:
            message = {'error': _('Promo code %s has been expired.') % (coupon_code)}
        elif not self._filter_on_mimimum_amount(order):
            message = {'error': _('A minimum of %s %s should be purchased to get the reward') % (
                self.rule_minimum_amount, self.currency_id.name)}
        elif self.promo_code and self.promo_code == order.promo_code:
            message = {'error': _('The promo code is already applied on this order')}
        elif not self.promo_code and self in order.no_code_promo_program_ids:
            message = {'error': _('The promotional offer is already applied on this order')}
        elif not self.active:
            message = {'error': _('Promo code is invalid')}
        elif self.rule_date_from and self.rule_date_from > order.date_order or self.rule_date_to and order.date_order > self.rule_date_to:
            message = {'error': _('Promo code is expired')}
        elif order.promo_code and self.promo_code_usage == 'code_needed':
            message = {'error': _('Promotionals codes are not cumulative.')}
        elif self._is_global_discount_program() and order._is_global_discount_already_applied():
            message = {'error': _('Global discounts are not cumulative.')}
        elif self.promo_applicability == 'on_current_order' and self.reward_type == 'product' and not order._is_reward_in_order_lines(
                self):
            message = {'error': _('The reward products should be in the sales order lines to apply the discount.')}
        elif not self._is_valid_partner(order.partner_id):
            message = {'error': _("The customer doesn't have access to this reward.")}
        elif not self._filter_programs_on_products(order):
            message = {'error': _(
                "You don't have the required product quantities on your sales order. If the reward is same product quantity, please make sure that all the products are recorded on the sales order (Example: You need to have 3 T-shirts on your sales order if the promotion is 'Buy 2, Get 1 Free'.")}
        else:
            if self not in applicable_programs and self.promo_applicability == 'on_current_order':
                message = {'error': _('At least one of the required conditions is not met to get the reward!')}
        return message

    @api.model
    def _filter_on_validity_dates(self, order):
        return self.filtered(lambda program:
                             program.rule_date_from and program.rule_date_to and
                             program.rule_date_from <= order.date_order.date() and program.rule_date_to >= order.date_order.date() or
                             not program.rule_date_from or not program.rule_date_to)


class SalesOrderInherit(models.Model):
    _inherit = 'sale.order'

    def _create_reward_coupon(self, program):
        # if there is already a coupon that was set as expired, reactivate that one instead of creating a new one
        coupon = self.env['sale.coupon'].search([
            ('program_id', '=', program.id),
            ('state', '=', 'expired'),
            ('partner_id', '=', self.partner_id.id),
            ('order_id', '=', self.id),
            ('discount_line_product_id', '=', program.discount_line_product_id.id),
        ], limit=1)
        if coupon:
            coupon.write({'state': 'reserved'})
        else:
            coupon = self.env['sale.coupon'].create({
                'program_id': program.id,
                'state': 'reserved',
                'partner_id': self.partner_id.id,
                'start_hour_use': program.start_hour_use_promotion,
                'end_hour_use': program.end_hour_use_promotion,
                'start_date_use': program.rule_date_from,
                'end_date_use': program.rule_date_to,
                'discount_line_product_id': program.discount_line_product_id.id,
                'order_id': self.id,

            })
        self.generated_coupon_ids |= coupon
        return coupon