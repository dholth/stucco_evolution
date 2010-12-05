ponzi_evolution
---------------

SQLAlchemy manager for repoze.evolution. Provides a simple way to
implement schema migrations as a directory of numbered Python scripts.

``ponzi_evolution`` keeps a table with (packagename, version) tuples and
will pass a SQLAlchemy session to numbered evolveN.py scripts to bring
the schema for ``packagename`` up-to-date. All you have to do is write
the Python and SQL needed to make that happen.
