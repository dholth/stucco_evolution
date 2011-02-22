def evolve(connection):
    """Migrate any rows from old ponzi_evolution table."""
    connection.execute("INSERT INTO stucco_evolution (package, version) "
        "SELECT package, version FROM ponzi_evolution")
