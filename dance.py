# This is the main loop, which passes events to the Player objects.

import pygame
from constants import *

from pad import pad

from util import toRealTime
from player import Player
from announcer import Announcer

from pygame.sprite import RenderUpdates

from pygame.mixer import music
import fontfx
import gradescreen
import steps
import fileparsers
import games
import error
import colors
import records

import os

# A simple movie-playing sprite. It can only do MPEG1 though.
class BGMovie(pygame.sprite.Sprite):
  def __init__ (self, filename):
    pygame.sprite.Sprite.__init__(self)
    self.filename = filename
    self.image = pygame.surface.Surface([640, 480])
    
    self.movie = pygame.movie.Movie(filename)
    self.movie.set_display(self.image,[[0, 0], [640, 480]])
    self.rect = self.image.get_rect()
    self.rect.top = 0
    self.rect.left = 0
    self.oldframe = -1
    self.changed = False
    
  def resetchange(self):
    self.changed = False

  def update(self,curtime):
    curframe = int(curtime * 29.97)
    if self.oldframe != curframe:
      self.changed = True
      self.movie.render_frame(curframe)
      self.oldframe = curframe

# Display the current FPS and store the average FPS for the song.
class FPSDisp(pygame.sprite.Sprite):
  def __init__(self):
    pygame.sprite.Sprite.__init__(self)
    self.image = pygame.surface.Surface([1, 1])
    self._oldtime = -10000000
    self._clock = pygame.time.Clock()
    self._cycles = 0
    self._totalcount = 0
    self._font = FONTS[16]

  # Return the average of the average FPS rather than just the average
  # FPS. This avoids the average FPS shooting up incredibly fast at
  # the end of the song when no arrows are left.
  def fps(self):
    return self._totalcount / self._cycles

  def update(self, time):
    self._clock.tick()

    loops = int(self._clock.get_fps())
    self._totalcount += loops
    self._cycles += 1

    if (time - self._oldtime) > 1:
      text = "%d fps" % loops
      self.image = self._font.render(text, True, [160, 160, 160])
      self.rect = self.image.get_rect()
      self.rect.bottom = 480
      self.rect.right = 640
      self._oldtime = time

# Puts a little blinking square in the bottom corner, for use with
# a custom lighting setup. This doesn't deal with BPM changes correctly.
class Blinky(pygame.sprite.Sprite):
  def __init__ (self, bpm):
    pygame.sprite.Sprite.__init__(self)
    self.tick = toRealTime(bpm, 0.5)
    self.frame = 0
    self.oldframe = -100
    self.topimg = []
    
    im = pygame.surface.Surface([48, 40])
    im.fill([1, 1, 1])
    self.topimg.append(im.convert())
    self.topimg.append(im.convert())

    im.fill([255, 255, 255])
    for i in range(2):          
      self.topimg.append(im.convert())

    self.image = self.topimg[3]
    self.rect = self.image.get_rect()
    self.rect.top = 440
    self.rect.left = 592

  def update(self, time):
    self.frame = int(time / self.tick) % 8
    if self.frame > 3: self.frame = 3

    if self.frame != self.oldframe:
      self.image = self.topimg[self.frame]
      self.oldframe = self.frame

# Display the time at the top of the screen, in seconds.
class TimeDisp(pygame.sprite.Sprite):
  def __init__(self):
    pygame.sprite.Sprite.__init__(self)
    self._oldtime = -1
    self.image = pygame.surface.Surface([1, 1])
    self.rect = self.image.get_rect()
    self.rect.top = 0
    self.rect.centerx = 320
    self._font = FONTS[32]

  def update(self, time):
    if (time - self._oldtime) > 0.1: # Update 10 times a second at most
      time_str = "%0.1f" % time
      self.image = self._font.render(time_str, True, [224, 224, 224])
      self._oldtime = time
      self.rect = self.image.get_rect()
      self.rect.top = 0
      self.rect.centerx = 320

# The "Ready? Go!" that appears before most songs.
class ReadyGoSprite(pygame.sprite.Sprite):
  def __init__(self, time):
    pygame.sprite.Sprite.__init__(self)
    ready = os.path.join(pydance_path, "images", "ready.png")
    go = os.path.join(pydance_path, "images", "go.png")
    self._time = time
    self._ready = pygame.image.load(ready).convert()
    self._ready.set_colorkey(self._ready.get_at([0, 0]), RLEACCEL)
    self._go = pygame.image.load(go).convert()
    self._go.set_colorkey(self._go.get_at([0, 0]), RLEACCEL)
    self._pick_image(min(0, time))

  def update(self, cur_time):
    if cur_time > self._time: self.kill()
    elif self.alive(): self._pick_image(cur_time)

  def _pick_image(self, cur_time):
    ttl = self._time - cur_time # time to live
    if ttl < 0.25:
      self.image = self._go
      alpha = ttl / 0.25
    elif ttl < 0.750:
      self.image = self._go
      alpha = 1
    elif ttl < 1.00:
      self.image = self._go
      alpha = (1 - ttl) / 0.25
    elif ttl < 1.5:
      self.image = self._ready
      alpha = (ttl - 1.0) / 0.5
    elif cur_time < 0.5:
      self.image = self._ready
      alpha = cur_time / 0.5
    else:
      self.image = self._ready
      alpha = 1

    self.image.set_alpha(int(256 * alpha))
    self.rect = self.image.get_rect()
    self.rect.center = (320, 240)

# Run through a playlist of songs and play each one until people quit.
def play(screen, playlist, configs, songconf, playmode):
  numplayers = len(configs)

  game = games.GAMES[playmode]

  songs_played = 0
  # Decides whether or not the Ready?/Go! should be displayed before
  # the song.
  first = True

  songdata = None

  players = []
  for playerID in range(numplayers):
    plr = Player(playerID, configs[playerID], songconf, game)
    players.append(plr)

  for songfn, diff in playlist:
    try: current_song = fileparsers.SongItem(songfn)
    except None:
      error.ErrorMessage(screen, "There was an error loading " +
                         os.path.split(songfn)[1])
      first = True
      continue

    songs_played += 1
    pygame.mixer.quit()
    prevscr = pygame.transform.scale(screen, (640,480))
    songdata = steps.SongData(current_song, songconf)

    for pid in range(len(players)):
      players[pid].set_song(current_song, diff[pid], songdata.lyricdisplay)

    print "Playing", songfn
    print songdata.title.encode("ascii", "replace"), "by",
    print songdata.artist.encode("ascii", "replace")

    if dance(screen, songdata, players, prevscr, first, game):
      first = False
      break # Failed
    first = False
    if True in [p.escaped for p in players]:
      break

  if mainconfig['grading'] and not first and songdata:
    grade = gradescreen.GradingScreen(screen, players, songdata.banner)

  # If we only play one song (all the way through), then it's safe to enter
  # a grade. This means course grades are going to get kind of messy,
  # and have to be handled by the course stuff rather than here.
  if songs_played == 1 and not players[0].escaped:
    for p in players:
      if not p.failed:
        records.add(current_song.info["recordkey"], diff[p.pid],
                    playmode, p.grade.rank(), " ")
      else:
        records.add(current_song.info["recordkey"], diff[p.pid],
                    playmode, -2, " ")

def dance(screen, song, players, prevscr, ready_go, game):
  songFailed = False

  pygame.mixer.init()

  # text group, e.g. judgings and combos
  tgroup =  RenderUpdates()
  # lyric display group
  lgroup = RenderUpdates()

  background = pygame.Surface([640, 480])

  if song.movie != None:
    backmovie = BGMovie(song.movie)
  else:
    backmovie = None
    
  background.fill(colors.BLACK)
  screen.fill(colors.BLACK)

  if ready_go:
    ready_go_time = min(100, *[plr.ready for plr in players])
    tgroup.add(ReadyGoSprite(ready_go_time))

  if mainconfig['showbackground'] > 0:
    if backmovie is None:
      bgkludge = pygame.image.load(song.background).convert()
      bgkrect = bgkludge.get_rect()
      if (bgkrect.size[0] == 320) and (bgkrect.size[1] == 240):
        bgkludge = pygame.transform.scale2x(bgkludge)
      else:
        bgkludge = pygame.transform.scale(bgkludge, [640, 480])
      bgkludge.set_alpha(mainconfig['bgbrightness'], RLEACCEL)
      
      q = mainconfig['bgbrightness'] / 256.0
      # FIXME
      for i in range(0, 101, 5):
        p = i / 100.0
        prevscr.set_alpha(256 * (1 - p) * q, RLEACCEL)
        screen.fill(colors.BLACK)
        screen.blit(prevscr, [0, 0])
        screen.blit(bgkludge, [0, 0])
        pygame.display.update()
        pygame.time.delay(1)

      background.blit(bgkludge, [0, 0])
    else:
      pygame.display.update()
  else:
    pygame.display.update()

  if mainconfig["strobe"]: tgroup.add(Blinky(song.bpm))

  if mainconfig["fpsdisplay"]:
    fpstext = FPSDisp()
    timewatch = TimeDisp()
    tgroup.add([fpstext, timewatch])
  else: fpstext = None

  if mainconfig['showlyrics']:
    lgroup.add(song.lyricdisplay.channels())

  songtext = fontfx.zztext(song.title, 480, 12)
  grptext = fontfx.zztext(song.artist, 160, 12)

  songtext.zin()
  grptext.zin()

  tgroup.add([songtext, grptext])

  song.init()

  if song.crapout != 0:
    error.ErrorMessage(screen, "The audio file for this song " +
                       song.filename + " could not be found.")
    return False # The player didn't fail.

  if mainconfig['assist']: music.set_volume(0.6)
  else: music.set_volume(1.0)

  song.play()
  for plr in players: plr.start_song()

  autofail = mainconfig['autofail']

  screenshot = False
  pad.empty()

  while True:
    if autofail:
      songFailed = True
      for plr in players:
        if not plr.lifebar.gameover:
          songFailed = False
          break
      if songFailed:
        song.kill()

    for plr in players: plr.get_next_events(song)

    if song.is_over(): break
    else: curtime = music.get_pos()/1000.0

    key = []

    ev = pad.poll()

    for i in range(len(players)):
      if (pad.states[(i, pad.START)] and pad.states[(i, pad.SELECT)]):
        ev = (0, pad.QUIT)
        break
      else:
        pass

    while ev[1] != pad.PASS:
      if ev[1] == pad.QUIT:
        for p in players: p.escaped = True
        break
      elif ev[1] == pad.SCREENSHOT:
        screenshot = True
      elif ev[1] == pad.LEFT: key.append((ev[0], 'l'))
      elif ev[1] == pad.DOWNLEFT: key.append((ev[0], 'w'))
      elif ev[1] == pad.UPLEFT: key.append((ev[0], 'k'))
      elif ev[1] == pad.RIGHT: key.append((ev[0], 'r'))
      elif ev[1] == pad.UPRIGHT: key.append((ev[0], 'z'))
      elif ev[1] == pad.DOWNRIGHT: key.append((ev[0], 'g'))
      elif ev[1] == pad.UP: key.append((ev[0], 'u'))
      elif ev[1] == pad.DOWN: key.append((ev[0], 'd'))
      elif ev[1] == pad.CENTER: key.append((ev[0], 'c'))

      ev = pad.poll()

    if ev[1] == pad.QUIT: return False
  
    for ev in key:
      if game.double: pid = ev[0] / 2
      else: pid = ev[0]
      
      if pid < len(players): players[pid].handle_key(ev, curtime)

    rectlist = []

    if backmovie:
      backmovie.update(curtime)
      if backmovie.changed or (fpstext.fps() > 30):
        backmovie.resetchange()
        screen.blit(backmovie.image, [0, 0])

    for plr in players: rectlist.extend(plr.game_loop(curtime, screen))

    lgroup.update(curtime)
    tgroup.update(curtime)
    rectlist.extend(tgroup.draw(screen))
    rectlist.extend(lgroup.draw(screen))

    if backmovie is None: pygame.display.update(rectlist)
    else: pygame.display.update()

    if screenshot:
      fn = os.path.join(rc_path, "screenshot.bmp")
      print "Saving a screenshot to", fn
      pygame.image.save(screen, fn)
      screenshot = False

    if backmovie is None:
      lgroup.clear(screen, background)
      tgroup.clear(screen, background)
      for plr in players: plr.clear_sprites(screen, background)

    if ((curtime > players[0].length - 1) and
        (songtext.zdir == 0) and (songtext.zoom > 0)):
      songtext.zout()
      grptext.zout()

  if fpstext: print "Average FPS for this song was %d." % fpstext.fps()
  return songFailed
