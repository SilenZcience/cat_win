<div id="top"></div>

<p>
   <a href="https://pepy.tech/project/cat-win/" alt="Downloads">
      <img src="https://static.pepy.tech/personalized-badge/cat-win?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Downloads" align="right">
   </a>
   <a href="https://pypi.org/project/cat-win/" alt="Visitors">
      <img src="https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2FSilenZcience%2Fcat_win&count_bg=%23FF7700&title_bg=%23555555&icon=&icon_color=%23E7E7E7&title=Visitors&edge_flat=false" align="right">
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
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/cat_win.logo.png" width="25%"/>
   </p>
   <p align="center">
      Simple Command-line Tool made in Python
      <br/>
      <a href="https://github.com/SilenZcience/cat_win/blob/main/cat_win/src/cat.py">
         <strong>Explore the code »</strong>
      </a>
      <br/>
      <br/>
      <a href="https://github.com/SilenZcience/cat_win/issues/new?assignees=&labels=feature&projects=&template=feature_request.yaml">Request Feature</a>
      ·
      <a href="https://github.com/SilenZcience/cat_win/issues/new?assignees=&labels=bug&projects=&template=bug_report.yaml&title=%F0%9F%90%9B+Bug+Report%3A+">Report Bug</a>
      ·
      <a href="https://github.com/SilenZcience/cat_win/issues/new?assignees=&labels=docs&projects=&template=documentation_request.yaml&title=%F0%9F%93%96+Documentation%3A+">Request Documentation</a>
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
         <li><a href="#documentation">Documentation</a></li>
         <li><a href="#examples">Examples</a></li>
         </ul>
      </li>
      <li><a href="#changelog">Changelog</a></li>
      <li><a href="#license">License</a></li>
      <li><a href="#contact">Contact</a></li>
   </ol>
</details>

<div id="about-the-project"></div>

## 🔥 About The Project

[![Unittests]](https://github.com/SilenZcience/cat_win/actions/workflows/unit_test.yml)
[![Build-and-Check]](https://github.com/SilenZcience/cat_win/actions/workflows/package_test.yml)
[![Coverage]](https://raw.githubusercontent.com/SilenZcience/cat_win/badges/badges/badge-coverage.svg)
[![Tests]](https://raw.githubusercontent.com/SilenZcience/cat_win/badges/badges/badge-tests.svg)
<!-- [![Compile-and-Push]](https://github.com/SilenZcience/cat_win/actions/workflows/build_executable.yml/badge.svg) -->

This project copies the fundamental framework of the cat command-line tool from Unix and translates its features to an OS Independent program using Python. </br> Over time the project evolved in subject areas of other tools like 'echo', 'grep', 'ls', 'base64'...

Additionally it includes the feature to strip and reverse the content of any given file, make use of the standard-input, which enables cat piping into each other, generating the checksum of any file, converting decimal, hexadecimal and binary numbers within any text, and much *much* <a href="#usage">more</a> ...

It is of course possible to use cat_win on Linux or MacOS, aswell as Windows!

<div id="made-with"></div>

### Made With
[![MadeWith-Python]](https://www.python.org/)
[![Python][Python-Version]](https://www.python.org/)

<p align="right">(<a href="#top">↑back to top↑</a>)</p>
<div id="getting-started"></div>

## ⚡️ Getting Started

<div id="prerequisites"></div>

### Prerequisites

Using cat_win as a `Python Package` demands a Python-Interpreter (>= 3.7).

Using cat_win as a `Binary Executable` demands no prerequisites, hereby the stand-alone executables are sufficient.

<div id="installation"></div>

### Installation
[![Version][CurrentVersion]](https://pypi.org/project/cat-win/)

`Python Package` </br>
Simply install the python package (via [PyPI-cat_win](https://pypi.org/project/cat-win/)):
```console
python -m pip install --upgrade cat_win[clip]
```
```console
python -m pip install --upgrade cat_win
```
cat_win uses the [pyperclip](https://pypi.org/project/pyperclip/) module by default. Should any problems occur, you can also use
the [pyperclip3](https://pypi.org/project/pyperclip3/) or [pyclip](https://pypi.org/project/pyclip/) module.
In this case simply don't install with `[clip]` and manually install the desired module yourself.

On older Windows systems colored output may not be displayed correctly.
In this case you can try to fix the problem by installing the cat_win-package with the optional color-fix `[cfix]` dependency.
This fix will use the [colorama](https://pypi.org/project/colorama/) module
which can also be installed after the fact to patch the problem.

`Binary Executable` </br>
**OR alternatively** you can use the (standalone) binary executable version:

<div id="download"></div>

Direct Download:
</br>
[Windows - __catw.exe__](https://raw.githubusercontent.com/SilenZcience/cat_win/binaries/bin/windows/catw.exe) </br>
[Windows - __cats.exe__ (shell)](https://raw.githubusercontent.com/SilenZcience/cat_win/binaries/bin/windows/cats.exe) </br>
[Linux - __catw__](https://raw.githubusercontent.com/SilenZcience/cat_win/binaries/bin/linux/catw) </br>
[Linux - __cats__ (shell)](https://raw.githubusercontent.com/SilenZcience/cat_win/binaries/bin/linux/cats) </br>
[MacOS - __catw__](https://raw.githubusercontent.com/SilenZcience/cat_win/binaries/bin/darwin/catw) </br>
[MacOS - __cats__ (shell)](https://raw.githubusercontent.com/SilenZcience/cat_win/binaries/bin/darwin/cats) </br>

(compiled using PyInstaller) </br>
It is recommended to add the file path(s) to your system-environment `PATH`-variables.

> ❗️ **You should never trust any executable file!** Feel free to compile the package yourself (e.g. using [PyInstaller](https://pyinstaller.org/en/stable/)).

> ⚠️ You can verify the creation of the executable files yourself by reading the [source code](https://github.com/SilenZcience/cat_win/blob/main/cat_win/src/cat.py), checking the [origin](https://github.com/SilenZcience/cat_win/tree/binaries/bin) of the file and validating the corresponding [workflow](https://github.com/SilenZcience/cat_win/blob/main/.github/workflows/build_executable.yml) used.

<p align="right">(<a href="#top">↑back to top↑</a>)</p>
<div id="usage"></div>

## ⚙️ Usage

```console
> catw [FILE]... [OPTION]...
> catw --help
Concatenate FILE(s) to standard output.
...
```

```console
> cats [OPTION]...
> cats --help
Interactively manipulate standard input.
...
```

<div id="documentation"></div>

### Documentation

👉 A detailed [Documentation🖺](https://github.com/SilenZcience/cat_win/blob/main/DOCUMENTATION.md) of all **Parameters** has moved to another File.
Read about specific **Arguments & Options** [here](https://github.com/SilenZcience/cat_win/blob/main/DOCUMENTATION.md).

<div id="examples"></div>

### Examples

<details>
   <summary><b>📂 Images 📂</b></summary>
   </br>

   <p float="left">
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example1.png" width="49%"/>
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example2.png" width="49%"/>
   </p>

   <p float="left">
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example3.png" width="49%"/>
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example4.png" width="49%"/>
   </p>

   <p float="left">
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example5.png" width="49%"/>
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example6.png" width="49%"/>
   </p>

   <p float="left">
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example7.png" width="49%"/>
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example8.png" width="49%"/>
   </p>

   - - - -

   <p float="left">
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example9.png" width="49%"/>
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example10.png" width="49%"/>
   </p>

   <p float="left">
      <img src="https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example11.png" width="49%"/>
   </p>

</details>
</br>

```py
$ echo "Hello World :)" | catw - [6:] | catw - [::-1] -ln
> 1) [8] ): dlroW
```

- - - -

```py
$ cats --eval --dec -nl
> >>> 0xF * 5
1) [42] 75 [Bin: 0b1001011, Oct: 0o113, Hex: 0x4b]
> >>> ...
```

<p align="right">(<a href="#top">↑back to top↑</a>)</p>
<div id="changelog"></div>

## 📋 Changelog

Take a look at the [Changelog](https://github.com/SilenZcience/cat_win/blob/main/CHANGELOG.md) file.

<div id="license"></div>

## 📜 License
<a href="https://github.com/SilenZcience/cat_win/blob/main/LICENSE" alt="License">
   <img src="https://img.shields.io/pypi/l/cat_win" align="right">
</a>

This project is licensed under the MIT License - see the [LICENSE](https://github.com/SilenZcience/cat_win/blob/main/LICENSE) file for details

<div id="contact"></div>

## ⭐️ Contact

> **SilenZcience** <br/>
[![GitHub-SilenZcience][GitHub-SilenZcience]](https://github.com/SilenZcience)

[OS-Windows]: https://img.shields.io/badge/os-windows-green
[OS-Linux]: https://img.shields.io/badge/os-linux-green
[OS-MacOS]: https://img.shields.io/badge/os-macOS-green

[Unittests]: https://github.com/SilenZcience/cat_win/actions/workflows/unit_test.yml/badge.svg?branch=dev
[Build-and-Check]: https://github.com/SilenZcience/cat_win/actions/workflows/package_test.yml/badge.svg?branch=dev
[Compile-and-Push]: https://github.com/SilenZcience/cat_win/actions/workflows/build_executable.yml/badge.svg?branch=dev

[Coverage]: https://raw.githubusercontent.com/SilenZcience/cat_win/badges/badges/badge-coverage.svg
[Tests]: https://raw.githubusercontent.com/SilenZcience/cat_win/badges/badges/badge-tests.svg

[MadeWith-Python]: https://img.shields.io/badge/Made%20with-Python-brightgreen
[Python-Version]: https://img.shields.io/badge/Python-3.7%20--%203.12%20%7C%20pypy--3.7%20--%20pypy--3.10-blue
<!-- https://img.shields.io/badge/Python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%20pypy--3.7%20%7C%20pypy--3.8%20%7C%20pypy--3.9%20%7C%20pypy--3.10-blue -->

[CurrentVersion]: https://img.shields.io/pypi/v/cat_win.svg

[License]: https://img.shields.io/pypi/l/cat_win

[GitHub-SilenZcience]: https://img.shields.io/badge/GitHub-SilenZcience-orange
