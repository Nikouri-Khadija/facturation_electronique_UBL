{
    'name': 'Facturation électronique (UBL)',
    'version': '18.0.1.1.0',
    'category': 'Accounting/Accounting',
    'summary': "Génération du fichier XML UBL 2.1 des factures clients",
    'author': "Nikouri Khadija",
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/facture_ubl_historique_views.xml',
        'report/facture_ubl_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
