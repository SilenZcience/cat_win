<div id="top"></div>

<p>
   <a href="https://pypi.org/project/cat-win/" alt="Downloads">
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
      <li><a href="#license">License</a></li>
      <li><a href="#contact">Contact</a></li>
   </ol>
</details>

## About The Project

This project copies the fundamental framework of the cat command-line tool from linux and translates its features to an OS Independent file.

Additionally it includes the feature to strip and reverse the content of any given file, make use of the standard-input, which enables cat piping into each other, generating the checksum of any file, and even convert decimal, hexadecimal and binary numbers within any text.

### Made With
[![Python][MadeWith-Python]](https://www.python.org/)

<p align="right">(<a href="#top">back to top</a>)</p>

## Getting Started

### Prerequisites

No Prerequisites are neccessary; The stand-alone executable `cat.exe` is sufficient.

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
cat [FILE]... [OPTION]...

cat --help
```

⚠️ *on linux or macOS systems you might need to define an alias or use:*
```console
python3 -m cat_win.cat [FILE]... [OPTION]...

python3 -m cat_win.cat --help
```

| Argument               | Description                                       |
|------------------------|---------------------------------------------------|
| -n, --number           | number all output lines                           |
| -e, --ends             | display $ at the end of each line                 |
| -t, --tabs             | display TAB characters as ^I                      |
| -s, --squeeze          | suppress repeated output lines                    |
| -r, --reverse          | reverse output                                    |
| -c, --count            | show sum of lines                                 |
| -b, --blank            | hide empty lines                                  |
| -f, --files            | list applied files                                |
| -i, --interactive      | use stdin                                         |
| -l, --clip             | copy output to clipboard                          |
| -m, --checksum         | show the checksums of all files                   |
| -a, --attributes       | show meta-information about the files             |
| -dec, --dec            | convert decimal numbers to hexadecimal and binary |
| -hex, --hex            | convert hexadecimal numbers to decimal and binary |
| -bin, --bin            | convert binary numbers to decimal and hexadecimal |
| -v, --version          | output version information                        |
| -col, --color          | show colored output                               |
| enc=X                  | set file enconding to X.                          |
| find=X                 | find X in the given files (literal).              |
| rfind=X                | find X in the given files (regex).                |
| [a;b]                  | replace a with b in every line.                   |
| [a:b]                  | python-like string manipulation syntax.           |

### Examples

![Example1](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example1.png "example1")

![Example2](https://raw.githubusercontent.com/SilenZcience/cat_win/main/img/example2.png "example2")

<p align="right">(<a href="#top">back to top</a>)</p>

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/SilenZcience/cat_win/blob/main/LICENSE) file for details

## Contact

> **SilenZcience** <br/>
[![GitHub-SilenZcience][GitHub-SilenZcience]](https://github.com/SilenZcience)

[OS-Windows]: https://svgshare.com/i/ZhY.svg
[OS-Linux]: https://svgshare.com/i/Zhy.svg
[OS-MacOS]: https://svgshare.com/i/ZjP.svg

[MadeWith-Python]: https://img.shields.io/badge/Made%20with-Python-brightgreen

[GitHub-SilenZcience]: https://img.shields.io/badge/GitHub-SilenZcience-orange