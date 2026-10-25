import base64

from lxml import etree

from odoo import fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    historique_ubl_ids = fields.One2many(
        'facturation_electronique.historique', 'facture_id', string="Historique XML UBL",
    )
    historique_ubl_count = fields.Integer(compute='_compute_historique_ubl_count')

    def _compute_historique_ubl_count(self):
        donnees = self.env['facturation_electronique.historique']._read_group(
            [('facture_id', 'in', self.ids)], ['facture_id'], ['__count'],
        )
        compte = {facture.id: total for facture, total in donnees}
        for move in self:
            move.historique_ubl_count = compte.get(move.id, 0)

    # ------------------------------------------------------------------
    # Facture électronique UBL 2.1
    # ------------------------------------------------------------------
    @staticmethod
    def _ubl_montant(valeur):
        return '%.2f' % valeur

    def _ubl_partie(self, partner, identifiant_fiscal):
        """Données UBL d'une partie (vendeur ou client)."""
        return {
            'nom': partner.name or '',
            'rue': ' '.join(filter(None, [partner.street, partner.street2])),
            'ville': partner.city or '',
            'code_postal': partner.zip or '',
            'pays': partner.country_id.code or 'MA',
            'ice': partner.company_registry or '',
            'if': identifiant_fiscal or '',
            'telephone': partner.phone or partner.mobile or '',
            'email': partner.email or '',
        }

    def _ubl_valeurs(self):
        """Valeurs du modèle facturation_electronique.facture_ubl."""
        self.ensure_one()
        m = self._ubl_montant
        lignes_produit = self.invoice_line_ids.filtered(lambda l: l.display_type == 'product')

        def tva_de(ligne):
            return ligne.tax_ids.filtered(
                lambda t: t.amount_type == 'percent' and t.amount >= 0
            )[:1]

        # Récapitulatif par taux de TVA
        par_taux = {}
        for ligne in lignes_produit:
            taux = tva_de(ligne).amount if tva_de(ligne) else 0.0
            base = par_taux.get(taux, 0.0)
            par_taux[taux] = base + ligne.price_subtotal
        taxes = [
            {
                'base': m(base),
                'montant': m(self.currency_id.round(base * taux / 100.0)),
                'categorie': 'S' if taux else 'Z',
                'taux': m(taux),
            }
            for taux, base in sorted(par_taux.items())
        ]
        return {
            'facture': {
                'numero': self.name,
                'date': self.invoice_date,
                'echeance': self.invoice_date_due,
                'type_code': '380',
            },
            'devise': self.currency_id.name,
            'vendeur': self._ubl_partie(self.company_id.partner_id, self.company_id.fe_identifiant_fiscal),
            'client': self._ubl_partie(self.partner_id.commercial_partner_id,
                                       self.partner_id.commercial_partner_id.fe_identifiant_fiscal),
            'taxes': taxes,
            'totaux': {
                'ht': m(self.amount_untaxed),
                'tva': m(self.amount_tax),
                'ttc': m(self.amount_total),
            },
            'lignes': [
                {
                    'quantite': m(ligne.quantity),
                    'montant_ht': m(ligne.price_subtotal),
                    'nom': ligne.product_id.display_name or ligne.name or '',
                    'categorie': 'S' if tva_de(ligne).amount else 'Z',
                    'taux': m(tva_de(ligne).amount or 0.0),
                    'prix_unitaire': m(ligne.price_unit),
                }
                for ligne in lignes_produit
            ],
        }

    def _ubl_contenu(self):
        """Contenu XML UBL de la facture (bytes)."""
        self.ensure_one()
        xml = self.env['ir.qweb']._render('facturation_electronique.facture_ubl', self._ubl_valeurs())
        racine = etree.fromstring(str(xml).encode('utf-8'), etree.XMLParser(remove_blank_text=True))
        return etree.tostring(racine, pretty_print=True, xml_declaration=True, encoding='UTF-8')

    def action_generer_facture_ubl(self):
        """Génère le fichier XML UBL de la facture client et le télécharge."""
        self.ensure_one()
        if self.move_type != 'out_invoice' or self.state != 'posted':
            raise UserError("La facture UBL se génère pour une facture client comptabilisée.")
        nom = 'facture-%s.xml' % self.name.replace('/', '-')
        historique = self.env['facturation_electronique.historique'].create({
            'facture_id': self.id,
            'fichier': base64.b64encode(self._ubl_contenu()),
            'fichier_nom': nom,
        })
        return historique.action_telecharger()

    def action_voir_historique_ubl(self):
        """Historique des fichiers XML UBL générés pour la facture."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'facturation_electronique.action_facture_ubl_historique')
        action['domain'] = [('facture_id', '=', self.id)]
        action['context'] = {'default_facture_id': self.id}
        return action
