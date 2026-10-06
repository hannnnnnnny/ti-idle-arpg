"""Regenerate the README screenshots and clips in docs/media.

    sh tools/build_host.sh && python tools/media/make_media.py   (project root)

Everything is rendered by the game itself through the headless runner
(build/ad_headless), frame by frame, at the calculator's 320x240 and shown
2x. Needs Pillow.
"""
import glob
import os
import shutil
import subprocess
import sys

from PIL import Image

RUNNER = os.path.join('build', 'ad_headless.exe' if os.name == 'nt' else 'ad_headless')
OUT = os.path.join('docs', 'media')
TMP = os.path.join('build', 'media_tmp')
SCALE = 2
ZH = ['--lang', '1']

# New game through the title, the save slot, class select and creation,
# into act I with its subtitles.
DOWN8 = ' '.join(['D:2 -:6'] * 8)
NEW_GAME = f'-:60 O:2 -:40 O:2 -:40 O:2 -:60 {DOWN8} O:2 -:330'
MENU_TOUR = '-:40 T:2 -:40 T:2 -:40 T:2 -:40 T:2 -:40 T:2 -:40 T:2 -:40 T:2 -:40'

CLIPS = [
    # name, runner args, (first tick, frames, ticks per frame), ms per frame
    ('gameplay', ['--new', '--class', '0', '--fast', '0.25'] + ZH + ['--script', '-:300'], (0, 125, 2), 66),
    ('new_game', ['--save', os.path.join(TMP, 'fresh.sav')] + ZH + ['--script', NEW_GAME], (40, 126, 5), 140),
    ('menus', ['--new', '--class', '1', '--fast', '1.5'] + ZH + ['--script', MENU_TOUR], (36, 80, 4), 160),
    ('late_game', ['--new', '--class', '2', '--fast', '120'] + ZH + ['--script', '-:400'], (30, 110, 3), 100),
    # the three signature builds, wearing their build-defining uniques
    ('meta_storm_werewolf', ['--new', '--class', '4', '--preset', '2', '--fast', '0.6', '--sig'] + ZH
     + ['--script', '-:600'], (180, 120, 3), 100),
    ('meta_bone_spear', ['--new', '--class', '3', '--preset', '0', '--fast', '0.5', '--sig'] + ZH
     + ['--script', '-:1100'], (640, 120, 3), 100),
    ('meta_inferno', ['--new', '--class', '1', '--preset', '0', '--fast', '0.4', '--sig'] + ZH
     + ['--script', '-:500'], (20, 120, 3), 100),
]

SHOTS = [
    # name, runner args, tick
    ('title', ['--save', os.path.join(TMP, 'fresh.sav')] + ZH + ['--script', '-:60'], 50),
    ('battle', ['--new', '--class', '3', '--fast', '0.5'] + ZH + ['--script', '-:200'], 150),
    ('hero', ['--new', '--class', '3', '--fast', '1.5'] + ZH + ['--script', '-:40 T:2 -:30'], 70),
    ('skills', ['--new', '--class', '1', '--fast', '1.5'] + ZH + ['--script', '-:40 T:2 -:5 T:2 -:5 T:2 -:30'], 80),
    ('paragon', ['--new', '--class', '4', '--fast', '3'] + ZH + ['--script', '-:40 T:2 -:5 T:2 -:5 T:2 -:5 T:2 -:30'], 85),
    ('town', ['--new', '--class', '0', '--fast', '1.5'] + ZH + ['--script', '-:40 T:2 -:5 T:2 -:5 T:2 -:5 T:2 -:5 T:2 -:30'], 95),
    ('goals', ['--new', '--class', '5', '--fast', '6'] + ZH + ['--script', '-:40' + ' T:2 -:5' * 6 + ' -:30'], 105),
]

LANG_SHOTS = [(lang, ['--new', '--class', '2', '--fast', '0.5', '--lang', str(lang), '--script', '-:40 T:2 -:30'], 70)
              for lang in range(5)]


def run(args):
    r = subprocess.run([RUNNER] + args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f'runner failed: {" ".join(args)}\n{r.stderr}')


def scaled(path):
    im = Image.open(path).convert('RGB')
    return im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)


def make_gif(name, frames, ms):
    palette = frames[len(frames) // 2].quantize(colors=255, method=Image.MEDIANCUT)
    q = [f.quantize(palette=palette, dither=Image.NONE) for f in frames]
    path = os.path.join(OUT, f'{name}.gif')
    q[0].save(path, save_all=True, append_images=q[1:], duration=ms, loop=0, optimize=True)
    print(f'{path}: {len(frames)} frames, {os.path.getsize(path) // 1024} KB')


def clip(name, args, rec, ms):
    prefix = os.path.join(TMP, name + '_')
    run(args + ['--record', f'{rec[0]}:{rec[1]}:{rec[2]}:{prefix}'])
    make_gif(name, [scaled(f) for f in sorted(glob.glob(prefix + '*.png'))], ms)


def shot(name, args, tick):
    path = os.path.join(TMP, name + '.png')
    run(args + ['--shot', f'{tick}:{path}'])
    scaled(path).save(os.path.join(OUT, name + '.png'))
    return path


def languages():
    tiles = [scaled(shot(f'lang{lang}', args, tick)) for lang, args, tick in LANG_SHOTS]
    for lang in range(5):
        os.remove(os.path.join(OUT, f'lang{lang}.png'))
    w, h = tiles[0].size
    sheet = Image.new('RGB', (w * 3 + 16, h * 2 + 8), (12, 8, 12))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 3) * (w + 8), (i // 3) * (h + 8)))
    sheet.save(os.path.join(OUT, 'languages.png'))


def main():
    shutil.rmtree(TMP, ignore_errors=True)
    os.makedirs(TMP)
    os.makedirs(OUT, exist_ok=True)
    for c in CLIPS:
        clip(*c)
    for s in SHOTS:
        shot(*s)
    languages()
    shutil.rmtree(TMP, ignore_errors=True)


if __name__ == '__main__':
    main()
