import stucco_evolution
import sqlalchemy
import sqlalchemy.orm

def test_evolve_compat():
    """Ensure we bring over any rows from the old table name 'ponzi_evolution'"""
    engine = sqlalchemy.create_engine('sqlite:///:memory:', echo=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    session.execute("CREATE TABLE ponzi_evolution (package STRING, version INTEGER)")
    session.execute("INSERT INTO ponzi_evolution (package, version) VALUES ('ponzi_evolution', 1)")
    session.execute("INSERT INTO ponzi_evolution (package, version) VALUES ('third_party', 2)")

    stucco_evolution.initialize(session)
    stucco_evolution.upgrade(session)
    session.commit()

    assert session.execute("SELECT COUNT(*) FROM stucco_evolution").scalar() == 3

def test_unversioned():
    engine = sqlalchemy.create_engine('sqlite:///:memory:', echo=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    stucco_evolution.initialize(session)
    manager = stucco_evolution.SQLAlchemyEvolutionManager(session, 'testing_testing', 4)
    assert manager.get_db_version() is None
    assert manager.get_sw_version() is 4
    assert isinstance(repr(manager), basestring)
