# Copyright 2026 reBricker.
# License LGPL-3 or later (https://www.gnu.org/licenses/lgpl).

import os
import tempfile

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestKeystore(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.keys_dir = tempfile.mkdtemp(prefix="ebics_keys_")
        journal = cls.env["account.journal"].search([("type", "=", "bank")], limit=1)
        if not journal:
            journal = cls.env["account.journal"].create(
                {"name": "Test Bank", "type": "bank", "code": "TBNK"}
            )
        cls.config = cls.env["ebics.config"].create(
            {
                "name": "Keystore test bank",
                "ebics_host": "TESTHOST",
                "ebics_url": "https://ebics.example.invalid/ebicsweb/ebicsweb",
                "ebics_partner": "PARTNER1",
                "ebics_version": "H005",
                "ebics_keys": cls.keys_dir,
                "journal_ids": [(6, 0, journal.ids)],
            }
        )
        cls.userid = cls.env["ebics.userid"].create(
            {
                "name": "USER1",
                "ebics_config_id": cls.config.id,
                "signature_class": "T",
            }
        )

    def test_save_and_restore(self):
        fn = self.userid.ebics_keys_fn
        self.assertTrue(fn.startswith(self.keys_dir))
        self.assertFalse(self.userid.ebics_keys_stored)
        payload = b"encrypted key material"
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        with open(fn, "wb") as f:
            f.write(payload)
        self.userid._keystore_save()
        self.assertTrue(self.userid.ebics_keys_stored)
        self.assertEqual(self.userid.ebics_keys_data.content, payload)

        # Simulate a fresh container: the file is gone, the database copy restores it.
        os.remove(fn)
        self.userid.invalidate_recordset(["ebics_keys_fn", "ebics_keys_found"])
        self.assertEqual(self.userid.ebics_keys_fn, fn)
        self.assertTrue(os.path.isfile(fn))
        with open(fn, "rb") as f:
            self.assertEqual(f.read(), payload)
        self.assertTrue(self.userid.ebics_keys_found)
        self.assertEqual(oct(os.stat(fn).st_mode & 0o777), oct(0o600))

    def test_unchanged_file_is_not_rewritten(self):
        fn = self.userid.ebics_keys_fn
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        with open(fn, "wb") as f:
            f.write(b"v1")
        self.userid._keystore_save()
        write_date = self.userid.write_date
        self.userid._keystore_save()
        self.assertEqual(self.userid.write_date, write_date)
