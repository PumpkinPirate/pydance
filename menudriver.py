# Code to construct pyDDR's menus

import pygame, menus, os, sys, copy, colors

from constants import *
from announcer import Announcer
from gfxtheme import GFXTheme
from songselect import SongSelect
from endless import Endless

# A simple on/off setting, 1 or 0
def get_onoff(name):
  if mainconfig[name]: return None, "on"
  else: return None, "off"

def switch_onoff(name):
  mainconfig[name] ^= 1
  return get_onoff(name)

def on_onoff(name):
  mainconfig[name] = 1
  return get_onoff(name)

def off_onoff(name):
  mainconfig[name] = 0
  return get_onoff(name)

# A simple on/off setting, 0 or 1
def get_offon(name):
  if mainconfig[name]: return None, "off"
  else: return None, "on"

def switch_offon(name):
  mainconfig[name] ^= 1
  return get_offon(name)

def on_offon(name):
  mainconfig[name] = 0
  return get_offon(name)

def off_offon(name):
  mainconfig[name] = 1
  return get_offon(name)

# Rotate through a list of option strings
def get_rotate(name, list):
  return None, mainconfig[name]

def switch_rotate(name, list):
  try:
    new_i = (list.index(mainconfig[name]) + 1) % len(list)
    mainconfig[name] = list[new_i]
  except ValueError: mainconfig[name] = list[0]
  return get_rotate(name, list)

def switch_rotate_back(name, list):
  try:
    new_i = (list.index(mainconfig[name]) - 1) % len(list)
    mainconfig[name] = list[new_i]
  except ValueError: mainconfig[name] = list[-1]
  return get_rotate(name, list)

# Rotate through a list of option strings, but use the index as the value.
def get_rotate_index(name, list):
  return None, list[mainconfig[name]]

def switch_rotate_index(name, list):
  mainconfig[name] = (mainconfig[name] + 1) % len(list)
  return get_rotate_index(name, list)

def switch_rotate_index_back(name, list):
  mainconfig[name] = (mainconfig[name] - 1) % len(list)
  return get_rotate_index(name, list)

def fullscreen_toggle(dummy):
  mainconfig["fullscreen"] ^= 1
  pygame.display.toggle_fullscreen()
  return None, None

def get_tuple(name, list):
  for item in list:
    if item[0] == mainconfig[name]:
      return None, item[1]
  return None, "custom: " + str(mainconfig[name])

def switch_tuple(name, list):
  next = False
  orig = mainconfig[name]
  for item in list:
    if next:
      mainconfig[name] = item[0]
      next = False
      break
    elif item[0] == mainconfig[name]:
      next = True
  if next: mainconfig[name] = list[0][0]
  elif mainconfig[name] == orig: mainconfig[name] = list[0][0]  
  return get_tuple(name, list)

def switch_tuple_back(name, list):
  list = copy.copy(list)
  list.reverse()
  return switch_tuple(name, list)

# Wrap an object constructor
def wrap_ctr(Obj, args):
  Obj(*args)
  return None, None

def do(screen, songdata):

  onoff_opt = { E_START: switch_onoff, E_CREATE: get_onoff,
                 E_LEFT: off_onoff, E_RIGHT: on_onoff }
  offon_opt = { E_START: switch_offon, E_CREATE: get_offon,
                 E_LEFT: off_offon, E_RIGHT: on_offon }
  rotate_opt = { E_START: switch_rotate,
                 E_LEFT: switch_rotate_back,
                 E_RIGHT: switch_rotate,
                 E_CREATE: get_rotate }
  rotate_index_opt = { E_START: switch_rotate_index,
                       E_LEFT: switch_rotate_index_back,
                       E_RIGHT: switch_rotate_index,
                       E_CREATE: get_rotate_index }
  tuple_opt = { E_START: switch_tuple,
                E_LEFT: switch_tuple_back,
                E_RIGHT: switch_tuple,
                E_CREATE: get_tuple }

  m = (("Play Game",
        ["Regular", {E_START: wrap_ctr}, (SongSelect, songdata)],
        ["Endless", {E_START: wrap_ctr}, (Endless, songdata)],
        ["Oni Mode", tuple_opt, ('maxonilife',
                                 [(0, 'off'), (3, 'three lives'),
                                  (4, 'four lives'), (5, 'five lives'),
                                  (7, 'seven lives'), (9, 'nine lives')])],
        ["Back", None, None]
        ),
       ("Game Options",
        ("Handicaps",
         ["Autofail", onoff_opt, ("autofail",)],
         ["Assist Mode", onoff_opt, ("assist",)],
         ["Jumps", offon_opt, ("badknees",)],
         ["Little", rotate_index_opt,
          ("little", ("show all", "no 16ths", "no 8ths",
                      "no 8ths or 16ths"))],
        ["Back", None, None]
         ),
        ["Arrow Colors", tuple_opt, ('arrowcolors', [(0, 'flat'),
                                                     (4, 'normal')])],
        ["Hidden", rotate_index_opt,
         ("hidden", ("off", "hide one","hide two","hide three"))],
        ["Sudden", rotate_index_opt,
         ("sudden", ("off", "hide one", "hide two", "hide three"))],
        ["Top Arrows", onoff_opt, ("showtoparrows",)],
        ["Scale Arrows", rotate_index_opt,
         ("arrowscale", ("shrink", "normal", "grow"))],
        ["Scrolling", rotate_index_opt, ("scrollstyle",
                                         ("normal", "reverse", "center"))],
        ["Arrow Speed", rotate_opt, ('scrollspeed', [0.25, 0.5, 1, 1.5,
                                                     2, 4, 8])],
        ["Back", None, None]
        ),
       ("Graphic Options",
        ["Arrow Effects", rotate_index_opt,
         ('explodestyle', ('none', 'rotate', 'scale', 'rotate & scale'))],
        ["Spin Arrows", onoff_opt, ("arrowspin",)],
        ["Backgrounds", onoff_opt, ('showbackground',)],
        ["Brightness", tuple_opt, ('bgbrightness',
                                   [(32, 'very dark'),
                                    (64, 'dark'),
                                    (127, 'normal'),
                                    (192, 'bright'),
                                    (255, 'very bright')])],
        ["Lyrics", onoff_opt, ("showlyrics",)],
        ["Lyrics Color", rotate_opt, ("lyriccolor",
                                     ["pink/purple", "purple/cyan",
                                      "cyan/aqua", "aqua/yellow",
                                      "yellow/pink"])],
        ["Back", None, None]
        ),
       ("Interface Options",
        ["Theme", rotate_opt, ('gfxtheme', GFXTheme.themes())],
        ["Announcer", rotate_opt, ('djtheme', Announcer.themes())],
        ["Song Previews", onoff_opt, ('previewmusic',)],
        ["Sort By", rotate_index_opt,
         ("sortmode", ["file", "title", "artist", "bpm", "mix"])],
        ["Timer Display", onoff_opt, ('fpsdisplay',)],
        ["Gratuitous Extras", onoff_opt, ('gratuitous',)],
        ["Display Help", onoff_opt, ("ingamehelp",)],
        ["Back", None, None]
        ),
       ["Quit", None, None]
       )

  me = menus.Menu("Main Menu", m, screen)
  me.display()
