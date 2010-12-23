from pkg_resources import EntryPoint
from zope.interface import implements
from zope.interface import Interface

import repoze.evolution
from repoze.evolution import IEvolutionManager

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from stucco_evolution.evolve import NAME, VERSION

Base = declarative_base()

class SchemaVersion(Base):
    __tablename__ = 'stucco_evolution'
    package = Column(String(30), primary_key=True)
    version = Column(Integer)

    def __repr__(self):
        return "<%s%r>" % (self.__class__.__name__, 
                           (self.package, self.version))

class SQLAlchemyEvolutionManager(object):
    implements(IEvolutionManager)
    def __init__(self, session, evolve_packagename,
                 sw_version, initial_db_version=None,
                 packagename=None):
        """ Initialize a SQLAlchemy evolution manager.
        
        :param session: is a SQLAlchemy ORM session that will be passed
        in to each evolution step.

        :param evolve_packagename: is the Python dotted package name of
        a package which contains evolution scripts.

        :param packagename: is the name used in the table used to track
        schema versions or ``evolve_packagename`` if not provided.

        :param sw_version: is the current software version of the software
        represented by this manager.

        :param initial_db_version`` indicates the presumed version of
        a database which doesn't already have a version set.  If not
        supplied or is set to ``None``, the evolution manager will not
        attempt to construe the version of a an unversioned db.
        """
        self.session = session
        self.evolve_packagename = evolve_packagename
        self.packagename = packagename or evolve_packagename
        self.sw_version = sw_version
        self.initial_db_version = initial_db_version

    def get_sw_version(self):
        return self.sw_version

    def get_db_version(self):
        query = self.session.query(SchemaVersion)
        db_version = query.filter_by(package=self.packagename).first()
        if db_version is None:
            return self.initial_db_version
        return db_version.version

    def evolve_to(self, version):
        scriptname = '%s.evolve%s' % (self.evolve_packagename, version)
        evmodule = EntryPoint.parse('x=%s' % scriptname).load(False)
        evmodule.evolve(self.session)
        self.set_db_version(version)
        
    def create(self):
        scriptname = '%s.create' % (self.evolve_packagename)
        crmodule = EntryPoint.parse('x=%s' % scriptname).load(False)
        crmodule.create(self.session)
        if self.get_db_version() is None:
            self.set_db_version(self.sw_version)

    def set_db_version(self, version):
        db_version = self.session.query(SchemaVersion).get(self.packagename)
        if db_version is None:
            db_version = SchemaVersion(package=self.packagename)
        db_version.version = version
        self.session.add(db_version)

    def __repr__(self):
        return "<%s%r>" % (self.__class__.__name__, 
                           (self.packagename, self.sw_version))

def find_dependencies(packagename):
    """Return list of database dependencies for packagename in topological order."""
    visited = set()
    dependencies = []
    def find_dependencies_inner(pkgname): # XXX detect cycles.
        if not pkgname in visited:
            mod = EntryPoint.parse('x=%s.evolve' % pkgname).load(False)
            visited.add(pkgname)
            for p in mod.DEPENDS:
                find_dependencies_inner(p)
            dependencies.append((pkgname, mod))
    find_dependencies_inner(packagename)
    return dependencies

def build_managers(session, dependencies):
    """Generate SQLAlchemyEvolutionManager instances given a session
    and a list of (packagename, module) tuples as returned by 
    find_dependencies."""
    managers = []
    for packagename, mod in dependencies:
        managers.append(SQLAlchemyEvolutionManager(
                session,
                evolve_packagename='%s.evolve' % packagename,
                packagename=packagename,
                sw_version=mod.VERSION
                ))
    return managers

def create_many(managers):
    """Call manager.create() on a list of managers.
    Caller is responsible for transaction management."""
    for manager in managers:
        manager.create()

def upgrade_many(managers):
    """Call repoze.evolution.evolve_to_latest(manager) on a list of managers.
    Caller is responsible for transaction management."""
    for manager in managers:
        repoze.evolution.evolve_to_latest(manager)

# XXX deprecated
def initialize(session):
    """Initialize tables for stucco_evolution itself."""
    create_many(build_managers(session, find_dependencies('stucco_evolution')))

# XXX deprecated
def upgrade(session):
    """Upgrade stucco_evolution's schema to the latest version."""
    upgrade_many(build_managers(session, find_dependencies('stucco_evolution')))
    