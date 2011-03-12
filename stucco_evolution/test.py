import stucco_evolution
import sqlalchemy.orm
from nose.tools import raises
import sys

def test_evolve_compat():
    """Ensure we bring over any rows from the old table name 'ponzi_evolution'"""
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    session.execute("CREATE TABLE ponzi_evolution (package STRING, version INTEGER)")
    session.execute("INSERT INTO ponzi_evolution (package, version) VALUES ('ponzi_evolution', 1)")
    session.execute("INSERT INTO ponzi_evolution (package, version) VALUES ('third_party', 2)")

    stucco_evolution.initialize(session.connection())

    session.flush()

    session.execute("UPDATE stucco_evolution SET version = 1 WHERE package = 'stucco_evolution'")

    stucco_evolution.upgrade_many(
              stucco_evolution.managers(session.connection(),
                  stucco_evolution.dependencies('stucco_evolution'))
              )
    
    session.commit()

    rows = session.execute("SELECT COUNT(*) FROM stucco_evolution").scalar()
    assert rows == 3, rows

def test_initialize():
    import stucco_evolution.evolve
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    connection = engine.connect()
    assert stucco_evolution.is_initialized(connection) is False
    stucco_evolution.initialize(connection)
    assert stucco_evolution.is_initialized(connection)
    db_version = stucco_evolution.manager(connection, 'stucco_evolution').get_db_version()
    assert db_version == stucco_evolution.evolve.VERSION

def test_unversioned():
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    stucco_evolution.initialize(session.connection())
    manager = stucco_evolution.SQLAlchemyEvolutionManager(session.connection(), 
                                                          'testing_testing', 4)
    assert manager.get_db_version() is None
    assert manager.get_sw_version() is 4
    assert isinstance(repr(manager), basestring)

def test_repr():
    r = repr(stucco_evolution.SchemaVersion(package='foo', version='4'))
    assert 'SchemaVersion' in r
    assert 'foo' in r
    assert '4' in r

def test_create_many():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    from stucco_evolution import dependencies, managers
    from stucco_evolution import create_many, upgrade_many
    from stucco_evolution import create_or_upgrade_packages
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    connection = engine.connect()
    Session = sqlalchemy.orm.sessionmaker()
    session = Session(bind=connection)
    dependencies = dependencies('stucco_openid')
    managers = managers(connection, dependencies)
    assert len(managers) == 3
    create_many(managers)
    upgrade_many(managers)
    create_or_upgrade_packages(connection, 'stucco_openid')

    connection.close()

def test_create_or_upgrade_many():
    """The recommended schema management strategy."""
    from stucco_evolution import dependencies, managers
    from stucco_evolution import create_or_upgrade_many
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    connection = engine.connect()
    dependencies = dependencies('stucco_openid')
    managers = managers(connection, dependencies)
    stucco_evolution.initialize(connection)
    create_or_upgrade_many(managers)
    
def test_naming_mischief():
    """evolution module NAME+'.evolve' must match __name__ (for now)"""
    class Module(object): pass # mock
    
    m1 = Module()
    m1.NAME = 'stucco_evolution'
    m1.VERSION = 4
    m1.__name__ = 'stucco_evolution.evolve'
    
    stucco_evolution.manager(None, m1)
    
    m2 = Module()
    m2.NAME = 'Larry Henderson'
    m2.VERSION = 4
    m2.__name__ = 'stucco_evolution.evolve'
    
    @raises(AssertionError)
    def naming_mischief():
        stucco_evolution.manager(None, m2)
    naming_mischief()

def test_circdep_exception():
    c = stucco_evolution.CircularDependencyError(['zero', 'one', 'two', 'one'])
    assert len(str(c))

@raises(stucco_evolution.CircularDependencyError)
def test_circdep():
    class Module(object): pass # mock
    m1 = Module()
    m1.NAME = 'stucco_evolution_test1'
    m1.DEPENDS = ['stucco_evolution_test2', 'stucco_evolution']
    m1.VERSION = 0
    m2 = Module()
    m2.NAME = 'stucco_evolution_test2'
    m2.DEPENDS = ['stucco_evolution', 'stucco_evolution_test1']
    m2.VERSION = 0
    sys.modules['stucco_evolution_test1'] = Module()
    sys.modules['stucco_evolution_test2'] = Module()
    sys.modules['stucco_evolution_test1.evolve'] = m1
    sys.modules['stucco_evolution_test2.evolve'] = m2

    stucco_evolution.dependencies('stucco_evolution_test1')

def test_manager_from_name():
    assert stucco_evolution.manager(None, 'stucco_evolution') is not None

def test_transactional_ddl():
    """Test transaction ddl. Requires a patched sqlite3 module."""
    from sqlalchemy import Column, Integer
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    class BoringTable(Base):
        __tablename__ = "boring"
        id = Column(Integer, primary_key=True)

    class TestException(Exception): pass

    class TestEvolutionManager(stucco_evolution.SQLAlchemyEvolutionManager):
        def create(self):
            Base.metadata.create_all(self.connection)

        def evolve_to(self, version):
            self.connection.execute("INSERT INTO boring (id) VALUES (1)")
            raise TestException("It wasn't meant to be.")

    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    connection = engine.connect()

    trans = connection.begin()

    stucco_evolution.initialize(connection)
    managers = [TestEvolutionManager(connection, 'test', 0)]
    stucco_evolution.create_or_upgrade_many(managers)

    managers[0].sw_version=1

    @raises(TestException)
    def go():
        try:
            managers[0].evolve_to(1)
        except:
            trans.rollback()
            raise

    go()

    assert not engine.has_table('boring')

    connection.close()

def test_transactional_ddl_2():
    """Test transaction ddl (2). Requires a patched sqlite3 module."""
    import logging
    log = logging.getLogger(__name__)
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    connection = engine.connect()
    log.debug("Isolation level: %s", 
              connection.connection.connection.isolation_level)
    trans = connection.begin()
    connection.execute("CREATE TABLE foo (bar INTEGER)")
    tables = connection.execute('PRAGMA table_info("foo")').fetchall()
    log.debug(tables)
    assert tables, tables
    trans.rollback()
    assert not engine.has_table('foo')

    connection.close()
