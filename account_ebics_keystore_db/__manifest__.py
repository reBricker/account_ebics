# Copyright 2026 reBricker.
# License LGPL-3 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "EBICS keys stored in the database",
    "version": "20.0.1.0.0",
    "license": "LGPL-3",
    "author": "reBricker",
    "website": "https://github.com/reBricker/account_ebics",
    "category": "Accounting & Finance",
    "summary": "Keep a copy of the EBICS key files in the database (container deployments)",
    "depends": ["account_ebics"],
    "data": ["views/ebics_userid_views.xml"],
    "installable": True,
}
