from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    fe_identifiant_fiscal = fields.Char(
        string="Identifiant fiscal (IF)",
        help="Identifiant fiscal de la société, repris dans la facture électronique.",
    )
