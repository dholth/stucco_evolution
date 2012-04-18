import os
import sys
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = ['SQLAlchemy', 'repoze.evolution']

tests_requires = ['nose'] + requires

setup(name='stucco_evolution',
      version='0.4',
      description='Moderately simple schema upgrades for SQLAlchemy.',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Intended Audience :: Developers",
        "Topic :: Database :: Front-Ends",
        ],
      author='Daniel Holth',
      author_email='dholth@fastmail.fm',
      url='http://bitbucket.org/dholth/stucco_evolution',
      keywords='sqlalchemy stucco',
      license='BSD',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=tests_requires,
      obsoletes=['ponzi_evolution'],
      test_suite='nose.collector',
      entry_points = """\
      [paste.paster_create_template]
      stucco_evolution=stucco_evolution.paster:EvolveModule
      """,
      )

