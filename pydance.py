#! /usr/bin/env python
# pydance - Dancing game written in Python

#import psyco
#psyco.jit()
#from psyco.classes import *

import pygame
from constants import *

import fontfx, menudriver, fileparsers, audio, colors

import os, sys, random, operator, error, util, getopt, math

os.chdir(pydance_path)

def SetDisplayMode(mainconfig):
  try:
    flags = HWSURFACE | DOUBLEBUF
    if mainconfig["vesacompat"]: flags = 0
    elif mainconfig["fullscreen"]: flags |= FULLSCREEN
    screen = pygame.display.set_mode([640, 480], flags, 16)
  except:
    print "Can't get a 16 bit display!" 
    sys.exit()
  return screen

def main():
  print "pydance, by theGREENzebra (tgz@clickass.org)"
  print "Initialising.."

  if mainconfig["usepsyco"]:
    try:
      import psyco
      print "Psyco optimizing compiler found. Using psyco.full()."
      psyco.full()
    except ImportError: print "Psyco optimizing compiler not found."

  # FIXME Debug mode needs to be added again. Or some command line options.

  fileList = []
  for dir in mainconfig["songdir"].split(os.pathsep):
    print "Searching", dir
    fileList += util.find(dir, ['*.step', '*.dance', '*.dwi', '*.sm', '*/song.*']) # Python's matching SUCKS

  totalsongs = len(fileList)
  parsedsongs = 0
  songs = []

  screen = SetDisplayMode(mainconfig)
  
  pygame.display.set_caption('pydance ' + VERSION)
  pygame.mouse.set_visible(0)

  audio.load(os.path.join(sound_path, "menu.ogg"))
  audio.play(4, 0.0)

  pbar = fontfx.TextProgress(FONTS[60], "Found " + str(totalsongs) +
                             " files. Loading...", colors.WHITE, colors.BLACK)
  r = pbar.render(0).get_rect()
  r.center = (320, 240)
  for f in fileList:
    try: songs.append(fileparsers.SongItem(f, False))
    except RuntimeWarning, message:
      print "W:", message
    except RuntimeError, message:
      print "E:", message
    except:
      print "E: Unknown error loading " + f
      print "E: Please contact the developers (pydance-devel@icculus.org)."
    img = pbar.render(parsedsongs / totalsongs)
    pygame.display.update(screen.blit(img, r))
    parsedsongs += 100

  ev = event.poll()
  while ev[1] != E_PASS: ev = event.poll()

  if len(songs) < 1:
    error.ErrorMessage(screen,
                      ("You don't have any songs or step files. Check out",
                       "http://icculus.org/pyddr/get.php",
                       "and download some free ones."
                       " ", " ", " ",
                       "If you already have some, make sure they're in",
                       mainconfig["songdir"]))
    print "You don't have any songs. http://icculus.org/pyddr/get.php."
    sys.exit(1)

  menudriver.do(screen, (songs, screen))
  audio.stop()
  pygame.display.quit()
  mainconfig.write(os.path.join(rc_path, "pydance.cfg"))

if __name__ == '__main__': main()
