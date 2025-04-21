import logging
from odoo import _, models, fields
from odoo import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class UtilsCounter(models.Model):
    _name = 'utils.counter'
    _description = 'The general Counter for gfza'
    _rec_name = 'counter'
    _order = 'id desc'
    _sql_constraints = [('unique_key', 'UNIQUE(key)', 'key must be unique')]

    key = fields.Char(string='Key', required=True)
    description = fields.Text(string='Description', required=False)
    counter = fields.Integer(string='Counter', required=True)

    def get_current_counter(self, key):
        self._cr.execute(
            'SELECT id, counter, key FROM utils_counter WHERE key = %s LIMIT 1 FOR NO KEY UPDATE ', [key])
        result = self._cr.fetchall()
        if result:
            for rec in result:
                return {"id": rec[0], "counter": rec[1], "key": rec[2]}
        else:
            counter_model = self.env['utils.counter']
            new_counter = counter_model.create({
                'key': key,
                'counter': 0,
            })
            if new_counter:
                self._cr.execute(
                    'SELECT id, counter, key FROM utils_counter WHERE key = %s  LIMIT 1 FOR NO KEY UPDATE',
                    [key])
                result = self._cr.fetchall()
                if result:
                    for rec in result:
                        return {"id": rec[0], "counter": rec[1], "key": rec[2]}

    def update_current_counter(self, counter_id, new_counter):
        results_counter = self.env['utils.counter'].search([('id', '=', counter_id)])
        if results_counter:
            results_counter.write({
                'counter': new_counter,
            })
