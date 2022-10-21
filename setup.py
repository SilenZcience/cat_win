import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), "README_PyPI.md")) as readme:
    README = readme.read()

setup(
    name='cat_win',
    version='1.0.5',    
    description="Simple 'cat' Command-line Tool made in Python",
    url='https://github.com/SilenZcience/cat_win',
    author='Silas A. Kraume',
    author_email='silas.kraume1552@gmail.com',
    long_description=README,
    long_description_content_type='text/markdown',
    license='MIT License',
    packages=['cat_win', 'cat_win.util'],
    install_requires=['pyperclip3==0.4.1'],
    entry_points={
        'console_scripts': 'cat = cat_win.cat:main'
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.6'
)