from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup


setup(name='hogs',
      version='0.1',
      py_modules=['hog'],
      entry_points={
        'console_scripts': [
            'hog = hog:main',
        ]
      },
     )
