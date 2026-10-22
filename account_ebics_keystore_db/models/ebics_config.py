# Copyright 2026 reBricker.
# License LGPL-3 or later (https://www.gnu.org/licenses/lgpl).

import os

from odoo import models


class EbicsConfig(models.Model):
    _inherit = "ebics.config"

    def _check_ebics_keys(self):
        # In a container the keys directory is gone after every restart, and
        # before the first key generation there is no database copy whose
        # restore would create it.
        for cfg in self:
            if cfg.ebics_keys:
                os.makedirs(cfg.ebics_keys, mode=0o700, exist_ok=True)
        return super()._check_ebics_keys()
