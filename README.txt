stucco_evolution
================

Demo
----

    import sqlalchemy
    import stucco_evolution

    engine = sqlalchemy.create_engine(...)

    with engine.begin() as connection:
        stucco_evolution.initialize(connection)
        stucco_evolution.create_or_upgrade_packages(connection, 'mypackage')

stucco_evolution creates or upgrades the database schema for itself,
'mypackage', and the dependencies of 'mypackage', in a transaction, in 
the correct, topologically-sorted order.

Summary
-------

stucco_evolution extends repoze.evolution for SQLAlchemy. It provides a
simple way to implement schema migrations within a single package as a
collection of numbered Python scripts, and it provides a way for packages
to depend on each other's schema as a directed acyclic graph, creating
and upgrading each schema's tables in topological dependency order.

stucco_evolution passes a SQLAlchemy connection to a package of numbered
scripts in order, remembers the versions of installed schema, and sorts
a collection of `evolve` packages by dependency order. It delegates
writing the actual `ALTER TABLE` statements to another library or your
brain. It delegates schema downgrades to a proper database backup.

stucco_evolution was written as support code for a web application, then
extracted from that code, extended, and published. It is now intendend to
manage the database schema for itself and other stucco_* packages to be
released someday. I hope you will find it useful for your own packages,
too. However, this software is provided "as is" and without any express or
implied warranties, including, without limitation, the implied warranties
of merchantibility and fitness for a particular purpose.

Usage
-----

If your package is called `mypackage`, you can add an evolution module
which must be called `evolve`. This module will contain scripts to
create and migrate your schema from one version to the next::

	cd mypackage
	mkdir evolve
	touch evolve/__init__.py

`evolve/__init__.py` must contain three constants::

	NAME = 'mypackage' # stucco_evolution imports 'mypackage' + '.evolve'
	VERSION = 0
	DEPENDS = []

`evolve/create.py` should always create the most current `VERSION` of your schema. It should be idempotent::

	def create(connection):
	    import mypackage.models
	    mypackage.models.Base.metadata.create_all(connection)

(If you have Paste Script installed you can type `paster create
-t stucco_evolution [mypackage]` to create an evolution module in
[mypackage]/evolve. Since Paste Script's package name substitution is
not perfect, check mypackage/evolve/__init__.py to make sure NAME +
'.evolve' can be imported.)

Now you are ready to create your versioned schema::

    import sqlalchemy
    import stucco_evolution

    engine = sqlalchemy.create_engine(...)

    with engine.begin() as connection: # engine.begin() since SQLAlchemy 0.7.6
        stucco_evolution.initialize(connection)
        stucco_evolution.create_or_upgrade_packages(connection, 'mypackage')

In this pattern, stucco_evolution tries to create the schema for
`mypackage` and all its dependencies, in topological order, if they
are not currently tracked in the stucco_evolution table. `create.py`
will only ever be called once for a particular package, so the evolution
scripts must be responsible for creating new tables added in a particular
`VERSION` of the schema.

Eventually `mypackage` will need a new `VERSION`. To do this, you must
increment `VERSION` to N and add `evolve/evolveN.py` to the evolution
module.

`evolve/__init__.py`::

	NAME = 'mypackage'
	VERSION = 1
	DEPENDS = []

`evolve/evolve1.py`::

	def evolve(connection):
	    connection.execute("CREATE TABLE foo (bar INTEGER)")
	    connection.execute("ALTER TABLE baz ADD COLUMN quux INTEGER")

The next time you call `create_or_upgrade(...)`, stucco_evolution will
notice `mymodule` is already tracked in the stucco_evolution table but
its database version less than `mymodule.evolve.VERSION`. To rectify,
stucco_evolution calls each evolveN.py greater than the database version
in order to bring the database up to date.

In case of dependencies, `stucco_evolution` will try to create or bring
each dependency package fully up-to-date before trying to upgrade its
dependent packages. Dependency support is an experimental feature.

Omitted features
----------------

There is no provision for downgrade scripts. I used to write them myself
but I never used them. Instead, back up your database and test against
a temporary testing database.

There is no DDL abstraction library. Feel free to use any one you like, or
just write the ALTER TABLE statements yourself.

Robust upgrade scripts
----------------------

If you are arrogant enough to release your package as a dependency to another
package or if it will be widely installed, you need to make sure your upgrade
scripts are robust. The most important rule:

* New code must never change the output of old evolution scripts.

The simplest way to do this is to issue all DDL as text and never import
your package in evolve scripts or call SQLAlchemy's create_all()
except in the create script. You could also try copying and pasting
your model into each evolve script, as suggested by sqlalchemy-migrate,
so SQLAlchemy can generate the DDL. You could keep backups of each version
of the schema and write tests that restore each backup and upgrade to the
latest version to make sure this remains possible for all prior versions.

