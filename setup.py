import mentalist

from setuptools import setup

setup(name='Mentalist',
      version=mentalist.version,
      author='sc0tfree',
      author_email='henry@sc0tfree.com',
      license='MIT',
      description='Mentalist is a graphical tool for custom wordlist generation. It utilizes common human paradigms for constructing passwords and can output the full wordlist or rules.',
      keywords='wordlist wordlist-generator passwords',
      packages=['mentalist', 'mentalist.view', 'mentalist.data', 'tests',
                'mentalist.icons'],
      entry_points={'gui_scripts': 'mentalist = mentalist.controller:main'},
      test_suite='tests.test_model',
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      package_data={'mentalist': ['data/*.txt', 'data/*.psv']},
      include_package_data=True,
      )
