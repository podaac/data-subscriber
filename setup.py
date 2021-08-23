from setuptools import setup

setup(name='podaac-data-subscriber',
      version='1.2.0',
      description='PO.DAAC Data Susbcriber Command Line Tool',
      url='https://github.com/podaac/data-subscriber',
      author='PO.DAAC',
      author_email='podaac@podaac.jpl.nasa.gov',
      license='apache-2',
      packages=['subscriber'],
      entry_points='''
        [console_scripts]
        podaac-data-subscriber=subscriber.podaac_data_subscriber:run
    ''',
      zip_safe=False)
