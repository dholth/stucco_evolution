import ponzi_evolution

def test_evolve():
    import sqlalchemy
    import sqlalchemy.orm
    import ponzi_evolution
    engine = sqlalchemy.create_engine('sqlite:///test.db', echo=True)
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    ponzi_evolution.initialize(session)
    ponzi_evolution.upgrade(session)
    session.commit()
    ponzi_evolution.PONZI_EVOLUTION_SCHEMA_VERSION = 1
    ponzi_evolution.upgrade(session)
    session.commit()
