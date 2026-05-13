# -*- coding: utf-8 -*-
{
    'name'      :   "ZKTeco Biometric Attendance Integration",
    'author'    :   "Jarvis",
    "website"   :   "https://softatt.com/",
    'category'  :   'Uncategorized',
    "price":    "779.99",
    "currency"  :   "USD",
    "license"   :   "OPL-1",
    'version'   :   '0.1',
    'depends'   :   ['base','mail','softatt_attendance'],
    
    "summary": """ 
    ZKTeco, ZKTeco Odoo, Odoo biometric, biometric attendance, ZKTeco biometric, Odoo fingerprint,
    Odoo face recognition, Odoo attendance, Odoo HR attendance, ZKTeco attendance, Odoo time tracking,
    ZKTeco integration, Odoo ZKTeco integration, Odoo time attendance, fingerprint attendance Odoo,
    face recognition attendance Odoo, Odoo HR biometric, payroll biometric Odoo, Odoo ZKTeco module,
    Odoo ZKTeco device, Odoo HRMS biometric, best Odoo biometric, Odoo ZKTeco without middleware,
    Odoo attendance no middleware, ZKTeco direct Odoo connection, Odoo ZKTeco integration price,
    buy ZKTeco Odoo module, ZKTeco Odoo support, Odoo attendance tracking, best biometric module Odoo,
    Odoo workforce tracking, Odoo ZKTeco SpeedFace, Odoo ZKTeco iFace, Odoo fingerprint device, 
    Odoo compatible biometric, Odoo biometric integration, Odoo biometric system, Odoo ZKTeco without static IP, 
    Odoo attendance system, ZKTeco face recognition Odoo, ZKTeco alternative Odoo, Odoo time attendance device, 
    Odoo employee tracking biometric, Odoo staff attendance biometric, Odoo time clock biometric, Odoo ZKTeco plugin, 
    Odoo biometric login, ZKTeco ERP integration, ZKTeco middleware-free Odoo, Odoo attendance without local PC, 
    Odoo time management biometric, biometric scanner Odoo, Odoo door access control biometric, 
    Odoo fingerprint scanner, Odoo attendance automation, ZKTeco ERP system, ZKTeco Odoo payroll, 
    ZKTeco Odoo HR, Odoo best attendance module, Odoo best biometric solution, 
    ZKTeco attendance tracking Odoo, ZKTeco Odoo software, best ZKTeco Odoo app, 
    Odoo biometric punch-in, Odoo shift attendance biometric, Zkteco API,
    ZKTeco terminal, Odoo biometric terminal, Odoo attendance terminal, ZKTeco machine,
    Odoo fingerprint machine, Odoo face recognition terminal, Odoo attendance machine, biometric terminal Odoo,
    ZKTeco time attendance terminal, Odoo time clock terminal, ZKTeco fingerprint terminal, 
    Odoo punch clock machine, Odoo staff attendance terminal, Odoo workforce terminal, 
    ZKTeco punch-in machine, Odoo shift attendance terminal, ZKTeco access control terminal,
    Odoo employee clock-in machine, ZKTeco face scan terminal, Odoo door access terminal,
    Odoo biometric device terminal, Odoo ZKTeco hardware integration, Odoo HR terminal, Odoo security terminal,
    best ZKTeco terminal for Odoo, ZKTeco terminal integration Odoo,
    ZKTeco BioTime, Odoo BioTime, BioTime Odoo integration, BioTime attendance Odoo, BioTime biometric Odoo,
    Odoo BioTime terminal, BioTime fingerprint Odoo, BioTime face recognition Odoo, Odoo BioTime machine, 
    ZKTeco BioTime software, Odoo BioTime attendance tracking, BioTime HR Odoo, BioTime payroll Odoo, 
    BioTime workforce management Odoo, Odoo BioTime device, Odoo BioTime system, BioTime time tracking Odoo,
    Odoo BioTime punch-in, Odoo BioTime time clock, ZKTeco BioTime ERP integration, 
    BioTime middleware-free Odoo, Odoo BioTime staff attendance, BioTime access control Odoo, 
    Odoo BioTime shift management, best BioTime module for Odoo, Odoo BioTime plugin, 
    Odoo BioTime automation, Odoo biometric punch-in BioTime, ZKTeco BioTime attendance machine, BioTime terminal Odoo, 
    SOFT TECH, SOFTTECH, SOFTATT, SOFTATTENDANCE ZKTECO, SOFTATTENDANCE ZKTECO EXTENSION,

    """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        
        'views/conf.xml',
        'views/res_users.xml',
        'views/att_log.xml',
        
        'views/device_user.xml',
        
        
        'wizards/download_att.xml',
        'wizards/sync_device_users.xml',
        'wizards/enroll_user_biodata.xml',
        'views/device.xml',

        'views/menu_items.xml',
        'data/cron.xml',
    ],
    
    'images': ['static/description/Banner.gif'],
    
    
}
