# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields,models,api,_
from lxml import etree


class hide_view_nodes(models.Model):
    _name = 'sh.navbar.buttons.access'
    _description = 'Hide Navbar And Buttos'


    model_id = fields.Many2one(
        'ir.model', string='Model', index=True, required=True, ondelete='cascade')

    model_name = fields.Char(string='Model Name Jatin', related='model_id.model', readonly=True, store=True)
    
    sh_store_btn_data_ids = fields.Many2many('sh.store.model.data','sh_btn_hide_view_nodes_store_model_nodes_rel','sh_hide_id','sh_store_id',string='Hide Button',domain="[('sh_node_option','=','button')]")
    sh_store_page_data_ids = fields.Many2many('sh.store.model.data','sh_page_hide_view_nodes_store_model_nodes_rel','sh_hide_id','sh_store_id',string='Hide Tab/Page',domain="[('sh_node_option','=','page')]")

    access_manager_id = fields.Many2one('sh.access.manager','Access Management')


    def _store_btn_data(self,btn, smart_button=False,smart_button_string=False):
        # string_value is used in case of kanban view button store, 
        string_value = 'string_value' in self._context.keys() and self._context['string_value'] or False
        
        store_model_button_obj = self.env['sh.store.model.data']
        name = btn.get('string') or string_value
        if smart_button:
            name = smart_button_string + ' - (Smart Button)'
        store_model_button_obj.create({
                'model_id' : self.model_id.id,
                'sh_node_option' : 'button',
                'sh_attribute_name' : btn.get('name'),
                'sh_attribute_string' : name,
                'sh_button_type' : btn.get('type'),
                'sh_is_smart_button' : smart_button,
            })
       

    def _get_smart_btn_string(self,btn_list,type=False):
        store_model_button_obj = self.env['sh.store.model.data']
        def _get_span_text(span_list):
            name = ''
            for sp in span_list:
                if sp.text:
                    name = name  +' '+ sp.text
            name = name.strip()
            return name    

        for btn in btn_list:
            name = ''
            field_list = btn.findall('field')
            if field_list:
                name = field_list[0].get('string')
            else:
                span_list = btn.findall('span')
                if span_list:
                    name = _get_span_text(span_list)
                else:
                    div_list = btn.findall('div')
                    if div_list:
                        span_list = div_list[0].findall('span')
                        if span_list:
                            name = _get_span_text(span_list)
            if not name:
                try:
                    name = btn.get('string')
                except:
                    pass
            if name and (type == 'object' or type == 'action'):
                domain = [('sh_button_type','=',btn.get('type')),('sh_attribute_string','=',name),('model_id','=',self.model_id.id),('sh_node_option','=','button')]
                if type == 'object':
                    domain += [('sh_attribute_name','=',btn.get('name'))]
                if type == 'action':    
                    domain += [('sh_attribute_name','=',btn.get('name'))]
                smart_button_id = store_model_button_obj.search(domain)   
                if not smart_button_id:
                    self._store_btn_data(btn,smart_button=True,smart_button_string=name)
                else:
                    smart_button_id[0].sh_is_smart_button = True


    
    @api.model
    @api.onchange('model_id')
    def _get_button(self):
        store_model_nodes_obj = self.env['sh.store.model.data']
        view_obj = self.env['ir.ui.view']

        if self.model_id and self.model_name:
            

            view_list = ['form','list','kanban']
            for view in view_list:
                for views in view_obj.search([('model','=',self.model_name),('type','=',view),('inherit_id','=',False)]):
                    # res = self.env[self.model_name].sudo().fields_view_get(view_id=views.id,view_type=view)
                    res = self.env[self.model_name].sudo().get_view(view_id=views.id,view_type=view)
                    doc = etree.XML(res['arch'])
                    
                    object_link = doc.xpath("//a")
                    for btn in object_link:
                        if btn.text and '\n' not in btn.text and 'type' in btn.attrib.keys() and btn.attrib['type'] and 'name' in btn.attrib.keys() and btn.attrib['name']:
                            domain = [('sh_button_type','=',btn.get('type')),('sh_attribute_string','=',btn.text),('sh_attribute_name','=',btn.get('name')),('model_id','=',self.model_id.id),('sh_node_option','=','link')]
                            if not store_model_nodes_obj.search(domain):
                                store_model_nodes_obj.create({
                                    'model_id' : self.model_id.id,
                                    'sh_node_option' : 'link',
                                    'sh_attribute_name' : btn.get('name'),
                                    'sh_attribute_string' : btn.text,
                                    'sh_button_type' : btn.get('type'),
                                })
                            
                    object_button = doc.xpath("//button[@type='object']")
                    for btn in object_button:
                        string_value = btn.get('string')
                        if view == 'kanban' and not string_value:
                            try:
                                string_value = btn.text if not btn.text.startswith('\n') else False
                            except:
                                pass
                        if btn.get('name') and string_value:
                            domain = [('sh_button_type','=',btn.get('type')),('sh_attribute_string','=',string_value),('sh_attribute_name','=',btn.get('name')),('model_id','=',self.model_id.id),('sh_node_option','=','button')]
                            if not store_model_nodes_obj.search(domain):
                                self.with_context(string_value=string_value)._store_btn_data(btn)
                                
                    action_button = doc.xpath("//button[@type='action']")
                    for btn in action_button:
                        string_value = btn.get('string')
                        if view == 'kanban' and not string_value:
                            try:
                                string_value = btn.text if not btn.text.startswith('\n') else False
                            except:
                                pass
                        if btn.get('name') and string_value:
                            domain = [('sh_button_type','=',btn.get('type')),('sh_attribute_string','=',string_value),('sh_attribute_name','=',btn.get('name')),('model_id','=',self.model_id.id),('sh_node_option','=','button')]
                            if not store_model_nodes_obj.search(domain):
                                self.with_context(string_value=string_value)._store_btn_data(btn)

                    if doc.xpath("//form"):
                        ## Smart Buttons Extraction
                        smt_button_division = doc.xpath("//div[@class='oe_button_box']")
                        if smt_button_division:
                            smt_button_division = etree.tostring(smt_button_division[0])
                            smt_button_division = etree.XML(smt_button_division)

                            smt_object_button = smt_button_division.xpath("//button[@type='object']")
                            self._get_smart_btn_string(smt_object_button,type='object')
                            
                            smt_action_button = smt_button_division.xpath("//button[@type='action']")
                            self._get_smart_btn_string(smt_action_button,type='action')

                        ## Tab Extraction
                        page_list = doc.xpath("//page")
                        if page_list:
                            for page in page_list:
                                if page.get('string'):
                                    domain = [('sh_attribute_string','=',page.get('string')),('model_id','=',self.model_id.id),('sh_node_option','=','page')]
                                    if page.get('name'):
                                        domain += [('sh_attribute_name','=',page.get('name'))]
                                    store_model_nodes_id = store_model_nodes_obj.search(domain,limit=1)
                                    if not store_model_nodes_id:
                                        store_model_nodes_obj.create({
                                            'model_id' : self.model_id.id,
                                            'sh_attribute_name' : page.get('name'),
                                            'sh_attribute_string' : page.get('string'),
                                            'sh_node_option' : 'page',
                                        })
                        if self.model_name == 'res.config.settings':
                            for setting_page in doc.xpath("//div[@class='app_settings_block']"):
                                if setting_page.get('string'):
                                    domain = [('sh_attribute_string','=',setting_page.get('string')),('model_id','=',self.model_id.id),('sh_node_option','=','page')]
                                    if setting_page.get('data-key'):
                                        domain += [('sh_attribute_name','=',setting_page.get('data-key'))]
                                    store_model_nodes_id = store_model_nodes_obj.search(domain,limit=1)
                                    if not store_model_nodes_id:
                                        store_model_nodes_obj.create({
                                            'model_id' : self.model_id.id,
                                            'sh_attribute_name' : setting_page.get('data-key') or '',
                                            'sh_attribute_string' : setting_page.get('string'),
                                            'sh_node_option' : 'page',
                                        })

class ShStoreModelData(models.Model):
    _name = 'sh.store.model.data'
    _description = 'Store Model Nodes'
    _rec_name = 'sh_attribute_string'

    
    model_id = fields.Many2one('ir.model', string='Model', index=True, ondelete='cascade',required=True)
    sh_node_option = fields.Selection([('button','Button'),('page','Page'),('link','Link'),('filter', 'Filter'), ('groupby', 'Group By')],string="Node Option",required=True)
    sh_attribute_name = fields.Char('Attribute Name')
    sh_attribute_string= fields.Char('Attribute String',required=True)

    sh_button_type = fields.Selection([('object','Object'),('action','Action')],string="Button Type")
    sh_is_smart_button = fields.Boolean('Smart Button')
