# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.tools import config


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount = fields.Float(
        compute="_compute_discount",
        store=True,
        readonly=False,
    )

    @api.depends("order_id", "order_id.general_discount")
    def _compute_discount(self):
        res = super()._compute_discount()
        test_condition = not config["test_enable"] or (
            config["test_enable"]
            and self.env.context.get("test_sale_order_general_discount")
        )
        if not test_condition:
            return res
        for line in self:
            # We check the value of general_discount on origin too to cover
            # the case where a discount was set to a value != 0 and then
            # set again to 0 to remove the discount on all the lines at the same
            # time
            if not line.product_id.bypass_general_discount and (
                line.order_id.general_discount or line.order_id._origin.general_discount
            ):
                line.discount = line.order_id.general_discount
            else:
                line.discount = 0
        return res
