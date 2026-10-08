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
the user's passphrase. No further configuration is needed; the EBICS keys
directory of the configuration must simply exist (it may be an empty volume).
