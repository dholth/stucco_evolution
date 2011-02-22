def create(connection):
    """Create the latest version of the schema. This function should be
    idempotent."""
    import stucco_evolution
    stucco_evolution.Base.metadata.create_all(connection)
    
