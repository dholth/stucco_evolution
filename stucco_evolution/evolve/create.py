def create(session):
    """Create the latest version of the schema. This function should be
    idempotent."""
    import stucco_evolution
    stucco_evolution.Base.metadata.create_all(session.bind)
    