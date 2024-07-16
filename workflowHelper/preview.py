#!/usr/bin/python
import os
from PIL import Image, ImageFont, ImageDraw, ImageColor

WIDTH, HEIGHT = 1280, 640
OFFSET = 75

COLOR_BACKGROUND = ImageColor.getcolor('#1A1A1A', mode = 'RGB')

COLOR_LINE_INDEX = ImageColor.getcolor('#73DA12', mode = 'RGB')
COLOR_LINE_LENGTH = ImageColor.getcolor('#9CDCFE', mode = 'RGB')
COLOR_TEXT = ImageColor.getcolor('#D3D7CF', mode = 'RGB')

KEYWORDS = [
    ('cat', ImageColor.getcolor('#CC0000', mode = 'RGB')),
    ('SilenZcience', ImageColor.getcolor('#CC00AB', mode = 'RGB')),
    ('Python', ImageColor.getcolor('#3e6cd6', mode = 'RGB')),
    ('Text-Processing', ImageColor.getcolor('#ffa500', mode = 'RGB')),
    ('-Analytics', ImageColor.getcolor('#ffa500', mode = 'RGB')),
]


script_dir = os.path.dirname(__file__)
init_path  = os.path.abspath(os.path.join(script_dir, '..', 'cat_win', '__init__.py'    ))
font_path  = os.path.abspath(os.path.join(script_dir, 'CaskaydiaCove Nerd Font Mono.otf'))
img_path   = os.path.abspath(os.path.join(script_dir, '..', 'img', 'socialPreview.png'  ))

text = ''
with open(init_path, 'r', encoding='utf-8') as iFile:
    text = iFile.readlines()
text = ["__sysversion__ = '3.6 - 3.12'" if t.startswith('__sysversion__') else t.rstrip()
        for t in text]

LINE_INDEX_LENGTH = len(str(len(text)))
LINE_LENGTH_LENGTH = len(str(max(map(len, text))))


def add_horinzontal_element(element, pos, _text, color, font):
    element.text(pos, _text, fill=color, font=font)
    x_1, _, x_2, _ = editPreview.textbbox(xy=pos, text=_text, font=font)
    return x_2 - x_1


def _highlight_all_keywords(element, pos, _text, font, step):
    _x_pos, _y_pos = pos
    if step >= len(KEYWORDS) or step < 0:
        _x_pos += add_horinzontal_element(editPreview, (_x_pos, _y_pos), _text, COLOR_TEXT, textFont)
        return _x_pos
    keyword, color = KEYWORDS[step]
    line_split = _text.split(keyword)
    _x_pos = _highlight_all_keywords(element, (_x_pos, _y_pos), line_split[0], font, step+1)
    for line_part in line_split[1:]:
        _x_pos += add_horinzontal_element(editPreview, (_x_pos, _y_pos), keyword, color, textFont)
        _x_pos = _highlight_all_keywords(editPreview, (_x_pos, _y_pos), line_part, textFont, step+1)
    return _x_pos


def highlight_all_keywords(element, pos, _text, font):
    _highlight_all_keywords(element, pos, _text, font, 0)


preview = Image.new(mode = 'RGB', size = (WIDTH, HEIGHT), color = COLOR_BACKGROUND)

editPreview = ImageDraw.Draw(preview, mode = 'RGB')
textFont = ImageFont.truetype(font_path, 21)

_, y_1, _, y_2 = editPreview.textbbox(xy=(0, 0), text='WIPpQqy"^._', font=textFont)
spacing = (y_2-y_1) + 5

y_pos = (HEIGHT - spacing * len(text)) // 2

for index, line in enumerate(text, start=1):
    x_pos = OFFSET
    line_index = f"{index: >{LINE_INDEX_LENGTH}}) "
    x_pos += add_horinzontal_element(editPreview, (x_pos, y_pos), line_index, COLOR_LINE_INDEX, textFont)
    line_length = f"[{len(line): >{LINE_LENGTH_LENGTH}}] "
    x_pos += add_horinzontal_element(editPreview, (x_pos, y_pos), line_length, COLOR_LINE_LENGTH, textFont)
    highlight_all_keywords(editPreview, (x_pos, y_pos), line, textFont)
    y_pos += spacing


preview.save(img_path)
