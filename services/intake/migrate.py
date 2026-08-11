"""
One-off migration runner: applies Alembic migrations against RDS from
inside the VPC via Lambda, since RDS is not publicly accessible and
neither your local machine nor anything outside the VPC can reach it
directly. Invoke manually once; not wired to any trigger.
"""

import os

from alembic.config import Config
from alembic import command


def lambda_handler(event, context):
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("script_location", "alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
    command.upgrade(alembic_cfg, "head")
    return {"status": "migrated"}