from setuptools import setup

setup(
    name='cat_win',
    version='1.0.1',    
    description="Simple 'cat' Command-line Tool made in Python",
    url='https://github.com/SilenZcience/cat_win',
    author='Silas A. Kraume',
    author_email='silas.kraume1552@gmail.com',
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