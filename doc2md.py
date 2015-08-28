#! /usr/bin/env python
# encoding: utf-8
"""
Very lightweight docstring to Markdown converter.


### License

Copyright © 2013 Thomas Gläßle <t_glaessle@gmx.de>

This work  is free. You can  redistribute it and/or modify  it under the
terms of the Do What The Fuck  You Want To Public License, Version 2, as
published by Sam Hocevar. See the COPYING file for more details.

This program  is free software.  It comes  without any warranty,  to the
extent permitted by applicable law.


### Description

Little convenience tool to extract docstrings from a module or class and
convert them to GitHub Flavoured Markdown:

https://help.github.com/articles/github-flavored-markdown

Its purpose is to quickly generate `README.md` files for small projects.


### API

The interface consists of the following functions:

 - `make_toc(sections)`
 - `doc2md(docstring, title)`

### Limitations

At the moment  this is suited only  for a very specific use  case. It is
hardly forseeable, if I will decide to improve on it in the near future.

"""
import re
import sys
import inspect

__all__ = ['doctrim', 'doc2md']

SECTIONS = [
    'Args:',
    'Attributes:',
    'Returns:',
    'Raises:',
    'Notes:',
    'Examples:'
]

INDENT = "    "
NEW_LINE = ""
LINK = '<a name="{name}"></a>'

# Level for each section in class
CLASS_NAME = 2
FUNCTION_NAME = 3
SECTION_NAME = 4

doctrim = inspect.cleandoc

def unindent(lines):
    """
    Remove common indentation from string.

    Unlike doctrim there is no special treatment of the first line.

    """
    try:
        # Determine minimum indentation:
        indent = min(len(line) - len(line.lstrip())
                     for line in lines if line)
    except ValueError:
        return lines
    else:
        return [line[indent:] for line in lines]

def code_block(lines, language=''):
    """
    Mark the code segment for syntax highlighting.
    """
    return ['```' + language] + lines + ['```']

def doctest2md(lines):
    """
    Convert the given doctest to a syntax highlighted markdown segment.
    """
    is_only_code = True
    lines = unindent(lines)
    for line in lines:
        if not line.startswith('>>> ') and not line.startswith('... ') and line not in ['>>>', '...']:
            is_only_code = False
            break
    if is_only_code:
        orig = lines
        lines = []
        for line in orig:
            lines.append(line[4:])
    return lines

def doc_code_block(lines, language):
    if language == 'python':
        lines = doctest2md(lines)
    return code_block(lines, language)

_reg_section = re.compile('^#+ ')
def is_heading(line):
    return _reg_section.match(line)

def get_heading(line):
    assert is_heading(line)
    part = line.partition(' ')
    return len(part[0]), part[2]

def make_heading(level, title):
    return '#'*max(level, 1) + ' ' + title

def find_sections(lines):
    """
    Find all section names and return a list with their names.
    """
    sections = []
    for line in lines:
        if is_heading(line):
            sections.append(get_heading(line))
    return sections

def make_toc(sections):
    """
    Generate table of contents for array of section names.
    """
    if not sections:
        return []
    refs = []
    for sec, ind in sections:
        ref = sec.lower()
        ref = ref.replace(' ', '-')
        ref = ref.replace('?', '')
        refs.append(INDENT*(ind) + "- [%s](#%s)" % (sec, ref))
    return '\n'.join(refs)

def _get_class_intro(lines):
    intro = []
    contents = lines[:]
    for line in lines:
        if line.strip() in SECTIONS:
            return intro, contents
        else:
            contents.pop(0)
            intro += [line + NEW_LINE]
    return intro, contents

def _is_class_section(line):
    line = line.strip()
    if line in SECTIONS:
        return SECTION_NAME
    return 0

def _doc2md(lines):
    md = []
    is_code = False
    for line in lines:
        trimmed = line.lstrip()
        level = _is_class_section(line)
        if is_code:
            if line:
                code.append(line)
            else:
                is_code = False
                md += doc_code_block(code, language)
                md += [line]
        elif trimmed.startswith('>>> '):
            is_code = True
            language = 'python'
            code = [line]
        elif trimmed.startswith('$ '):
            is_code = True
            language = 'bash'
            code = [line]
        elif level > 0:
            md += [make_heading(level, line)]
        else:
            md += [line]
    if is_code:
        md += doc_code_block(code, language)
    return md

def doc2md(docstr, title, type=0):
    # Type = 0 -> class, Type = 1 -> functions
    """
    Convert a docstring to a markdown text.
    """
    text = doctrim(docstr)
    lines = text.split('\n')
    intro, contents = _get_class_intro(lines)
    if type == 0:
        level = CLASS_NAME
        title = LINK.format(name=title.lower())+title
    if type == 1:
        level = FUNCTION_NAME
        title = 'Function: {func_name}'.format(func_name=title)
    md = [
        make_heading(level, title),
        NEW_LINE
    ]
    md += intro
    md += _doc2md(contents)
    return "\n".join(md)

# This function is obsolete, shouldn't be used.
def mod2md(module, title, title_api_section, toc=True):
    """
    Generate markdown document from module, including API section.
    """
    docstr = module.__doc__

    text = doctrim(docstr)
    lines = text.split('\n')

    sections = find_sections(lines)
    if sections:
        level = min(n for n,t in sections) - 1
    else:
        level = 1

    api_md = []
    api_sec = []
    if title_api_section and module.__all__:
        sections.append((level+1, title_api_section))
        for name in module.__all__:
            api_sec.append((level+2, name))
            api_md += ['', '']
            entry = module.__dict__[name]
            if entry.__doc__:
                md, sec = doc2md(entry.__doc__, name,
                        min_level=level+2, more_info=True, toc=False)
                api_sec += sec
                api_md += md

    sections += api_sec

    # headline
    md = [
        make_heading(level, title),
        "",
        lines.pop(0),
        ""
    ]

    # main sections
    if toc:
        md += make_toc(sections)
    md += _doc2md(lines)

    # API section
    md += [
        '',
        '',
        make_heading(level+1, title_api_section),
    ]
    if toc:
        md += ['']
        md += make_toc(api_sec)
    md += api_md

    return "\n".join(md)
