from pkg_resources import EntryPoint
from zope.interface import implements
from zope.interface import Interface

import repoze.evolution
from repoze.evolution import IEvolutionManager

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import logging
log = logging.getLogger(__name__)

Base = declarative_base()

class CircularDependencyError(Exception):
    def __init__(self, packagenames):
        self.packagenames = packagenames
        self.message = "Circular dependency between evolution modules:"
    
    def __str__(self):
        return "%s %r" % (self.message, self.packagenames)

class SchemaVersion(Base):
    __tablename__ = 'stucco_evolution'
    package = Column(String(30), primary_key=True)
    version = Column(Integer)

    def __repr__(self):
        return "<%s%r>" % (self.__class__.__name__, 
                           (self.package, self.version))

class SQLAlchemyEvolutionManager(object):
    implements(IEvolutionManager)
    def __init__(self, connection, evolve_packagename,
                 sw_version, packagename=None):
        """Initialize a SQLAlchemy evolution manager.
        
        :param connection: is a SQLAlchemy ORM connection that will be passed
        in to each evolution step.

        :param evolve_packagename: is the Python dotted package name of
        a package which contains evolution scripts.

        :param packagename: is the name used in the table used to track
        schema versions or ``evolve_packagename`` if not provided.

        :param sw_version: is the current software version of the software
        represented by this manager.
        """
        self.connection = connection
        self.evolve_packagename = evolve_packagename
        self.packagename = packagename or evolve_packagename
        self.sw_version = sw_version
        self._session = sessionmaker(bind=self.connection)()

    def get_sw_version(self):
        return self.sw_version

    def get_db_version(self):
        query = self._session.query(SchemaVersion)
        db_version = query.filter_by(package=self.packagename).first()
        if db_version is None: return None
        return db_version.version

    def evolve_to(self, version):
        """Run single evolve script with our connection. Record version.
        
        :param version: N of evolveN.py to run
        """
        scriptname = '%s.evolve%s' % (self.evolve_packagename, version)
        log.info("Run evolve script %s", scriptname)
        evmodule = EntryPoint.parse('x=%s' % scriptname).load(False)
        evmodule.evolve(self.connection)
        self.set_db_version(version)
        
    def create(self):
        """Run create.py to create latest schema version. Record version."""
        scriptname = '%s.create' % (self.evolve_packagename)
        log.info("Run create script %s", scriptname)
        crmodule = EntryPoint.parse('x=%s' % scriptname).load(False)
        crmodule.create(self.connection)
        if self.get_db_version() is None:
            self.set_db_version(self.sw_version)

    def set_db_version(self, version):
        session = self._session
        db_version = session.query(SchemaVersion).get(self.packagename)
        if db_version is None:
            db_version = SchemaVersion(package=self.packagename)
        db_version.version = version
        session.add(db_version)
        session.flush()

    def __repr__(self):
        return "<%s%r>" % (self.__class__.__name__, 
                           (self.packagename, self.sw_version))

def dependencies(packagename):
    """Return list of evolution modules for packagename and its dependencies
    in topological order. Raise CircularDependencyError in case of circular
    dependencies."""
    visited = set()
    dependencies = []
    stack = []
    def find_dependencies_inner(pkgname):
        stack.append(pkgname)
        log.debug("%r %r", pkgname, stack)
        if pkgname in stack[:-1]:
            raise CircularDependencyError(stack)
        if not pkgname in visited:
            mod = EntryPoint.parse('x=%s.evolve' % pkgname).load(False)
            visited.add(pkgname)
            for p in mod.DEPENDS:
                find_dependencies_inner(p)
            dependencies.append(mod)
        stack.pop()
    find_dependencies_inner(packagename)
    return dependencies

def manager(connection, package_or_name):
    """Build one SQLAlchemyEvolutionManager for connection and 
    'import package_or_name.evolve' if package_or_name is a string, 
    else build SQLAlchemyEvolutionManager for module package_or_name."""
    if isinstance(package_or_name, basestring):
        evmodule = EntryPoint.parse('x=%s.evolve' % package_or_name).load(False)
    else:
        evmodule = package_or_name
    # Naming mischief is reserved for future expansion:
    assert evmodule.__name__ == evmodule.NAME + '.evolve', \
        'evolution module __name__ %r must start with NAME %r' \
        ' and end with ".evolve"' % (
            evmodule.__name__, evmodule.NAME)
    manager = SQLAlchemyEvolutionManager(
                connection,
                evolve_packagename=evmodule.__name__,
                packagename=evmodule.NAME,
                sw_version=evmodule.VERSION
                )
    return manager

def managers(connection, dependencies):
    """Return a list of SQLAlchemyEvolutionManager instances given a connection
    and a list of evolution modules as returned by dependencies()."""
    built = []
    for evmodule in dependencies:
        built.append(manager(connection, evmodule))
    return built

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

def create_or_upgrade_many(managers):
    """For each manager in managers, if manager.get_db_version() is None,
    call manager.create(). Else call repoze.evolution.evolve_to_latest(manager).
    With this strategy, evolveN.py (not create.py) is responsible for
    creating any new tables introduced in that version.
    """
    for manager in managers:
        if manager.get_db_version() is None:
            manager.create()
        else:
            repoze.evolution.evolve_to_latest(manager)

def create_or_upgrade_packages(connection, packagename):
    """Create or upgrade schema for `packagename` and its dependencies,
    using SQLAlchemy `connection`. Caller must commit transaction.
    Recommended.
    
    Calls::

        create_or_upgrade_many(managers(connection, dependencies(packagename)))

    """
    create_or_upgrade_many(managers(connection, dependencies(packagename)))

def initialize(connection):
    """Create tables for stucco_evolution itself (if they do not exist)."""
    if not is_initialized(connection):
        manager(connection, 'stucco_evolution').create()

def is_initialized(connection):
    """Is stucco_evolution ready to go for connection?
    If not, call initialize(connection)"""
    return connection.dialect.has_table(connection, SchemaVersion.__tablename__)

