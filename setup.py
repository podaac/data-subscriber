from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(name='podaac-data-subscriber',
      version='1.9.0',
      description='PO.DAAC Data Susbcriber Command Line Tool',
      url='https://github.com/podaac/data-subscriber',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='PO.DAAC',
      author_email='podaac@podaac.jpl.nasa.gov',
      license='apache-2',
      packages=['subscriber'],
      entry_points='''
        [console_scripts]
        podaac-data-subscriber=subscriber.podaac_data_subscriber:main
        podaac-data-downloader=subscriber.podaac_data_downloader:main
    ''',
      zip_safe=False)
