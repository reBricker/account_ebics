# Copyright 2026 reBricker.
# License LGPL-3 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class EbicsXfer(models.TransientModel):
    _inherit = "ebics.xfer"

    # Transfers normally leave the key file untouched; saving afterwards is cheap
    # and covers library versions that update the file (e.g. bank key renewals).

    def ebics_upload(self):
        try:
            return super().ebics_upload()
        finally:
            self.ebics_userid_id._keystore_save()

    def ebics_download(self):
        try:
            return super().ebics_download()
        finally:
            self.ebics_userid_id._keystore_save()
