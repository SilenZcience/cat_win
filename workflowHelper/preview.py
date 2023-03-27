#!/usr/bin/python
from PIL import Image, ImageFont, ImageDraw, ImageColor
import os

width, height = 1280, 640
offset = 75

color_Background = ImageColor.getcolor('#1A1A1A', mode = 'RGB')

color_LineIndex = ImageColor.getcolor('#73DA12', mode = 'RGB')
color_LineLength = ImageColor.getcolor('#9CDCFE', mode = 'RGB')
color_Text = ImageColor.getcolor('#D3D7CF', mode = 'RGB')

keyWords = [
    ('cat', ImageColor.getcolor('#CC0000', mode = 'RGB')),
    ('SilenZcience', ImageColor.getcolor('#CC00AB', mode = 'RGB')),
    ('Python', ImageColor.getcolor('#3e6cd6', mode = 'RGB'))
]


script_dir = os.path.dirname(__file__)
init_path  = os.path.abspath(os.path.join(script_dir, '..', 'cat_win', '__init__.py'    ))
font_path  = os.path.abspath(os.path.join(script_dir, 'CaskaydiaCove Nerd Font Mono.otf'))
img_path   = os.path.abspath(os.path.join(script_dir, '..', 'img', 'socialPreview.png'  ))

text = ''
with open(init_path, 'r', encoding='utf-8') as iFile:
    text = iFile.readlines()
text = [t.rstrip() for t in text]

lineIndexLength = len(str(len(text)))
lineLengthLength = len(str(max(map(len, text))))


def addHorinzontalElement(element, pos, text, color, font):
    element.text(pos, text, fill=color, font=font)
    x_1, _, x_2, _ = editPreview.textbbox(xy=pos, text=text, font=font)
    return (x_2-x_1)
    

def _highlightAllKeywords(element, pos, text, font, step):
    x_pos, y_pos = pos
    if step >= len(keyWords) or step < 0:
        x_pos += addHorinzontalElement(editPreview, (x_pos, y_pos), text, color_Text, textFont)
        return x_pos
    keyword, color = keyWords[step]
    lineSplit = text.split(keyword)
    x_pos = _highlightAllKeywords(element, (x_pos, y_pos), lineSplit[0], font, step+1)
    for linePart in lineSplit[1:]:
        x_pos += addHorinzontalElement(editPreview, (x_pos, y_pos), keyword, color, textFont)
        x_pos = _highlightAllKeywords(editPreview, (x_pos, y_pos), linePart, textFont, step+1)
    return x_pos
    

def highlightAllKeywords(element, pos, text, font):
    _highlightAllKeywords(element, pos, text, font, 0)
    

preview = Image.new(mode = 'RGB', size = (width, height), color = color_Background)

editPreview = ImageDraw.Draw(preview, mode = 'RGB')
textFont = ImageFont.truetype(font_path, 21)

_, y_1, _, y_2 = editPreview.textbbox(xy=(0, 0), text='WIPpQqy"^._', font=textFont)
spacing = (y_2-y_1) + 5

y_pos = (height - spacing * len(text)) // 2

for index, line in enumerate(text, start=1):
    x_pos = offset
    line_index = f"{index: >{lineIndexLength}}) "
    x_pos += addHorinzontalElement(editPreview, (x_pos, y_pos), line_index, color_LineIndex, textFont)
    line_length = f"[{len(line): >{lineLengthLength}}] "
    x_pos += addHorinzontalElement(editPreview, (x_pos, y_pos), line_length, color_LineLength, textFont)
    highlightAllKeywords(editPreview, (x_pos, y_pos), line, textFont)
    y_pos += spacing


preview.save(img_path)
