from odoo import models, fields, api
from dateutil import relativedelta
from datetime import datetime
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    sponsor_name = fields.Char(string="Sponsor")
    sponsor_type = fields.Selection([
        ('company', 'Company'),
        ('individual', 'Individual')
    ], string='Sponsor Type')
    employee_type = fields.Selection([
        ('in_source', 'In Source'),
        ('out_source', 'Out Source'),
        ('part_time', 'Part Time')
    ], string='Employee Type')
    residency_number = fields.Char(string="Residency Number")
    passport_expiry_date = fields.Date(string="Passport Expire Date")
    insurance_type = fields.Selection([
        ('saudi', 'Saudi'),
        ('other', 'Other'),
    ], string='Social Insurance Type')

    def visa_passport_expiry_reminder(self):
        today_date = fields.Date.today()
        passport_expiration_template = self.env.ref('employee_changes.email_template_passport_expire')
        visa_expiration_template = self.env.ref('employee_changes.email_template_visa_expire')
        employee_rec = self.env['hr.employee'].search([])
        for employee in employee_rec:
            if employee.passport_expiry_date and employee.passport_id:
                passport_date_difference = relativedelta.relativedelta(employee.passport_expiry_date, today_date)
                if passport_date_difference.months == 1:
                    email_values = {
                        'email_to': '%s, %s, %s' % (employee.work_email, employee.coach_id.work_email or False,
                                                    employee.parent_id.work_email or False),
                    }
                    passport_expiration_template.send_mail(employee.id, force_send=True, email_values=email_values)
            if employee.visa_expire and employee.visa_no:
                visa_date_difference = relativedelta.relativedelta(employee.visa_expire, today_date)
                if visa_date_difference.months == 1:
                    email_values = {
                        'email_to': '%s, %s, %s' % (employee.work_email, employee.coach_id.work_email or False,
                                                    employee.parent_id.work_email or False),
                    }
                    visa_expiration_template.send_mail(employee.id, force_send=True, email_values=email_values)

    # end of service section
    # employee_type2 = fields.Selection([('worker', 'Worker'), ('employee', 'Employee')], string='End of Service For')
    employee_worth = fields.Selection(selection=[('from_employer', 'Termination from employer'),
                                                 ('less_than_2_years', "Employee resigns less than 2 years"),
                                                 ('from_2_to_5', 'Employee resigns from 2 years to 5 years'),
                                                 ('from_5_to_10', 'Employee resigns from 5 to 10 years'),
                                                 ('after_10', 'Employee resigns after 10 years')],
                                      string='Employee Worth')
    calculate_balance = fields.Boolean('Calculate?')
    end_service_date = fields.Date('Date')
    balance = fields.Float('Balance', compute="_get_end_service_balance")
    add_to_payslip = fields.Boolean('Add to Payslip')
    rewarded_result = fields.Float(string='Rewarded', readonly=True)

    # @api.onchange('contract_id.bank_accounts')
    # def _compute_bank_accounts(self):
    #     for this in self:
    #         this.bank_accounts = this.contract_id.bank_accounts
    #         for line in this.bank_accounts:
    #             line.emp_id = this.id
    # if this.contract_id.bank_accounts:
    #     this.bank_accounts =[(5,0,0)]
    #     for line in this.contract_id.bank_accounts:
    #         this.bank_accounts = [(0,0,{'emp_id':this.id,
    #                             'name':line.name,
    #                             'bank_account_number':line.bank_account_number})]
    # else:
    #     this.bank_accounts =[(5,0,0)]

    bank_accounts = fields.One2many('bank.account', 'emp_id')
    # bank_accounts = fields.One2many('bank.account','emp_id',compute = _compute_bank_accounts)
    iban = fields.Char('IBAN')

    # iban = fields.Char('IBAN',related="contract_id.iban")

    @api.depends('calculate_balance', 'end_service_date')
    def _get_end_service_balance(self):
        self.balance = 0.0
        if self.calculate_balance:
            if not self.end_service_date:
                return True
            contract = self.env['hr.contract'].search([('employee_id', '=', self.id),
                                                       ('state', '=', 'open')], limit=1)
            if contract and contract.date_start:
                start = datetime.strptime(str(contract.date_start), '%Y-%m-%d')
                end = datetime.strptime(str(self.end_service_date), '%Y-%m-%d')
                r = relativedelta.relativedelta(end, start)
                years = int(r.years)
                months = r.months + (12 * r.years)

                end_of_service_calculation = contract.wage + contract.housing_allowance + contract.transportation_allowance

                if 6 > years >= 1:
                    self.balance = end_of_service_calculation * 0.5 * months
                elif years > 5:
                    self.balance = end_of_service_calculation * months

            if self.add_to_payslip:
                if self.employee_worth == 'from_employer':
                    self.rewarded_result = self.balance
                elif self.employee_worth == 'less_than_2_years':
                    self.rewarded_result = 0.0
                elif self.employee_worth == 'from_2_to_5':
                    self.rewarded_result = self.balance / 3
                elif self.employee_worth == 'from_5_to_10':
                    self.rewarded_result = self.balance * 2 / 3
                else:
                    self.rewarded_result = self.balance


class BankAccount(models.Model):
    _inherit = 'bank.account'

    emp_id = fields.Many2one('hr.employee')
