from pkg_resources import EntryPoint
from zope.interface import implements
from zope.interface import Interface

from repoze.evolution import IEvolutionManager

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

PONZI_EVOLUTION_SCHEMA_VERSION = 0

class SchemaVersion(Base):
    __tablename__ = 'ponzi_evolution'
    package = Column(String(30), primary_key=True)
    version = Column(Integer)

class SQLAlchemyEvolutionManager(object):
    implements(IEvolutionManager)
    def __init__(self, session, evolve_packagename,
                 sw_version, initial_db_version=None,
                 packagename=None):
        """ Initialize a SQLAlchemy evolution manager.  ``session``
        is a SQLAlchemy ORM session that will be passed in to each
        evolution step.  ``evolve_packagename`` is the Python dotted
        package name of a package which contains evolution scripts.
        ``packagename`` is the name used in the table used to track schema
        versions or ``evolve_packagename`` if not provided. ``sw_version``
        is the current software version of the software represented by
        this manager.  ``initial_db_version`` indicates the presumed
        version of a database which doesn't already have a version set.
        If not supplied or is set to ``None``, the evolution manager will
        not attempt to construe the version of a an unversioned db."""
        self.session = session
        self.evolve_packagename = evolve_packagename
        self.packagename = packagename or evolve_packagename
        self.sw_version = sw_version
        self.initial_db_version = initial_db_version

    def get_sw_version(self):
        return self.sw_version

    def get_db_version(self):
        query = self.session.query(SchemaVersion)
        db_version = query.get(self.packagename)
        if db_version is None:
            return self.initial_db_version
        return db_version.version

    def evolve_to(self, version):
        scriptname = '%s.evolve%s' % (self.evolve_packagename, version)
        evmodule = EntryPoint.parse('x=%s' % scriptname).load(False)
        evmodule.evolve(self.session)
        self.set_db_version(version)
        self.session.commit()

    def set_db_version(self, version):
        db_version = self.session.query(SchemaVersion).get(self.packagename)
        if db_version is None:
            db_version = SchemaVersion(package=self.packagename)
        db_version.version = version
        self.session.add(db_version)

def initialize(session):
    """Initialize tables for this package and upgrade to latest schema."""
    Base.metadata.create_all(session.bind)
    manager = SQLAlchemyEvolutionManager(session, 'ponzi_evolution.evolve',
            PONZI_EVOLUTION_SCHEMA_VERSION,
            packagename='ponzi_evolution')
    if manager.get_db_version() is None:
        manager.set_db_version(PONZI_EVOLUTION_SCHEMA_VERSION)

def upgrade(session):
    """Upgrade this package's schema to the latest version."""
    import repoze.evolution
    manager = SQLAlchemyEvolutionManager(session, 'ponzi_evolution.evolve',
            PONZI_EVOLUTION_SCHEMA_VERSION,
            packagename='ponzi_evolution')
    repoze.evolution.evolve_to_latest(manager)

