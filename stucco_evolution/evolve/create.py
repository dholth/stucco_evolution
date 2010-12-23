def create(session):
    import stucco_evolution
    stucco_evolution.Base.metadata.create_all(session.bind)