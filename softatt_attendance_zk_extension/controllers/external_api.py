# -*- coding: utf-8 -*-
from time import strftime
from odoo import http
from odoo.http import request
import requests 
import werkzeug.wrappers 
from psycopg2 import sql
import json
import logging

_logger = logging.getLogger(__name__)

class AttendenceTransactions(http.Controller):

    @http.route('/attendence/transactions/<int:max_id>/<int:limit>', methods=["GET", "POST"], type='http',  auth="user", csrf=False)
    def transactions(self,max_id, limit,**kw):
            devices=request.env.user.device_ids.ids
            if len(devices) == 0:
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type="application/json; charset=utf-8",
                    response=json.dumps({"Error": "No Devices found!",}))
            _logger.error(kw)
            data=request.httprequest.data
            body=json.loads(data)['params'] if data else {}            
            if body.get('device_codes', False):
                params = (max_id, tuple(body.get('device_codes')), limit)
            else:
                params = (max_id, tuple(devices), limit)
                
            query = """
                SELECT
                    t.id,
                    t.emp_code,
                    t.punch_state,
                    d.id as device_id,
                    d.name as area,
                    to_char(t.punch_time, 'YYYY-MM-DD HH24:MI:SS') as punch_time,
                    punch_state
                FROM
                    sa_biometric_att t
                    LEFT JOIN sa_biometric_device d ON(d.id=t.device_id)
                WHERE
                    t.id > %s
                    AND t.device_id IN %s
                ORDER BY
                    punch_time, punch_state
                LIMIT %s
            """
            request.env.cr.execute(query, params)
            transactions=request.env.cr.dictfetchall()
            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                response=json.dumps({
                    "transactions": transactions,
                    }))