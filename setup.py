import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = ['SQLAlchemy', 'repoze.evolution']

setup(name='stucco_evolution',
      version='0.9',
      description='Dead simple schema upgrades for SQLAlchemy.',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Daniel Holth',
      author_email='dholth@fastmail.fm',
      url='http://bitbucket.org/dholth/stucco_evolution',
      keywords='sqlalchemy',
      license='BSD',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      obsoletes=['ponzi_evolution'],
      test_suite="stucco_evolution",
      entry_points = """\
      """,
      )

