# Copyright 2026 reBricker.
# License LGPL-3 or later (https://www.gnu.org/licenses/lgpl).

import os
import re

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.binary import BinaryBytes

PASSPHRASE_ENV_PREFIX = "EBICS_PASSPHRASE_"


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
    # The passphrase is no longer a plain stored field: the value entered in the
    # form lives in ebics_passphrase_db, and a passphrase provided through the
    # environment (EBICS_PASSPHRASE_<USERID>) is only handed out on the server
    # side, inside the EBICS operations. It never reaches the database, its
    # backups or the web client.
    ebics_passphrase = fields.Char(
        compute="_compute_ebics_passphrase",
        inverse="_inverse_ebics_passphrase",
        store=False,
    )
    ebics_passphrase_db = fields.Char(
        string="EBICS Passphrase (database)",
        copy=False,
    )
    ebics_passphrase_env = fields.Boolean(
        compute="_compute_ebics_passphrase_env",
        string="Passphrase from environment",
        help="The passphrase is read from the environment variable "
        "EBICS_PASSPHRASE_<USERID> of the Odoo server and is not stored.",
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

    def _ebics_passphrase_env_name(self):
        self.ensure_one()
        return PASSPHRASE_ENV_PREFIX + re.sub(r"[^A-Z0-9]", "_", (self.name or "").upper())

    def _ebics_env_passphrase(self):
        self.ensure_one()
        if not self.name:
            return False
        return os.environ.get(self._ebics_passphrase_env_name()) or False

    @api.depends("name")
    def _compute_ebics_passphrase_env(self):
        for rec in self:
            rec.ebics_passphrase_env = bool(rec._ebics_env_passphrase())

    @api.depends("name", "ebics_passphrase_db")
    @api.depends_context("ebics_env_passphrase")
    def _compute_ebics_passphrase(self):
        use_env = self.env.context.get("ebics_env_passphrase")
        for rec in self:
            env_passphrase = use_env and rec._ebics_env_passphrase()
            rec.ebics_passphrase = env_passphrase or rec.ebics_passphrase_db

    def _inverse_ebics_passphrase(self):
        for rec in self:
            if rec.ebics_passphrase and rec._ebics_env_passphrase():
                raise UserError(
                    self.env._(
                        "The passphrase of EBICS UserID %(user)s is provided by the "
                        "environment variable %(var)s and cannot be set here.",
                        user=rec.name,
                        var=rec._ebics_passphrase_env_name(),
                    )
                )
            rec.ebics_passphrase_db = rec.ebics_passphrase

    @api.depends("state", "ebics_passphrase", "ebics_keys_found", "ebics_passphrase_env")
    def _compute_ebics_passphrase_view_modifiers(self):
        super()._compute_ebics_passphrase_view_modifiers()
        for rec in self.filtered("ebics_passphrase_env"):
            rec.ebics_passphrase_required = False
            rec.ebics_passphrase_invisible = True
            rec.ebics_passphrase_store_readonly = True

    def _with_env_passphrase(self):
        return self.with_context(ebics_env_passphrase=True)

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
            return super(EbicsUserID, self._with_env_passphrase()).ebics_init_1()
        finally:
            self._keystore_save()

    def ebics_init_2(self):
        try:
            return super(EbicsUserID, self._with_env_passphrase()).ebics_init_2()
        finally:
            self._keystore_save()

    def ebics_init_3(self):
        try:
            return super(EbicsUserID, self._with_env_passphrase()).ebics_init_3()
        finally:
            self._keystore_save()

    def ebics_init_4(self):
        try:
            return super(EbicsUserID, self._with_env_passphrase()).ebics_init_4()
        finally:
            self._keystore_save()
