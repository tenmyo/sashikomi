#!/usr/bin/env python
# vi: fenc=utf-8 ff=unix et sw=4 sts=4 tw=80
#
# zlib License
#
# Copyright (C) 2017 TENMYO Masakazu
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.

import argparse
import collections
import csv
import enum
import io
import os
import re
import shutil
import sys

TokenKind = enum.Enum('TokenKind', ('STRING',
                                    'VARIABLE_OPEN',
                                    'VARIABLE_CLOSE',
                                    'COMMAND_OPEN',
                                    'COMMAND_CLOSE'))


Token = collections.namedtuple('Token', ('kind', 'fpath', 'value'))


def tokenize(fpath: str, text):
    token_spec = [
        ('ESCAPE', r'\$\$'),
        ('VARIABLE_OPEN', r'\${'),
        ('VARIABLE_CLOSE', r'\}'),
        ('COMMAND_OPEN', r'\$\('),
        ('COMMAND_CLOSE', r'\)'),
        ('STRING', r'[^$})]+'),
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_spec)
    for mo in re.finditer(tok_regex, text):
        kind = mo.lastgroup
        value = mo.group(kind)
        if kind == 'ESCAPE':
            kind = 'STRING'
            value = '$'
        yield Token(TokenKind[kind], fpath, value)


class BaseNode:
    def __init__(self, fpath: str):
        self.nodes = []
        self.fpath = fpath

    def eval(self, reps: dict) -> str:
        return ''.join(node.eval(reps) for node in self.nodes)


class FileNode(BaseNode):
    def __init__(self, fpath: str, tokens):
        super().__init__(fpath)
        for token in tokens:
            if token.kind == TokenKind.STRING:
                self.nodes.append(StringNode(self.fpath, token.value))
            elif token.kind == TokenKind.VARIABLE_OPEN:
                self.nodes.append(VariableNode(self.fpath, tokens))
            elif token.kind == TokenKind.VARIABLE_CLOSE:
                self.nodes.append(StringNode(self.fpath, token.value))
            elif token.kind == TokenKind.COMMAND_OPEN:
                self.nodes.append(CommandNode(self.fpath, tokens))
            elif token.kind == TokenKind.COMMAND_CLOSE:
                self.nodes.append(StringNode(self.fpath, token.value))


class VariableNode(BaseNode):
    def __init__(self, fpath: str, tokens):
        super().__init__(fpath)
        for token in tokens:
            if token.kind == TokenKind.STRING:
                self.nodes.append(StringNode(self.fpath, token.value))
            elif token.kind == TokenKind.VARIABLE_OPEN:
                self.nodes.append(VariableNode(self.fpath, tokens))
            elif token.kind == TokenKind.VARIABLE_CLOSE:
                break
            elif token.kind == TokenKind.COMMAND_OPEN:
                self.nodes.append(CommandNode(self.fpath, tokens))
            elif token.kind == TokenKind.COMMAND_CLOSE:
                self.nodes.append(StringNode(self.fpath, token.value))

    def eval(self, reps: dict) -> str:
        text = super().eval(reps).strip()
        return reps[text]


class CommandNode(BaseNode):
    def __init__(self, fpath: str, tokens):
        super().__init__(fpath)
        for token in tokens:
            if token.kind == TokenKind.STRING:
                self.nodes.append(StringNode(self.fpath, token.value))
            elif token.kind == TokenKind.VARIABLE_OPEN:
                self.nodes.append(VariableNode(self.fpath, tokens))
            elif token.kind == TokenKind.VARIABLE_CLOSE:
                self.nodes.append(StringNode(self.fpath, token.value))
            elif token.kind == TokenKind.COMMAND_OPEN:
                self.nodes.append(CommandNode(self.fpath, tokens))
            elif token.kind == TokenKind.COMMAND_CLOSE:
                break

    def eval(self, reps: dict) -> str:
        texts = super().eval(reps).strip().split(maxsplit=1)
        command = texts[0].strip()
        if len(texts) > 1:
            args = texts[1]
        else:
            args = ""
        if command == "include":
            return self.cmd_include(reps, args)
        return command + args

    def cmd_include(self, reps: dict, args: str) -> str:
        incpath = os.path.join(os.path.dirname(self.fpath), args.strip())
        with open(incpath) as f:
            return read_template(self.fpath, f).eval(reps)


class StringNode(BaseNode):
    def __init__(self, fpath: str, text: str):
        super().__init__(fpath)
        self.nodes.append(text)

    def eval(self, reps: dict) -> str:
        return self.nodes[0]


def read_template(fpath: str, f: io.TextIOBase) -> BaseNode:
    return FileNode(fpath, tokenize(fpath, f.read()))


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('in_tmpl', help='template file')
    parser.add_argument('in_csv', help='parameter csv file')
    parser.add_argument('out_dir', help='output directory')
    parser.add_argument('--clean',
                        help='crean directory before output',
                        action='store_true')
    parser.add_argument('--fname',
                        help='column name of output filename. default __n',
                        default='__n')
    parser.add_argument('-w', '--overwrite',
                        help='overwrite to output file',
                        action='store_true')
    args = parser.parse_args(argv)

    if args.clean:
        if os.path.exists(args.out_dir):
            shutil.rmtree(args.out_dir)

    os.makedirs(args.out_dir, exist_ok=True)

    if args.overwrite:
        writetype = 'w'
    else:
        writetype = 'a'

    with open(args.in_tmpl) as tmplfile:
        rootnode = read_template(args.in_tmpl, tmplfile)

    with open(args.in_csv, newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            header = tuple(row)
            break
        for (n, row) in enumerate(csvreader):
            d = collections.defaultdict(str, zip(header, row))
            d['__n'] = str(n)
            out_fpath = os.path.join(args.out_dir, d[args.fname])
            with open(out_fpath, writetype) as outfile:
                outfile.write(rootnode.eval(d))


if __name__ == '__main__':
    main(sys.argv[1:])
