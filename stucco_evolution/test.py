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

    stucco_evolution.initialize(session)

    session.flush()

    session.execute("UPDATE stucco_evolution SET version = 1 WHERE package = 'stucco_evolution'")

    stucco_evolution.upgrade_many(
              stucco_evolution.managers(session,
                  stucco_evolution.dependencies('stucco_evolution'))
              )
    
    session.commit()

    rows = session.execute("SELECT COUNT(*) FROM stucco_evolution").scalar()
    assert rows == 3, rows

def test_initialize():
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    assert stucco_evolution.is_initialized(session) is False
    stucco_evolution.initialize(session)
    assert stucco_evolution.is_initialized(session)

def test_unversioned():
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    stucco_evolution.initialize(session)
    manager = stucco_evolution.SQLAlchemyEvolutionManager(session, 'testing_testing', 4)
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
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    dependencies = dependencies('stucco_openid')
    managers = managers(session, dependencies)
    assert len(managers) == 3
    create_many(managers)
    upgrade_many(managers)
    create_or_upgrade_packages(session, 'stucco_openid')

def test_create_or_upgrade_many():
    """The recommended schema management strategy."""
    from stucco_evolution import dependencies, managers
    from stucco_evolution import create_or_upgrade_many
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    dependencies = dependencies('stucco_openid')
    managers = managers(session, dependencies)
    stucco_evolution.initialize(session)
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
