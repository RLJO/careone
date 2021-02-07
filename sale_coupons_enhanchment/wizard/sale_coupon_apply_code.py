# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta, datetime


class SaleCouponApplyCode(models.TransientModel):
    _inherit = 'sale.coupon.apply.code'

    code_type = fields.Selection(string="Code Type", selection=[('promo', 'Promotion'), ('coupon', 'Coupon'), ],
                                 required=True, default='coupon')
    promo_code = fields.Char(string="Promo Code", required=False, )
    coupon_code = fields.Many2one('sale.coupon', string="Coupon Code", required=False)
    is_free_order_readonly_x = fields.Boolean(string="", )

    # hisham edition
    @api.onchange('coupon_code')
    def coupon_code_onchange(self):
        if self.coupon_code:
            today = datetime.today().date()
            today_x = datetime.today() + timedelta(hours=2)
            real_time = datetime.now() + timedelta(hours=2)
            current_time = real_time.time()
            sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
            if self.coupon_code.partner_id and (self.coupon_code.partner_id != sales_order.partner_id):
                raise ValidationError('%s/%s/%s' % (self.coupon_code.partner_id,sales_order.partner_id,self.coupon_code.partner_id and (self.coupon_code.partner_id != sales_order.partner_id)))
                raise ValidationError('The coupon is not applicable by this customer')
            elif self.coupon_code.vehicle_id and (self.coupon_code.vehicle_id != sales_order.vehicle_id):
                raise ValidationError('The coupon is not applicable on this vehicle')
            elif self.coupon_code.start_date_use > today_x.date() or self.coupon_code.end_date_use < today_x.date():
                raise ValidationError('Invalid date')
            elif self.coupon_code.start_hour_use > (current_time.hour + current_time.minute / 60) or self.coupon_code.end_hour_use < (current_time.hour + current_time.minute / 60):
                raise ValidationError('Invalid time')
            elif self.coupon_code.validity_duration != 0:
                if self.coupon_code.expiration_date < today:
                    raise ValidationError('Coupon expired')
            elif self.coupon_code.state != 'new':
                raise ValidationError('Coupon not valid')

            if self.coupon_code.is_free_order == True:
                self.is_free_order = True
                self.is_free_order_readonly_x = True

    is_free_order = fields.Boolean(string="Free Order", store=True)

    def process_coupon(self):
        """
        Apply the entered coupon code if valid, raise an UserError otherwise.

        """
        if self.code_type == 'coupon':
            coupon = self.env['sale.coupon'].browse(self.coupon_code.id)
            today = datetime.today() + timedelta(hours=2)
            real_time = datetime.now() + timedelta(hours=2)
            current_time = real_time.time()
            today_week_day = today.strftime("%A")
            is_applicable_programs_today=False
            for co in coupon:
                if today_week_day == 'Saturday' and co.is_str == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Sunday' and co.is_sun == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Monday' and co.is_mon == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Tuesday' and co.is_tus == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Wednesday' and co.is_wen == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Thursday' and co.is_thur == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Friday' and co.is_fri == True:
                    is_applicable_programs_today = True
                if is_applicable_programs_today == False:
                    raise ValidationError(_('Sorry There Is No Available Today.'))

        if self.code_type == 'promo':
            sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
            error_status = self.apply_promo(sales_order, self.promo_code)
            if error_status.get('error', False):
                raise UserError(error_status.get('error', False))
            if error_status.get('not_found', False):
                raise UserError(error_status.get('not_found', False))
            promotion = self.env['sale.coupon.program'].search([('promo_code','=',self.promo_code)])
            sales_order.promotion_program_id = promotion.id

        else:
            if self.is_free_order == True:
                sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
                my_domain_products = self.env['product.product'].search(
                    safe_eval(self.coupon_code.program_id.rule_products_domain))
                x = 0
                for rec in my_domain_products:
                    x = rec.id
                    break
                my_domain_product = self.env['product.product'].search([('id', '=', x)])
                my_free_product = self.coupon_code.program_id.reward_product_id
                if my_free_product:
                    order_obj_id = self.env['sale.order.line']
                    my_domain_product_line = {
                        'product_id': my_domain_product.id,
                        'order_id': sales_order.id,
                    }
                    my_free_product_line = {
                        'product_id': my_free_product.id,
                        'order_id': sales_order.id,
                    }
                    order_obj_id.create(my_domain_product_line)
                    order_obj_id.create(my_free_product_line)
                    base_records_ids = []
                    for rec in sales_order.order_line:
                        base_records_ids.append(rec.id)
                    error_status = self.apply_coupon(sales_order, self.coupon_code.code)
                    self.env['sale.order.line'].search([('id', '=', base_records_ids[0])]).unlink()
                    if error_status.get('error', False):
                        raise UserError(error_status.get('error', False))
                    if error_status.get('not_found', False):
                        raise UserError(error_status.get('not_found', False))

                    program = self.env['sale.coupon'].search([('id', '=', self.coupon_code.id)])
                    product = self.env['sale.coupon.program'].search([('id', '=', program.program_id.id)]).discount_line_product_id
                    for line in sales_order.order_line:
                        if line.product_id.id == product.id:
                            line.used_coupon = self.coupon_code.id
                else:
                    raise UserError("You Can't Use Free Order With This Program !")

            else:
                sales_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
                error_status = self.apply_coupon(sales_order, self.coupon_code.code)
                if error_status.get('error', False):
                    raise UserError(error_status.get('error', False))
                if error_status.get('not_found', False):
                    raise UserError(error_status.get('not_found', False))

    def apply_promo(self, order, coupon_code):
        if self.code_type == 'coupon':
            # coupon = self.env['sale.coupon'].browse(coupon_code)
            today = datetime.today() + timedelta(hours=2)
            real_time = datetime.now() + timedelta(hours=2)
            current_time = real_time.time()
            today_week_day = today.strftime("%A")
            is_applicable_programs_today=False
            for co in coupon_code:
                if today_week_day == 'Saturday' and co.is_str == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Sunday' and co.is_sun == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Monday' and co.is_mon == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Tuesday' and co.is_tus == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Wednesday' and co.is_wen == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Thursday' and co.is_thur == True:
                    is_applicable_programs_today = True
                elif today_week_day == 'Friday' and co.is_fri == True:
                    is_applicable_programs_today = True
                if is_applicable_programs_today == False:
                    raise ValidationError(_('Sorry There Is No Available Today.'))
        error_status = {}
        program = self.env['sale.coupon.program'].search([('promo_code', '=', coupon_code)])
        if program:
            error_status = program._check_promo_code(order, coupon_code)
            if not error_status:
                if program.promo_applicability == 'on_next_order':
                    # Avoid creating the coupon if it already exist
                    if program.discount_line_product_id.id not in order.generated_coupon_ids.filtered(
                            lambda coupon: coupon.state in ['new', 'reserved']).mapped('discount_line_product_id').ids:
                        order._create_reward_coupon(program)
                else:  # The program is applied on this order
                    order._create_reward_line(program)
                    order.code_promo_program_id = program
        else:
            error_status = {'not_found': _('The code %s is invalid') % (coupon_code)}
        return error_status
