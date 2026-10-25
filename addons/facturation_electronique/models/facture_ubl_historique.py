from odoo import fields, models


class FactureUblHistorique(models.Model):
    _name = 'facturation_electronique.historique'
    _description = "Historique des factures électroniques UBL"
    _order = 'date_generation desc, id desc'
    _rec_name = 'fichier_nom'

    facture_id = fields.Many2one(
        'account.move', string="Facture", required=True, readonly=True,
        ondelete='cascade', index=True,
    )
    partner_id = fields.Many2one(
        related='facture_id.partner_id', string="Client", store=True,
    )
    company_id = fields.Many2one(
        related='facture_id.company_id', string="Société", store=True,
    )
    currency_id = fields.Many2one(related='facture_id.currency_id')
    montant_total = fields.Monetary(
        related='facture_id.amount_total', string="Montant TTC",
    )
    date_generation = fields.Datetime(
        string="Date de génération", required=True, readonly=True,
        default=fields.Datetime.now,
    )
    utilisateur_id = fields.Many2one(
        'res.users', string="Généré par", required=True, readonly=True,
        default=lambda self: self.env.user,
    )
    fichier = fields.Binary(string="Fichier XML", attachment=True, readonly=True)
    fichier_nom = fields.Char(string="Nom du fichier", readonly=True)

    def action_telecharger(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/fichier/%s?download=true' % (self._name, self.id, self.fichier_nom),
            'target': 'self',
        }
