# -*- coding: utf-8 -*-
# Part of Odoo, Aktiv Software PVT. LTD.
# See LICENSE file for full copyright & licensing details.

from odoo import models, fields, api


class CleanData(models.TransientModel):
    _name = "clean.data"
    _description = "Clean Data"

    so_do = fields.Boolean("Sales & All Transfers")
    po = fields.Boolean("Purchase & All Transfers")
    all_trans = fields.Boolean("Only Transfers")
    inv_pymt = fields.Boolean("All Invoicing, Payments & Journal Entries")
    journals = fields.Boolean("Only Journal Entries")
    cus_ven = fields.Boolean("Customers & Vendors")
    coa = fields.Boolean("Chart Of Accounts & All Accounting Data")
    pos = fields.Boolean("Point Of Sale")
    project = fields.Boolean("Projects, Tasks & Timesheets")
    all_data = fields.Boolean("All Data")
    mrp = fields.Boolean("Manufacturing Orders")
    crm_pipeline = fields.Boolean("All Pipelines")
    crm_lead_mining_requests = fields.Boolean("Lead Mining Requests")
    crm_lost_reason = fields.Boolean("Lost Reasons")
    project_task = fields.Boolean("Only Task & Timesheets")
    timesheet = fields.Boolean("Only Timesheets")
    bom_mrp = fields.Boolean("BOM & Manufacturing Orders")
    workcentre_mrp = fields.Boolean("Work Order Center")
    sales_teams = fields.Boolean("Sales Teams")
    quotation_templates = fields.Boolean("Quotation Templates")
    activity_types = fields.Boolean("Activity Types")
    pricelists = fields.Boolean("Pricelists")
    expenses = fields.Boolean("My Expenses")
    package_types = fields.Boolean("Package Types")
    locations = fields.Boolean("Locations")
    rules = fields.Boolean("Rules")
    warehouses = fields.Boolean("Warehouses")
    vendor_pricelist = fields.Boolean("Vendor Pricelists")
    blanket_order = fields.Boolean("Blanket Orders")
    pos_order = fields.Boolean("POS Orders")
    pos_bill = fields.Boolean("POS Bills/Coins")
    pos_product_category = fields.Boolean("POS Product Category")
    quality_alert = fields.Boolean("Quality Alerts")
    quality_check = fields.Boolean("Quality Checks")
    quality_point = fields.Boolean("Quality Control Points")
    maintenance_request = fields.Boolean("Maintenance Requests")
    maintenance_equipment = fields.Boolean("Maintenance Equipments")
    maintenance_equipment_category = fields.Boolean(
        "Maintenance Equipment " "Categories"
    )
    helpdesk_ticket = fields.Boolean("Helpdesk Tickets")
    product_product = fields.Boolean("Product Variants")
    product_category = fields.Boolean("Product Categories")
    account_payment_term = fields.Boolean("Account Payment Term")
    account_tax_group = fields.Boolean("Tax Groups")
    gamification_badge = fields.Boolean("Badges")
    hr_contract = fields.Boolean("Contracts and Details")
    field_service_task = fields.Boolean("All tasks and details")
    by_resources = fields.Boolean("By Resources")
    by_roles = fields.Boolean("By Roles")
    by_projects = fields.Boolean("By Projects")
    company_id = fields.Many2one("res.company", "Company")

    def clear_mail_activity_records(self, model, table_name):
        # Check if the table exists
        self._cr.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table_name,))
        table_exists = self._cr.fetchone()[0]
        if table_exists:
            # Delete the table deleted records activity records
            query = f"""
                DELETE FROM mail_activity
                WHERE res_model = %s
                AND res_id NOT IN (SELECT id FROM {table_name})
            """
            self._cr.execute(query, (model,))

    def clear_mail_message_records(self, model, table_name):
        self._cr.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table_name,))
        table_exists = self._cr.fetchone()[0]
        if table_exists:
            # Delete the table deleted records message records
            query = f"""
                DELETE FROM mail_message
                WHERE model = %s
                AND res_id NOT IN (SELECT id FROM {table_name})
            """
            self._cr.execute(query, (model,))

    def check_and_delete(self, table):
        """
        Check if a table exists in the database schema
        and delete its records if it does.

        Args:
            table (str): The name of the table to be checked and deleted.

        Returns:
            None
        """
        table_name = table
        model = table_name.replace("_", ".")

        # Check if the table exists
        sql = (
                """SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = '%s');"""
                % table
        )
        self._cr.execute(sql)
        res = self._cr.dictfetchall()
        res = res and res[0] or {}
        if not res.get("exists"):
            return

        # Determine the SQL query for deletion based on table and company_id
        if self.company_id:
            if table in ["account_payment", "account_bank_statement_line"]:
                sql = """
                    DELETE FROM %s
                    WHERE move_id IN (
                    SELECT id FROM account_move
                    WHERE company_id = %s
                )
                """ % (
                    table,
                    self.company_id.id,
                )

            elif table in [
                "project_tags",
                "account_payment",
                "account_bank_statement_line",
                "project_update",
                "project_milestone",
                "project_project_stage",
                "mrp_workorder",
                "mrp_bom_line",
                "mrp_bom",
                "crm_iap_lead_mining_request",
                "crm_lost_reason",
                "mail_activity_type",
                "mrp_routing_workcenter",
                "pos_bill",
                "pos_category",
                "product_product",
                "product_category",
                "product_template",
                "account_tax_group",
                "gamification_badge",
                "hr_plan_activity_type",
                "mail_activity",
                "account_fiscal_position_tax",
                "account_reconcile_model",
                "account_reconcile_model_line",
                "account_tax",
                "account_partial_reconcile",
                "account_move",
                "account_move_line",
                "sale_order_line",
                "mrp_production",
                "stock_lot",
                "mrp_bom",
                "stock_quant",
                "stock_move",
                "pos_session",
                "pos_config",
                "sale_order_template_option",
                "project_collaborator",
                "project_sale_line_employee_map",
                "sale_order_template_line",
                "stock_valuation_layer",
                "purchase_order_line",
                "sale_order",
                "account_transfer_model_line",
                "account_transfer_model",
                "account_account",
                "account_journal",
            ]:
                sql = """delete from %s ;""" % table
                self.clear_mail_activity_records(model, table_name)
                self.clear_mail_message_records(model, table_name)
            else:
                sql = """DELETE FROM %s WHERE company_id = %s;""" % (
                    table,
                    self.company_id.id,
                )
                self.clear_mail_activity_records(model, table_name)
                self.clear_mail_message_records(model, table_name)

        else:
            sql = """delete from %s ;""" % table
        self._cr.execute(sql)
        self.clear_mail_activity_records(model, table_name)
        self.clear_mail_message_records(model, table_name)

    def _clear_so_order(self):
        """
        Clears sales order related data from the database.

        Deletes records from 'planning_slot'
        if 'sale_project_forecast' is installed.
        Then, iterates through and clears several
        sales-related tables using `check_and_delete`.
        """
        sale_project_forecast = self.env["ir.module.module"].search(
            [("name", "=", "sale_project_forecast")]
        )
        if sale_project_forecast.state == "installed":
            sql = (
                """delete from planning_slot where sale_line_id is not null;"""
            )
            self._cr.execute(sql)
        sale_order = [
            "stock_quant",
            "stock_move_line",
            "stock_move",
            "stock_picking",
            "account_partial_reconcile",
            "account_payment_register",
            "account_move_line",
            "account_move",
            "sale_order_line",
            "sale_order",
        ]
        for so in sale_order:
            self.check_and_delete(so)
        table_name = 'sale_order'
        self.clear_mail_activity_records('sale.order', table_name)
        self.clear_mail_message_records('sale.order', table_name)

    def _clear_po(self):
        """
        Clears purchase order related data from the database.

        Iterates through and clears several purchase-related
        tables using `check_and_delete method`.
        """
        purchase_order = [
            "stock_quant",
            "stock_move_line",
            "stock_move",
            "stock_picking",
            "account_partial_reconcile",
            "account_payment_register",
            "account_move_line",
            "account_move",
            "purchase_order",
            "purchase_order_line",
        ]
        for po in purchase_order:
            self.check_and_delete(po)
        table_name = 'purchase_order'
        self.clear_mail_activity_records('purchase.order', table_name)
        self.clear_mail_message_records('purchase.order', table_name)

    def _clear_transfer(self):
        """
        Clears picking order related data from the database.

        Iterates through and clears several picking-related
        tables using `check_and_delete method`.
        """
        picking_order = [
            "stock_picking",
            "stock_move_line",
            "stock_move",
            "stock_quant",
        ]
        for picking in picking_order:
            self.check_and_delete(picking)

    def _clear_sales_teams(self):
        """
        Clears crm team data from the database.
        """
        crm_team = "crm_team"
        self.check_and_delete(crm_team)

    def _clear_planning_by_resources(self):
        """
        Clears planning related to resources from the database.
        Deletes records from 'planning_slot' where 'resource_id'
        is not null if the 'planning' module is installed.
        """
        planning = self.env["ir.module.module"].search(
            [("name", "=", "planning")]
        )
        if planning.state == "installed":
            sql = (
                """delete from planning_slot where resource_id is not null;"""
            )
            self._cr.execute(sql)

    def _clear_planning_by_roles(self):
        """
        Clears planning related to roles from the database.
        Deletes records from 'planning_slot' where
        'role_id' is not null if the 'planning' module is installed.
        """
        planning = self.env["ir.module.module"].search(
            [("name", "=", "planning")]
        )
        if planning.state == "installed":
            sql = """delete from planning_slot where role_id is not null;"""
            self._cr.execute(sql)

    def _clear_planning_by_projects(self):
        """
        Clears planning related to projects from the database.
        Deletes records from 'planning_slot' where 'project_id'
        is not null if the 'project_forecast' module is installed.
        """
        project_forecast = self.env["ir.module.module"].search(
            [("name", "=", "project_forecast")]
        )
        if project_forecast.state == "installed":
            sql = """delete from planning_slot where project_id is not null;"""
            self._cr.execute(sql)

    def _clear_stock_package_type(self):
        """
        Clears stock package type related data from the database.
        Deletes records from 'stock_package_type'
        using `check_and_delete`.
        """
        stock_package_type = "stock_package_type"
        self.check_and_delete(stock_package_type)

    def _clear_stock_location(self):
        """
        Clears stock location related data from the database.
        If the 'stock' module is installed, updates
        'internal_transit_location_id' of 'res_company' to NULL.
        Then, iterates through and clears several tables
        related to stock locations using `check_and_delete`.
        """
        stock = self.env["ir.module.module"].search([("name", "=", "stock")])
        if stock.state == "installed":
            sql = """ update res_company set internal_transit_location_id=NULL;"""
            self._cr.execute(sql)
        stock_location_list = [
            "stock_move_line",
            "stock_quant",
            "sale_order",
            "pos_session",
            "pos_config",
            "purchase_order",
            "mrp_production",
            "stock_taxmove_line",
            "stock_picking",
            "stock_warehouse_orderpoint",
            "stock_move",
            "stock_rule",
            "mrp_workorder",
        ]

        for stock_location in stock_location_list:
            self.check_and_delete(stock_location)
        self._cr.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public' AND table_name = 'stock_location'
                        )
                    """)
        table_exists = self._cr.fetchone()[0]
        if table_exists:
            if self.company_id:
                sql = (
                        """
                        UPDATE stock_location
                        SET active = FALSE
                        WHERE  company_id = %s and usage='internal'

                    """
                        % self.company_id.id
                )
                self._cr.execute(sql)
            else:
                sql = (
                    """
                    UPDATE stock_location
                    SET active = FALSE
                    WHERE usage = 'internal'

                """
                )
                self._cr.execute(sql)

    def _clear_stock_rule(self):
        """
        Clears stock move & rule related data
        from the database.
        """
        stock_rule_list = ["stock_move", "stock_rule"]
        for stock_rule in stock_rule_list:
            self.check_and_delete(stock_rule)

    def _clear_stock_warehouse(self):
        """
        Clears stock warehouse related data from the database.
        Iterates through and clears several tables
        related to stock warehouses using `check_and_delete`.
        """
        stock_warehouse_list = [
            "mrp_workorder",
            "stock_move",
            "mrp_production",
            "purchase_order",
            "pos_session",
            "pos_config",
            "sale_order",
            "stock_rule",
            "stock_picking",
            "stock_warehouse",
        ]
        for stock_warehouse in stock_warehouse_list:
            self.check_and_delete(stock_warehouse)

    def _clear_product_supplierinfo(self):
        """
        Clears product supplier info data from the
        database using check_and_delete method.
        """
        product_supplierinfo = "product_supplierinfo"
        self.check_and_delete(product_supplierinfo)

    def _clear_purchase_requisition(self):
        """
        Clears purchase requisition data from
        the database using check_and_delete method.
        """
        purchase_requisition = "purchase_requisition"
        self.check_and_delete(purchase_requisition)

    def _clear_sale_quotation_templates(self):
        """
        Clears sale order template  data from
        the database using check_and_delete method.
        """
        sale_order_template = "sale_order_template"
        self.check_and_delete(sale_order_template)

    def _clear_field_service_task(self):
        """
        Clears field service task related data from the database.

        Deletes records from 'project_task' where 'project_id'
        matches conditions based on whether 'industry_fsm'
        module is installed and if a company is specified.
        """
        project_task = "project_task"
        if (
                self.env["ir.module.module"].search(
                    [("name", "=", "industry_fsm"), ("state", "=", "installed")]
                )
                and self.company_id
        ):
            sql = (
                    """
                    DELETE FROM project_task
                    WHERE project_id IN (
                    SELECT id FROM project_project
                    WHERE is_fsm = TRUE AND company_id = %s
                )
                """
                    % self.company_id.id
            )

            self._cr.execute(sql)

        elif (
                self.env["ir.module.module"].search(
                    [("name", "=", "industry_fsm"), ("state", "=", "installed")]
                )
                and not self.company_id
        ):
            sql = """
                DELETE FROM project_task
                WHERE project_id IN (
                SELECT id FROM project_project
                WHERE is_fsm = TRUE
            )
            """

            self._cr.execute(sql)

        else:
            pass

        self.clear_mail_activity_records('project.task', project_task)
        self.clear_mail_message_records('project.task', project_task)

    def _clear_mail_activity_type(self):
        """
        Clears mail activity type related data from the database.

        Deletes records from 'hr_plan_activity_type' and then
        from a list of related tables using `check_and_delete`.
        """
        activity_actions = self.env['ir.actions.server'].sudo().search([('activity_type_id', '!=', False)])
        if activity_actions:
            sql = """
                DELETE FROM ir_actions WHERE id in (%s);
            """ % (tuple(activity_actions.ids))
            self._cr.execute(sql)

        mail_activity_type_list = [
            "mail_activity",
            "hr_plan_activity_type",
        ]
        self._cr.execute("""
                                        SELECT EXISTS (
                                            SELECT FROM information_schema.tables
                                            WHERE table_schema = 'public' AND table_name = 'mail_activity_type'
                                        )
                                    """)
        table_exists = self._cr.fetchone()[0]
        if table_exists:
            if self.company_id:
                sql = (
                        """
                        UPDATE mail_activity_type
                        SET active = False
                        WHERE  company_id = %s

                    """
                        % self.company_id.id
                )
                self._cr.execute(sql)
            else:
                sql = (
                    """
                    UPDATE mail_activity_type
                    SET active = False
                """
                )
                self._cr.execute(sql)
        for mail_activity_type in mail_activity_type_list:
            self.check_and_delete(mail_activity_type)

    def _clear_pricelists(self):
        """
        Clears sale order. product pricelist, pos_config,
        pos seesion data from the database using
        check_and_delete method.
        """
        product_pricelist_list = [
            "product_pricelist",
        ]
        for product_pricelist in product_pricelist_list:
            self.check_and_delete(product_pricelist)

    def _clear_inv_pymt(self):
        """
        Clears payment related data from the
        database using check_and_delete method.
        """
        payment_list = [
            "account_partial_reconcile",
            "account_payment_register",
            "account_move_line",
            "account_move",
            "account_payment",
        ]
        for payment in payment_list:
            self.check_and_delete(payment)

    def _clear_cus_ven(self):
        """
        Clears customer and vendor data for the current company.
        Deletes records from 'res_partner' that are not
        associated with 'res_users' or 'res_company'
        and belong to the current company.
        """
        if self.company_id:
            delete_rp = """
                DELETE FROM res_partner
                WHERE id NOT IN (
                    SELECT partner_id FROM res_users
                    UNION
                    SELECT partner_id FROM res_company
                )  AND create_uid not in  (
                    SELECT id FROM res_users WHERE login = '__system__'
                );
            """
            self._cr.execute(delete_rp)
        else:
            delete_rp = """
                    DELETE FROM res_partner
                    WHERE id NOT IN (
                        SELECT partner_id FROM res_users
                        UNION
                        SELECT partner_id FROM res_company
                    ) AND create_uid not in  (
                    SELECT id FROM res_users WHERE login = '__system__'
                    );
                """
            self._cr.execute(delete_rp)

            table_name = "res_partner"
            self.clear_mail_activity_records('res.partner', table_name)
            self.clear_mail_message_records('res.partner', table_name)

    def _clear_coa(self):
        """
        Clears account & post related data from
        the database using check_and_delete method.
        """
        coa_list = [
            "pos_payment",
            "pos_order",
            "pos_session",
            "pos_config",
            "account_move_line",
            "account_move",
            "account_payment",
            "account_fiscal_position_tax",
            "account_reconcile_model",
            "account_reconcile_model_line",
            "account_partial_reconcile",
            "account_tax",
            "account_bank_statement_line",
            "account_bank_statement",
            "pos_payment_method",
            "account_transfer_model_line",
            "account_transfer_model",
            "hr_expense_sheet",
        ]
        self._cr.execute("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables
                                    WHERE table_schema = 'public' AND table_name = 'account_account'
                                )
                            """)
        table_exists = self._cr.fetchone()[0]
        if table_exists:
            if self.company_id:
                sql = (
                        """
                        UPDATE account_account
                        SET deprecated = True
                        WHERE  company_id = %s

                    """
                        % self.company_id.id
                )
                self._cr.execute(sql)
                sql = (
                        """
                        UPDATE account_journal
                        SET active = False
                        WHERE  company_id = %s

                    """
                        % self.company_id.id
                )
                self._cr.execute(sql)
            else:
                sql = (
                    """
                    UPDATE account_account
                    SET deprecated = True
                """
                )
                self._cr.execute(sql)
                sql = (
                    """
                    UPDATE account_journal
                    SET active = False
                """
                )
                self._cr.execute(sql)

        for coa in coa_list:
            self.check_and_delete(coa)

    def _clear_account_payment_term(self):
        """
        Clears account payment term data from
        the database using check_and_delete method.
        """
        account_payment_term = "account_payment_term"
        self.check_and_delete(account_payment_term)

    def _clear_journal(self):
        """
        Clears account move line & account move data
        from the database using check_and_delete method.
        """
        accounts = ["account_move_line", "account_move"]
        for acc in accounts:
            self.check_and_delete(acc)

    def _clear_project(self):
        """
        Clears project related data from the
        database using check_and_delete method.
        """
        project_list = [
            "project_task_stage_personal",
            "project_update",
            "project_collaborator",
            "project_sale_line_employee_map",
            "project_task",
            "project_tags",
            "project_milestone",
            "account_analytic_line",
        ]
        self._cr.execute("""
                                        SELECT EXISTS (
                                            SELECT FROM information_schema.tables
                                            WHERE table_schema = 'public' AND table_name = 'project_project'
                                        )
                                    """)
        table_exists = self._cr.fetchone()[0]
        if table_exists:
            if self.company_id:
                sql = (
                        """
                        DELETE FROM project_project
                        WHERE  user_id not in (select id from res_users where login ='__system__') and company_id = %s

                    """
                        % self.company_id.id
                )
                self._cr.execute(sql)
            else:
                sql = (
                    """
                    DELETE FROM project_project
                    WHERE  user_id not in (select id from res_users where login ='__system__') 
                """
                )
                self._cr.execute(sql)
            for project in project_list:
                self.check_and_delete(project)

    def _clear_project_task(self):
        """
        Clears account analytic line & project task
        data from the database using check_and_delete method.
        """
        task_list = ["account_analytic_line"]
        self._cr.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public' AND table_name = 'project_task'
                        )
                    """)
        table_exists = self._cr.fetchone()[0]
        if table_exists:
            if self.company_id:
                sql = (
                        """
                        DELETE FROM project_task
                        WHERE  project_id not in (select id from project_project where user_id in (select id from res_users where login ='__system__')) and company_id = %s

                    """
                        % self.company_id.id
                )
                self._cr.execute(sql)
            else:
                sql = (
                    """
                    DELETE FROM project_task
                    WHERE  project_id not in (select id from project_project where user_id in (select id from res_users where login ='__system__')) 

                """
                )
                self._cr.execute(sql)
            for task in task_list:
                self.check_and_delete(task)

    def _clear_project_timesheet(self):
        """
        Clears account analytic line data from the
        database using check_and_delete method.
        """
        analytic_line = "account_analytic_line"
        self.check_and_delete(analytic_line)

    def _clear_mrp_order(self):
        """
        Clears crm lead data from the database using check_and_delete method.
        """
        mrp_workorder_production_list = ["mrp_workorder", "mrp_production"]
        for work_prod in mrp_workorder_production_list:
            self.check_and_delete(work_prod)

    def _clear_crm(self):
        """
        Clears crm lead data from the database
        using check_and_delete method.
        """
        crm_lead = "crm_lead"
        self.check_and_delete(crm_lead)

    def _clear_crm_lead_mining_requests(self):
        """
        Clears crm iap lead mining request data
        from the database using check_and_delete method.
        """
        crm_iap_lead_mining_request = "crm_iap_lead_mining_request"
        self.check_and_delete(crm_iap_lead_mining_request)

    def _clear_crm_lost_reason(self):
        """
        Clears crm lost reason data from the database
        using check_and_delete method.
        """
        crm_lost_reason = "crm_lost_reason"
        self.check_and_delete(crm_lost_reason)

    def _clear_hr_expense(self):
        """
        Clears hr expense data from the
        database using check_and_delete method.
        """
        hr_expense = "hr_expense"
        self.check_and_delete(hr_expense)

    def _clear_bom_mrp_order(self):
        """
        Clears mrp work center related data from the database.

        Iterates through and clears several mrp related tables
        using `check_and_delete method`.
        """
        mrp_workorder_list = ["mrp_workorder", "mrp_production", "mrp_bom"]
        for mrp_workorder in mrp_workorder_list:
            self.check_and_delete(mrp_workorder)

    def _clear_mrp_workcenter(self):
        """
        Clears mrp work center related data from the database.

        Iterates through and clears several mrp related tables
         using `check_and_delete method`.
        """
        mrp_workcenter_list = [
            "mrp_workcenter_productivity",
            "mrp_workorder",
            "mrp_routing_workcenter",
            "mrp_workcenter",
        ]
        for mrp_workcenter in mrp_workcenter_list:
            self.check_and_delete(mrp_workcenter)

    def _clear_pos_order(self):
        """
        Clears pos related data from the database.

        Iterates through and clears several pos_payment
        and post_order tables using `check_and_delete method`.
        """
        pos_order_list = ["pos_payment", "pos_order"]
        for pos_order in pos_order_list:
            self.check_and_delete(pos_order)

    def _clear_pos_bill(self):
        """
        Clears pos bill data from the
        database using check_and_delete method.
        """
        pos_bill = "pos_bill"
        self.check_and_delete(pos_bill)

    def _clear_pos_category(self):
        """
        Clears pos category data from the
        database using check_and_delete method.
        """
        pos_category = "pos_category"
        self.check_and_delete(pos_category)

    def _clear_quality_alert(self):
        """
        Clears quality alert data from the
        database using check_and_delete method.
        """
        quality_alert = "quality_alert"
        self.check_and_delete(quality_alert)

    def _clear_quality_check(self):
        """
        Clears quality check data from the
        database using check_and_delete method.
        """
        quality_check = "quality_check"
        self.check_and_delete(quality_check)

    def _clear_quality_point(self):
        """
        Clears quality point data from the
        database using check_and_delete method.
        """
        quality_point = "quality_point"
        self.check_and_delete(quality_point)

    def _clear_maintenance_request(self):
        """
        Clears maintenance request data from the
         database using check_and_delete method.
        """
        maintenance_request = "maintenance_request"
        self.check_and_delete(maintenance_request)

    def _clear_maintenance_equipment(self):
        """
        Clears maintenance equipment data from the
        database using check_and_delete method.
        """
        maintenance_equipment = "maintenance_equipment"
        self.check_and_delete(maintenance_equipment)

    def _clear_maintenance_equipment_category(self):
        """
        Clears maintenance equipment category data
        from the database using check_and_delete method.
        """
        maintenance_equipment_category = "maintenance_equipment_category"
        self.check_and_delete(maintenance_equipment_category)

    def _clear_helpdesk_ticket(self):
        """
        Clears helpdesk ticket data from the
        database using check_and_delete method.
        """
        helpdesk_ticket = "helpdesk_ticket"
        self.check_and_delete(helpdesk_ticket)
        self.clear_mail_activity_records('helpdesk.ticket', helpdesk_ticket)
        self.clear_mail_message_records('helpdesk.ticket', helpdesk_ticket)

    def _clear_hr_contract(self):
        """
        Clears hr contract data from the database
        using check_and_delete method.
        """
        hr_contract = "hr_contract"
        self.check_and_delete(hr_contract)
        self.clear_mail_activity_records('hr.contract', hr_contract)
        self.clear_mail_message_records('hr.contract', hr_contract)

    def _clear_product_product(self):
        sale_project_forecast = self.env["ir.module.module"].search(
            [("name", "=", "sale_project_forecast")]
        )
        if sale_project_forecast.state == "installed":
            sql = (
                """delete from planning_slot where sale_line_id is not null;"""
            )
            self._cr.execute(sql)
        product_product_list = [
            "sale_order_template_line",
            "hr_expense",
            "project_sale_line_employee_map",
            "project_collaborator",
            "project_update",
            "project_project",
            "stock_valuation_layer",
            "stock_quant",
            "mrp_production",
            "mrp_bom_line",
            "mrp_bom",
            "sale_order_template_option",
            "account_move_line",
            "stock_lot",
            "purchase_order_line",
            "stock_move",
            "sale_order_line",
            "pos_combo_line",
            "loyalty_reward",
            "delivery_carrier",
            "product_product",

        ]
        for product_product in product_product_list:
            self.check_and_delete(product_product)

    def _clear_product_category(self):
        sale_project_forecast = self.env["ir.module.module"].search(
            [("name", "=", "sale_project_forecast")]
        )
        if sale_project_forecast.state == "installed":
            sql = (
                """delete from planning_slot where sale_line_id is not null;"""
            )
            self._cr.execute(sql)
        product_category_list = [
            "sale_order_template_line",
            "hr_expense",
            "stock_valuation_layer",
            "project_sale_line_employee_map",
            "project_collaborator",
            "project_update",
            "project_project",
            "stock_quant",
            "mrp_production",
            "mrp_bom_line",
            "mrp_bom",
            "sale_order_template_option",
            "account_move_line",
            "stock_lot",
            "purchase_order_line",
            "stock_move",
            "sale_order_line",
            "delivery_carrier",
            "product_product",
            "product_template",
            "loyalty_reward",
        ]
        for product_category in product_category_list:
            self.check_and_delete(product_category)
        self._cr.execute("""
                                        SELECT EXISTS (
                                            SELECT FROM information_schema.tables
                                            WHERE table_schema = 'public' AND table_name = 'product_category'
                                        )
                                    """)
        table_exists = self._cr.fetchone()[0]
        if table_exists:
            if self.company_id:
                sql = (
                        """
                        DELETE from  product_category
                        WHERE  NAME NOT IN ('All','Expenses','Saleable') and company_id = %s

                    """
                        % self.company_id.id
                )
                self._cr.execute(sql)
            else:
                sql = (
                    """
                    DELETE from  product_category
                    WHERE  NAME NOT IN ('All','Expenses','Saleable') 

                """
                )
                self._cr.execute(sql)

    def _clear_gamification_badge(self):
        """
        Clears gamification badge data from
        the database using the check_and_delete method.
        """
        gamification_badge = "gamification_badge"
        self.check_and_delete(gamification_badge)

    def _clear_account_tax_group(self):
        """
        Clears account related data from the database.

        Iterates through and clears several account-related
         tables using `check_and_delete method`.
        """

        account_tax_group_list = [
            "account_fiscal_position_tax",
            "account_move_line",
            "account_reconcile_model",
            "account_reconcile_model_line",
            "account_tax",
            "account_tax_group",
        ]

        for account_tax_group in account_tax_group_list:
            self.check_and_delete(account_tax_group)

    @api.onchange("all_data")
    def all_true(self):
        """
        Sets multiple boolean fields to True or False
        based on the value of `all_data`.

        When the `all_data` attribute is changed,
        this method sets the values of the specified
        fields to True if `all_data` is truthy,
        and False otherwise.

        List of fields affected:
        """
        fields = [
            "so_do",
            "po",
            "all_trans",
            "inv_pymt",
            "journals",
            "cus_ven",
            "coa",
            "project",
            "project_task",
            "timesheet",
            "mrp",
            "workcentre_mrp",
            "crm_pipeline",
            "crm_lead_mining_requests",
            "crm_lost_reason",
            "sales_teams",
            "quotation_templates",
            "activity_types",
            "pricelists",
            "bom_mrp",
            "package_types",
            "expenses",
            "locations",
            "rules",
            "warehouses",
            "vendor_pricelist",
            "blanket_order",
            "pos_order",
            "pos_bill",
            "pos_product_category",
            "quality_alert",
            "quality_check",
            "quality_point",
            "maintenance_request",
            "maintenance_equipment",
            "maintenance_equipment_category",
            "helpdesk_ticket",
            "product_product",
            "product_category",
            "account_payment_term",
            "account_tax_group",
            "gamification_badge",
            "hr_contract",
            "field_service_task",
            "by_resources",
            "by_roles",
            "by_projects",
        ]
        value = bool(self.all_data)
        for field in fields:
            setattr(self, field, value)

    def clean_data(self):
        """
        Clears various data records based on specified conditions.

        This method iterates over each record in the
        current object and clears data depending on
        the attributes of each record.
        If a record has the `all_data` attribute set to True,
        it clears all types of data using a predefined set
        of methods.
        Otherwise, it selectively clears data based on individual
        conditions.

        """
        clear_methods_all = [
            self._clear_so_order,
            self._clear_po,
            self._clear_transfer,
            self._clear_inv_pymt,
            self._clear_coa,
            self._clear_cus_ven,
            self._clear_project,
            self._clear_project_task,
            self._clear_project_timesheet,
            self._clear_mrp_order,
            self._clear_sales_teams,
            self._clear_sale_quotation_templates,
            self._clear_mail_activity_type,
            self._clear_pricelists,
            self._clear_crm,
            self._clear_crm_lost_reason,
            self._clear_crm_lead_mining_requests,
            self._clear_bom_mrp_order,
            self._clear_mrp_workcenter,
            self._clear_hr_expense,
            self._clear_stock_package_type,
            self._clear_stock_location,
            self._clear_stock_rule,
            self._clear_stock_warehouse,
            self._clear_product_supplierinfo,
            self._clear_purchase_requisition,
            self._clear_pos_order,
            self._clear_pos_bill,
            self._clear_pos_category,
            self._clear_quality_alert,
            self._clear_quality_check,
            self._clear_quality_point,
            self._clear_maintenance_request,
            self._clear_maintenance_equipment,
            self._clear_maintenance_equipment_category,
            self._clear_helpdesk_ticket,
            self._clear_product_product,
            self._clear_product_category,
            self._clear_account_payment_term,
            self._clear_account_tax_group,
            self._clear_gamification_badge,
            self._clear_hr_contract,
            self._clear_field_service_task,
            self._clear_planning_by_resources,
            self._clear_planning_by_roles,
            self._clear_planning_by_projects,
        ]

        clear_conditions = {
            "so_do": self._clear_so_order,
            "po": self._clear_po,
            "all_trans": self._clear_transfer,
            "inv_pymt": self._clear_inv_pymt,
            "journals": self._clear_journal,
            "coa": self._clear_coa,
            "cus_ven": self._clear_cus_ven,
            "project": self._clear_project,
            "project_task": self._clear_project_task,
            "timesheet": self._clear_project_timesheet,
            "crm_pipeline": self._clear_crm,
            "sales_teams": self._clear_sales_teams,
            "quotation_templates": self._clear_sale_quotation_templates,
            "pricelists": self._clear_pricelists,
            "activity_types": self._clear_mail_activity_type,
            "crm_lost_reason": self._clear_crm_lost_reason,
            "crm_lead_mining_requests": self._clear_crm_lead_mining_requests,
            "mrp": self._clear_mrp_order,
            "workcentre_mrp": self._clear_mrp_workcenter,
            "bom_mrp": self._clear_bom_mrp_order,
            "expenses": self._clear_hr_expense,
            "package_types": self._clear_stock_package_type,
            "locations": self._clear_stock_location,
            "rules": self._clear_stock_rule,
            "warehouses": self._clear_stock_warehouse,
            "vendor_pricelist": self._clear_product_supplierinfo,
            "blanket_order": self._clear_purchase_requisition,
            "pos_order": self._clear_pos_order,
            "pos_bill": self._clear_pos_bill,
            "pos_product_category": self._clear_pos_category,
            "quality_alert": self._clear_quality_alert,
            "quality_check": self._clear_quality_check,
            "quality_point": self._clear_quality_point,
            "maintenance_request": self._clear_maintenance_request,
            "maintenance_equipment": self._clear_maintenance_equipment,
            "maintenance_equipment_category": self._clear_maintenance_equipment_category,
            "helpdesk_ticket": self._clear_helpdesk_ticket,
            "product_product": self._clear_product_product,
            "product_category": self._clear_product_category,
            "account_payment_term": self._clear_account_payment_term,
            "account_tax_group": self._clear_account_tax_group,
            "gamification_badge": self._clear_gamification_badge,
            "hr_contract": self._clear_hr_contract,
            "field_service_task": self._clear_field_service_task,
            "by_resources": self._clear_planning_by_resources,
            "by_roles": self._clear_planning_by_roles,
            "by_projects": self._clear_planning_by_projects,
        }

        for rec in self:
            if rec.all_data:
                for method in clear_methods_all:
                    method()
            else:
                for condition, method in clear_conditions.items():
                    if getattr(rec, condition, False):
                        method()
