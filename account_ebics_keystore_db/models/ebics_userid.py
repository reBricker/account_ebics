# Copyright 2026 reBricker.
# License LGPL-3 or later (https://www.gnu.org/licenses/lgpl).

import os

from odoo import api, fields, models
from odoo.tools.binary import BinaryBytes


class EbicsUserID(models.Model):
    """Keep the EBICS key file of every user id in the database as well.

    account_ebics stores the (passphrase encrypted) key file on the local file
    system.  On container platforms that file system does not survive a restart
    or a redeploy.  This extension mirrors the key file into the database: it is
    saved after every operation that may touch the keys and written back to disk
    whenever the file is missing, so a freshly started container finds its keys
    again without any manual step.
    """

    _inherit = "ebics.userid"

    ebics_keys_data = fields.Binary(
        string="EBICS Keys (database copy)",
        attachment=False,
        copy=False,
        help="Passphrase encrypted key file as written by the fintech library. "
        "Restored to the EBICS keys directory when the file is missing there.",
    )
    ebics_keys_stored = fields.Boolean(
        compute="_compute_ebics_keys_stored", string="Keys in database"
    )

    @api.depends("ebics_keys_data")
    def _compute_ebics_keys_stored(self):
        for rec in self:
            rec.ebics_keys_stored = bool(rec.ebics_keys_data)

    @api.depends("name", "ebics_config_id.ebics_keys", "ebics_keys_data")
    def _compute_ebics_keys_fn(self):
        # Every access to the key file name goes through this compute, so the
        # file is restored before any code looks for it on disk.
        super()._compute_ebics_keys_fn()
        self._keystore_restore()

    def _keystore_restore(self):
        """Write the database copy to disk when the key file is missing."""
        for rec in self:
            fn = rec.ebics_keys_fn
            if not fn or not rec.ebics_keys_data or os.path.isfile(fn):
                continue
            os.makedirs(os.path.dirname(fn), mode=0o700, exist_ok=True)
            with open(fn, "wb") as f:
                f.write(rec.ebics_keys_data.content)
            os.chmod(fn, 0o600)

    def _keystore_save(self):
        """Copy the key file from disk into the database when it changed."""
        for rec in self:
            fn = rec.ebics_keys_fn
            if not fn or not os.path.isfile(fn):
                continue
            with open(fn, "rb") as f:
                data = f.read()
            stored = rec.ebics_keys_data.content if rec.ebics_keys_data else b""
            if data != stored:
                rec.sudo().write({"ebics_keys_data": BinaryBytes(data)})

    # Operations of account_ebics that create or change the key file.

    def ebics_init_1(self):
        try:
            return super().ebics_init_1()
        finally:
            self._keystore_save()

    def ebics_init_2(self):
        try:
            return super().ebics_init_2()
        finally:
            self._keystore_save()

    def ebics_init_3(self):
        try:
            return super().ebics_init_3()
        finally:
            self._keystore_save()

    def ebics_init_4(self):
        try:
            return super().ebics_init_4()
        finally:
            self._keystore_save()
