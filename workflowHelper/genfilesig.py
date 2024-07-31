#!/usr/bin/python
"""
generate the file signature (magic number) database (json) using the wikipedia table
https://github.com/gambolputty/wikitable2csv?tab=readme-ov-file trim cells and include line breaks
https://en.wikipedia.org/wiki/List_of_file_signatures
"""


import mimetypes
import csv
import json

mimetypes.init()

with open('./cat_win/res/signatures.json', 'r', encoding='utf-8') as sig:
    signatures = json.load(sig)

new_signatures = {}

with open('sig.csv', 'r', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for i, row in enumerate(csv_reader):
        if i == 0:
            continue
        hex_sig, _, offset, ext, desc = row
        if not hex_sig or not offset or not offset.isdigit():
            # print('INVALID: ', f"{repr(ext)};{repr(desc)}")
            continue
        if not ext:
            print("WARNING: ", f"{repr(desc)}")
            ext = desc
        hex_sig = hex_sig.replace('\u00a0', ' ').upper().split('\n')
        for i in range(len(hex_sig)-1, -1, -1):
            if '(' in hex_sig[i]:
                hex_sig[i] = hex_sig[i][:hex_sig[i].find('(')]
        hex_sig = ''.join(hex_sig).split(' ')
        for i in range(len(hex_sig)-1, -1, -1):
            if len(hex_sig[i]) == 4:
                hex_sig[i] = hex_sig[i][:2] + '\n' + hex_sig[i][2:]
        hex_sig = ''.join(hex_sig).split('\n')

        hex_sig = [f"{offset},{hs}" for hs in hex_sig]

        for ex in ext.split('\n'):
            if ex in new_signatures:
                new_signatures[ex]['signs'] += hex_sig.copy()
            else:
                new_signatures[ex] = {'signs': hex_sig.copy(),
                                        'mime': ex}

for ext, sig in new_signatures.items():
    if sig['mime'] == ext:
        try:
            sig['mime'] = mimetypes.types_map[f".{ext}"]
        except KeyError:
            if ext in signatures:
                sig['mime'] = signatures[ext]['mime']

for ext, sig in signatures.items():
    if ext not in new_signatures:
        new_signatures[ext] = sig

print("Old Length:", len(signatures))
print("New Length:", len(new_signatures))

with open('signatures.json', 'w', encoding='utf-8') as json_file:
    json.dump(new_signatures, json_file, indent=4, separators=(',',': '))
