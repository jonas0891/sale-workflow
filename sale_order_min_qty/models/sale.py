# Copyright 2019 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    sale_min_qty = fields.Float(
        string="Min Qty",
        related="product_id.sale_min_qty",
        readonly=True,
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    force_sale_min_qty = fields.Boolean(
        related="product_id.force_sale_min_qty", readonly=True, store=True
    )
    is_qty_less_min_qty = fields.Boolean(
        string="Qty < Min Qty", compute="_compute_is_qty_less_min_qty"
    )
    sale_multiple_qty = fields.Float(
        string="Multiple Qty",
        related="product_id.sale_multiple_qty",
        readonly=True,
        store=True,
        digits=dp.get_precision("Product Unit of Measure"),
    )
    is_qty_not_multiple_qty = fields.Boolean(
        string="Not Multiple Qty", compute="_compute_is_qty_not_multiple_qty"
    )

    @api.constrains("product_uom_qty")
    def check_constraint_min_qty(self):
        invaild_min_lines = []
        msg = ""
        line_to_test = self.filtered(
            lambda l: not l.product_id.force_sale_min_qty and l.is_qty_less_min_qty
        )
        for line in line_to_test:
            invaild_min_lines.append(
                _('Product "%s": Min Quantity %s.')
                % (line.product_id.name, line.product_id.sale_min_qty)
            )

        if invaild_min_lines:
            msg += _(
                "Check minimum order quantity for this products: * \n"
            ) + "\n ".join(invaild_min_lines)
            msg += _(
                "\n* If you want sell quantity less than Min Quantity"
                ',Check "force min quatity" on product'
            )

        invaild_multiple_lines = []
        line_to_test = self.filtered(lambda l: l.is_qty_not_multiple_qty)
        for line in line_to_test:
            invaild_multiple_lines.append(
                _('Product "%s": multiple Quantity %s.')
                % (line.product_id.name, line.product_id.sale_multiple_qty)
            )

        if invaild_multiple_lines:
            msg += _(
                "Check multiple order quantity for this products: * \n"
            ) + "\n ".join(invaild_multiple_lines)
            msg += _(
                "\n* If you want sell quantity not multiple Quantity"
                ",Set multiple quantity to 0 on product or product template"
                " or product category"
            )

        if msg:
            raise ValidationError(msg)

    @api.multi
    @api.depends("product_uom_qty", "sale_min_qty")
    def _compute_is_qty_less_min_qty(self):
        for line in self:
            rounding = line.product_uom.rounding
            product_qty = line.product_uom._compute_quantity(
                line.product_uom_qty, line.product_id.uom_id
            )
            line.is_qty_less_min_qty = (
                float_compare(
                    product_qty, line.sale_min_qty, precision_rounding=rounding
                )
                < 0
            )

    @api.multi
    @api.depends("product_uom_qty", "sale_multiple_qty")
    def _compute_is_qty_not_multiple_qty(self):
        for line in self:
            product_qty = line.product_uom._compute_quantity(
                line.product_uom_qty, line.product_id.uom_id
            )
            line.is_qty_not_multiple_qty = (
                line.sale_multiple_qty > 0 and product_qty % line.sale_multiple_qty != 0
            )
