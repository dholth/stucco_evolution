import stucco_evolution
import sqlalchemy
import sqlalchemy.orm

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

    # XXX Hack to test upgrading. Should provide a standard 'get evolution
    # manager for package' mechanism.
    session.execute("UPDATE stucco_evolution SET version = 1 WHERE package = 'stucco_evolution'")

    stucco_evolution.upgrade(session)
    session.commit()

    rows = session.execute("SELECT COUNT(*) FROM stucco_evolution").scalar()
    assert rows == 3, rows

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

