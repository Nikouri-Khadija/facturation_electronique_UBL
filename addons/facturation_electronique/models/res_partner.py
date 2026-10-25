from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fe_identifiant_fiscal = fields.Char(
        string="Identifiant fiscal (IF)",
        help="Identifiant fiscal du client, repris dans la facture électronique.",
    )
