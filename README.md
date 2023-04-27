<div id="top"></div>

<p>
   <a href="https://pepy.tech/project/cat-win/" alt="Downloads">
      <img src="https://static.pepy.tech/personalized-badge/cat-win?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Downloads" align="right">
   </a>
   <a href="https://pypi.org/project/cat-win/" alt="Visitors">
      <img src="https://visitor-badge.laobi.icu/badge?page_id=SilenZcience.cat_win&right_color=orange" align="right">
   </a>
   <a href="https://github.com/SilenZcience/cat_win/tree/main/cat_win" alt="CodeSize">
      <img src="https://img.shields.io/github/languages/code-size/SilenZcience/cat_win?color=purple" align="right">
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
[![Coverage]](https://raw.githubusercontent.com/SilenZcience/cat_win/badges/.github/badges/badge-coverage.svg)
[![Tests]](https://raw.githubusercontent.com/SilenZcience/cat_win/badges/.github/badges/badge-tests.svg)
<!-- [![Compile-and-Push]](https://github.com/SilenZcience/cat_win/actions/workflows/build_executable.yml/badge.svg) -->

This project copies the fundamental framework of the cat command-line tool from Linux and translates its features to an OS Independent program using Python. </br> Over time the project evolved in subject areas of other tools like 'echo', 'grep', 'ls', 'base64'.

Additionally it includes the feature to strip and reverse the content of any given file, make use of the standard-input, which enables cat piping into each other, generating the checksum of any file, converting decimal, hexadecimal and binary numbers within any text, and much <a href="#usage">more</a> ...

Contrary to the name of the project it is of course possible to use cat_win on Linux or MacOS!

### Made With
[![MadeWith-Python]](https://www.python.org/)
[![Python][Python-Version]](https://www.python.org/)

<p align="right">(<a href="#top">back to top</a>)</p>

## Getting Started

### Prerequisites

- Using cat_win as a Python-Package demands a Python-Interpreter (>= 3.7).
- Using cat_win as an Executable (Windows only!) demands no prerequisites, hereby the stand-alone executable `catw.exe`  is sufficient.

### Installation
[![Version][CurrentVersion]](https://pypi.org/project/cat-win/)

Simply install the python package (via [PyPI-cat_win](https://pypi.org/project/cat-win/)):
```console
python -m pip install --upgrade cat_win[clip]
```
cat_win uses the [pyperclip](https://pypi.org/project/pyperclip/) module by default. Should any problems occur, you can also use
the [pyperclip3](https://pypi.org/project/pyperclip3/) or [pyclip](https://pypi.org/project/pyclip/) module.
In this case simply run:
```console
python -m pip install --upgrade cat_win
```
and manually install the desired module yourself.

**OR alternatively** you can use the compiled version (*`Windows only`*):

1. Simply download the [catw.exe](https://raw.githubusercontent.com/SilenZcience/cat_win/main/bin/catw.exe) file.
2. Add the file path to your system-environment `PATH`-variables.

> ⚠️ **You should never trust any executable file!** Feel free to compile the package yourself (e.g. using [PyInstaller](https://pyinstaller.org/en/stable/)).

> You can verify the creation of catw.exe yourself by reading the [source code](https://github.com/SilenZcience/cat_win/blob/main/cat_win/cat.py), checking the [origin](https://github.com/SilenZcience/cat_win/tree/main/bin) of the file and validating the corresponding [workflow](https://github.com/SilenZcience/cat_win/blob/main/.github/workflows/build_executable.yml) used.

<p align="right">(<a href="#top">back to top</a>)</p>

## Usage

```console
catw [FILE]... [OPTION]...
catw --help
```

> ⚠️ *from v1.0.33 to v1.1.0 the entrypoint changes from `cat` to `catw`. If you wish to keep the old command, you will have to define an alias yourself.*

| Argument / Option      | Description                                               |
|------------------------|-----------------------------------------------------------|
| *-h, --help*           | show help message and exit                                |
| *-v, --version*        | output version information                                |
| *-d, --debug*          | show debug information                                    |
|                        |                                                           |
| *-n, --number*         | number all output lines                                   |
| *-l, --linelength*     | display the length of each line                           |
| *-e, --ends*           | display $ at the end of each line                         |
| *-t, --tabs*           | display TAB characters as ^I                              |
| *--eof, --eof*         | display EOF characters as ^EOF                            |
| *-u, --unique*         | suppress repeated output lines                            |
| *-b, --blank*          | hide empty lines                                          |
| *-r, --reverse*        | reverse output                                            |
| *-p, --peek*           | only print the first and last lines                       |
| *-s, --sum*            | show sum of lines                                         |
| *-S, --SUM*            | ONLY show sum of lines                                    |
| *-f, --files*          | list applied files                                        |
| *-F, --FILES*          | ONLY list applied files and file sizes                    |
| *-g, --grep*           | only show lines containing queried keywords               |
| *-i, --interactive*    | use stdin                                                 |
| *-o, --oneline*        | take only the first stdin-line                            |
| *-E, --ECHO*           | handle every following parameter as stdin                 |
| *-c, --clip*           | copy output to clipboard                                  |
| *-m, --checksum*       | show the checksums of all files                           |
| *-a, --attributes*     | show meta-information about the files                     |
|                        |                                                           |
| *--dec, --DEC*         | convert decimal numbers to hexadecimal and binary         |
| *--hex, --HEX*         | convert hexadecimal numbers to decimal and binary         |
| *--bin, --BIN*         | convert binary numbers to decimal and hexadecimal         |
| *--b64e, --b64e*       | encode the input to base64                                |
| *--b64d, --b64d*       | decode the input from base64                              |
|                        |                                                           |
| *--hexview, --HEXVIEW* | display the raw byte representation in hexadecimal        |
| *--binview, --binview* | display the raw byte representation in binary             |
|                        |                                                           |
| *--nc, --nocolor*      | disable colored output                                    |
| *--nb, --nobreak*      | do not interrupt the output on queried keywords           |
| *--nk, --nokeyword*    | inverse the grep output                                   |
| *-R, --reconfigure*    | reconfigure the stdin and stdout with the parsed encoding |
| *--config, --config*   | change color configuration                                |
|                        |                                                           |
| *enc=X*                | set file enconding to X (default is utf-8)                |
| *find=X*               | find/query a substring X in the given files               |
| *match=X*              | find/query a pattern X in the given files                 |
| *trunc=X:Y*            | truncate file to lines X and Y (python-like)              |
|                        |                                                           |
| *[a,b]*                | replace a with b in every line                            |
| *[a:​b:c]*              | python-like string indexing syntax (line by line)         |

### Examples

<details open>
	<summary><b>📂 Images 📂</b></summary>

![Example1](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example1.png "example1")

![Example2](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example2.png "example2")

![Example3](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example3.png "example3")

![Example4](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example4.png "example4")

![Example5](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example5.png "example5")

![Example6](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example6.png "example6")

</details>

```console
$ echo "Hello World :)" | catw -i [6:] | catw -i [::-1] -ln
> 1) [8] ): dlroW
```

```c
$ cats --dec -nl
> >>> 12345
> 1) [53] 12345 {Hexadecimal: 0x3039; Binary: 0b11000000111001}
> >>> 54321
> 2) [55] 54321 {Hexadecimal: 0xd431; Binary: 0b1101010000110001}
> ...
```

<p align="right">(<a href="#top">back to top</a>)</p>

## Changelog

Take a look at the [Changelog](https://github.com/SilenZcience/cat_win/blob/main/CHANGELOG.md) file.

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
[Compile-and-Push]: https://github.com/SilenZcience/cat_win/actions/workflows/build_executable.yml/badge.svg

[Coverage]: https://raw.githubusercontent.com/SilenZcience/cat_win/badges/.github/badges/badge-coverage.svg
[Tests]: https://raw.githubusercontent.com/SilenZcience/cat_win/badges/.github/badges/badge-tests.svg

[MadeWith-Python]: https://img.shields.io/badge/Made%20with-Python-brightgreen
[Python-Version]: https://img.shields.io/badge/Python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%20pypy--3.8%20%7C%20pypy--3.9-blue

[CurrentVersion]: https://img.shields.io/pypi/v/cat_win.svg

[GitHub-SilenZcience]: https://img.shields.io/badge/GitHub-SilenZcience-orange
