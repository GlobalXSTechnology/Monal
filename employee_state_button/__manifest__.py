{
    'name': "Employee State Button",
    'author': "ali",
    'version': '18.0',
    # 'depends': ['hr','hr_umrah_eligibility','studio_customization','hr_hourly_cost'],
    'depends': ['hr','hr_contract','hr_holidays','hr_hourly_cost','hr_umrah_eligibility','monal_weekly_off'],
    'data': [
        'views/employee_button.xml',
    ],
    "installable": True,
    "application": False,
}
