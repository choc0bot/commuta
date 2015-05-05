from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
commutra = Table('commutra', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('token', String(length=64)),
    Column('commute_tag', Integer),
    Column('commute_string', String(length=128)),
    Column('goal_name', String(length=128)),
    Column('goal_value', Integer),
    Column('goal_savings', Integer),
    Column('carbon_number', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['commutra'].columns['carbon_number'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['commutra'].columns['carbon_number'].drop()
