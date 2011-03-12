def create(connection):
    """Create the latest version of the schema. This function should be
    idempotent and can be usefully called more than once per database
    for development, but stucco_evolution tries to call this only once
    in production."""
    # import yourproject
    # yourproject.Base.metadata.create_all(connection)
    # or
    # connection.execute("CREATE TABLE ...")
