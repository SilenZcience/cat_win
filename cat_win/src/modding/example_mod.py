"""
example mod
place me in the ~mods folder inside the
config directory to see how modding works
"""

# --- import modding support ---
from cat_win.src.modding import *

# --- create a new argument constant for the example mod ---
argconst.ALL_ARGS.append(
    ArgConstant(
        '--lol', '--lol', 'show this help message and exit',
        999999, section=222
    ),
)
# --- register a pre-hook for the example mod ---
@register_pre(999999)
def example_mod(ctx) -> bool:
    print('[example_mod2] hook fired!')
    return False

# --- overwrite an existing post-hook for the example mod ---
@register_post(ARGS_SUM)
def example_mod(ctx) -> bool:
    print('[example_mod1] hook fired!')
    return False
