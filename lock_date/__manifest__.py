{
    "name": "Lock Date",
    "version": "18.0",
    'author': 'Khalid',
    "depends": ["hr",'hr_work_entry_contract_enterprise','hr_payroll','food_allowance','sync_employee_advance_salary',
                'payroll_overtime_inputs','emp_fine_deduction','monal_leave_encashment','emp_att_deduction'],
    'website': 'https://www.globalxs.co',
    "data": [
        "security/ir.model.access.csv",
        "views/lock_date_views.xml",

    ],
    "installable": True,
    "application": True,
}
