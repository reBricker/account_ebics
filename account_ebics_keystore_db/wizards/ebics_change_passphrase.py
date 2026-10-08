# Copyright 2026 reBricker.
# License LGPL-3 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class EbicsChangePassphrase(models.TransientModel):
    _inherit = "ebics.change.passphrase"

    def change_passphrase(self):
        try:
            return super().change_passphrase()
        finally:
            self.ebics_userid_id._keystore_save()
