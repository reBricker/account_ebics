# Copyright 2026 reBricker.
# License LGPL-3 or later (https://www.gnu.org/licenses/lgpl).


def migrate(cr, version):
    # ebics_passphrase is no longer stored: move existing values to
    # ebics_passphrase_db and clear the old column.
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ebics_userid' AND column_name = 'ebics_passphrase'
        """
    )
    if not cr.fetchone():
        return
    cr.execute(
        """
        UPDATE ebics_userid
           SET ebics_passphrase_db = ebics_passphrase
         WHERE ebics_passphrase IS NOT NULL AND ebics_passphrase_db IS NULL
        """
    )
    cr.execute("UPDATE ebics_userid SET ebics_passphrase = NULL")
