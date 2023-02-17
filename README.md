<div id="top"></div>

<p>
   <a href="https://pepy.tech/project/cat-win" alt="Downloads">
      <img src="https://static.pepy.tech/personalized-badge/cat-win?period=total&units=international_system&left_color=grey&right_color=orange&left_text=Downloads" align="right">
   </a>
   <a href="https://pypi.org/project/cat-win/" alt="Visitors">
      <img src="https://visitor-badge.laobi.icu/badge?page_id=SilenZcience.cat_win" align="right">
   </a>
</p>

[![OS-Windows]][OS-Windows]
[![OS-Linux]][OS-Linux]
[![OS-MacOS]][OS-MacOS]

<br/>
<div align="center">
<h2 align="center">cat_win</h2>
   <p align="center">
      Simple Command-line Tool made in Python
      <br/>
      <a href="https://github.com/SilenZcience/cat_win/blob/main/cat_win/cat.py">
         <strong>Explore the code »</strong>
      </a>
      <br/>
      <br/>
      <a href="https://github.com/SilenZcience/cat_win/issues">Report Bug</a>
      ·
      <a href="https://github.com/SilenZcience/cat_win/issues">Request Feature</a>
   </p>
</div>


<details>
   <summary>Table of Contents</summary>
   <ol>
      <li>
         <a href="#about-the-project">About The Project</a>
         <ul>
            <li><a href="#made-with">Made With</a></li>
         </ul>
      </li>
      <li>
         <a href="#getting-started">Getting Started</a>
         <ul>
            <li><a href="#prerequisites">Prerequisites</a></li>
            <li><a href="#installation">Installation</a></li>
         </ul>
      </li>
      <li><a href="#usage">Usage</a>
         <ul>
         <li><a href="#examples">Examples</a></li>
         </ul>
      </li>
	  <li><a href="#changelog">Changelog</a></li>
      <li><a href="#license">License</a></li>
      <li><a href="#contact">Contact</a></li>
   </ol>
</details>

## About The Project

[![Unittests]](https://github.com/SilenZcience/cat_win/actions/workflows/unit_test.yml)
[![Build-and-Check]](https://github.com/SilenZcience/cat_win/actions/workflows/package_test.yml)

This project copies the fundamental framework of the cat command-line tool from Linux and translates its features to an OS Independent program using Python.

Additionally it includes the feature to strip and reverse the content of any given file, make use of the standard-input, which enables cat piping into each other, generating the checksum of any file, converting decimal, hexadecimal and binary numbers within any text, and much <a href="#usage">more</a> ...

Contrary to the name of the project it is of course possible to use cat_win on Linux or MacOS!

### Made With
[![MadeWith-Python]](https://www.python.org/)

<p align="right">(<a href="#top">back to top</a>)</p>

## Getting Started

### Prerequisites

No Prerequisites are neccessary; The stand-alone executable `catw.exe` is sufficient.

> ⚠️ **You should never trust any executable file!**

### Installation

1. Clone the repository and move into the root\bin directory with:
```console
git clone git@github.com:SilenZcience/cat_win.git
cd cat_win\bin
```
2. Add the directory to your system-environment `PATH`-variables.

or simply install the python package ([PyPI-cat_win](https://pypi.org/project/cat-win/)):
```console
pip install cat-win
```
<p align="right">(<a href="#top">back to top</a>)</p>

## Usage

```console
catw [FILE]... [OPTION]...
catw --help
```

> ⚠️ *from v1.0.33 to v1.1.0 the entrypoint changes from ``cat`` to ``catw``. If you wish to keep the old command, you will have to define an alias yourself.*


| Argument               | Description                                       |
|------------------------|---------------------------------------------------|
| *-h, --help*           | show help message and exit                        |
| *-v, --version*        | output version information                        |
| *-d, --debug*          | show debug information                            |
|                        |                                                   |
| *-n, --number*         | number all output lines                           |
| *-l, --linelength*     | display the length of each line                   |
| *-e, --ends*           | display $ at the end of each line                 |
| *-t, --tabs*           | display TAB characters as ^I                      |
| *--eof, --eof*         | display EOF characters as ^EOF                    |
| *-u, --unique*         | suppress repeated output lines                    |
| *-b, --blank*          | hide empty lines                                  |
| *-r, --reverse*        | reverse output                                    |
| *-s, --sum*            | show sum of lines                                 |
| *-f, --files*          | list applied files                                |
| *-i, --interactive*    | use stdin                                         |
| *-o, --oneline*        | take only the first stdin-line                    |
| *-p, --peek*           | only print the first and last lines               |
| *-c, --clip*           | copy output to clipboard                          |
| *-m, --checksum*       | show the checksums of all files                   |
| *-a, --attributes*     | show meta-information about the files             |
|                        |                                                   |
| *--dec, --DEC*         | convert decimal numbers to hexadecimal and binary |
| *--hex, --HEX*         | convert hexadecimal numbers to decimal and binary |
| *--bin, --BIN*         | convert binary numbers to decimal and hexadecimal |
| *--b64e, --b64e*       | encode the input to base64                        |
| *--b64d, --b64d*       | decode the input from base64                      |
|                        |                                                   |
| *--nc, --nocolor*      | disable colored output                            |
| *--config, --config*   | change color configuration                        |
|                        |                                                   |
| *enc=X*                | set file enconding to X (default is utf-8)        |
| *find=X*               | find substring X in the given files               |
| *match=X*              | find pattern X in the given files                 |
| *trunc=X:Y*            | truncate file to lines X and Y (python-like)      |
|                        |                                                   |
| *[a,b]*                | replace a with b in every line                    |
| *[a:​b:c]*              | python-like string indexing syntax (line by line) |

### Examples

![Example1](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example1.png "example1")

![Example2](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example2.png "example2")

![Example3](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example3.png "example3")

![Example4](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example4.png "example4")

<p align="right">(<a href="#top">back to top</a>)</p>

## Changelog

Take a look at the Changelog [here](https://github.com/SilenZcience/cat_win/blob/main/CHANGELOG.md).

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/SilenZcience/cat_win/blob/main/LICENSE) file for details

## Contact

> **SilenZcience** <br/>
[![GitHub-SilenZcience][GitHub-SilenZcience]](https://github.com/SilenZcience)

[OS-Windows]: https://svgshare.com/i/ZhY.svg
[OS-Linux]: https://svgshare.com/i/Zhy.svg
[OS-MacOS]: https://svgshare.com/i/ZjP.svg

[Unittests]: https://github.com/SilenZcience/cat_win/actions/workflows/unit_test.yml/badge.svg
[Build-and-Check]: https://github.com/SilenZcience/cat_win/actions/workflows/package_test.yml/badge.svg

[MadeWith-Python]: https://img.shields.io/badge/Made%20with-Python-brightgreen

[GitHub-SilenZcience]: https://img.shields.io/badge/GitHub-SilenZcience-orange