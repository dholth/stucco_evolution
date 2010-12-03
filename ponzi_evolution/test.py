import ponzi_evolution
import sqlalchemy
import sqlalchemy.orm

def test_evolve():
    engine = sqlalchemy.create_engine('sqlite:///:memory:', echo=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    ponzi_evolution.initialize(session)
    ponzi_evolution.upgrade(session)
    session.commit()
    ponzi_evolution.PONZI_EVOLUTION_SCHEMA_VERSION = 1
    ponzi_evolution.upgrade(session)
    session.commit()

def test_unversioned():
    engine = sqlalchemy.create_engine('sqlite:///:memory:', echo=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    ponzi_evolution.initialize(session)
    manager = ponzi_evolution.SQLAlchemyEvolutionManager(session, 'testing_testing', 4)
    assert manager.get_db_version() is None

