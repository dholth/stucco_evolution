def evolve(session):
    """Migrate any rows from old ponzi_evolution table."""
    session.execute("INSERT INTO stucco_evolution (package, version) "
        "SELECT package, version FROM ponzi_evolution")
