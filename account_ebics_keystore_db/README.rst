.. image:: https://img.shields.io/badge/license-LGPL--3-blue.png
   :target: https://www.gnu.org/licenses/lgpl
   :alt: License: LGPL-3

==================================
EBICS keys stored in the database
==================================

``account_ebics`` keeps the passphrase encrypted key file of every EBICS user id
on the local file system of the Odoo server. On container platforms
(Kubernetes, Docker) that file system is usually ephemeral: a restart or a
redeploy would lose the keys and the EBICS user would have to be initialised
again with the bank.

This module keeps a copy of the key file in the database:

- after every operation that creates or changes the keys (initialisation,
  bank key download, passphrase change, transfers) the file is copied into the
  ``ebics.userid`` record,
- whenever the file is missing on disk it is written back from the database
  before it is used.

The copy is the file as written by the fintech library, i.e. still protected by
the user's passphrase. The EBICS keys directory of the configuration is created
when it is missing (e.g. an empty volume after a restart).

Passphrase from the environment
===============================

With the key file in the database, a passphrase stored next to it would make a
database backup sufficient to use the keys. The passphrase of an EBICS user id
can therefore be provided as environment variable of the Odoo server instead::

    EBICS_PASSPHRASE_<USERID>

``<USERID>`` is the EBICS UserID in upper case, every character other than
``A-Z`` and ``0-9`` replaced by ``_``. On Kubernetes the variable typically
comes from a secret. When it is set:

- the passphrase field is hidden on the user id form and cannot be set there,
- initialisation, bank key download and transfers (including the batch
  download) use the value from the environment,
- the value is never written to the database nor sent to the web client.

Leave "Store EBICS Passphrase" checked so that automated downloads pick the
user id. Changing the passphrase of such a user id with the wizard is not
supported; generate new keys instead.

Passphrases entered in the form are kept in the field ``ebics_passphrase_db``
(migrated from the former ``ebics_passphrase`` column).
