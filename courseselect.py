import os
import math
import pygame
import fontfx
import colors
import ui
import records
import grades
import dance
import random
import util
import options

from constants import *
from interface import *
from courses import CRSFile
from pygame.mixer import music

NO_BANNER = os.path.join(image_path, "no-banner.png")

DIFF_COLORS = { "BEGINNER": colors.color["white"],
                "LIGHT": colors.color["orange"],
                "EASY": colors.color["orange"],
                "BASIC": colors.color["orange"],
                "STANDARD": colors.color["red"],
                "STANDER": colors.color["red"], # Shit you not, 3 people.
                "TRICK": colors.color["red"],
                "MEDIUM": colors.color["red"],
                "DOUBLE": colors.color["red"],
                "ANOTHER": colors.color["red"],
                "PARA": colors.color["blue"],
                "NORMAL": colors.color["red"],
                "MANIAC": colors.color["green"],
                "HARD": colors.color["green"],
                "HEAVY": colors.color["green"],
                "HARDCORE": colors.color["purple"],
                "SMANIAC": colors.color["purple"],
                "S-MANIAC": colors.color["purple"], # Very common typo
                "CHALLENGE": colors.color["purple"],
                "CRAZY": colors.color["purple"],
                "EXPERT": colors.color["purple"]
                }

SORTS = {
  "title": (lambda x, y: (cmp(x.name.lower(),
                              y.name.lower()))),
  "mix": (lambda x, y: (cmp(str(x.mixname).lower(),
                            str(y.mixname).lower()) or
                        SORTS["title"](x, y)))
  }

SORT_NAMES = ["mix", "title"]

NUM_SORTS = len(SORT_NAMES)

CS_HELP = [
  "Up / Down: Change song selection",
  "Left / Right: Change difficulty setting",
  "Enter / Up Right: Open a folder or start a course",
  "Escape / Up Left: Close a folder or exit",
  "Tab / Select: Go to a random course",
  "Start: Switch to Options screen",
  "F11: Toggle fullscreen - S: Change the sort mode",
  ]

def folder_name(name, type):
  if type == "mix": return name
  else: return "%s: %s" % (type.capitalize(), name)

def load_banner(filename):
  banner = pygame.image.load(filename)
  size = banner.get_size()
  if size <= (100, 100): # Parapara-style... no idea what to do.
    return banner, None
  elif size == (177, 135): # KSF-style 1
    return banner, None
  elif size == (300, 200): # KSF-style 2
    banner.set_colorkey(banner.get_at([0, 0]), RLEACCEL)
    return banner, None
  elif abs(size[0] - size[1]) < 3: # "Square", need to rotate.
    banner = banner.convert()
    banner.set_colorkey(banner.get_at([0, 0]), RLEACCEL)
    return pygame.transform.rotozoom(banner, -45, 1.0), [51, 50, 256, 80]
  else: # 256x80, standard banner, I hope.
    if size != (256, 80): banner = pygame.transform.scale(banner, [256, 80])
    return banner, None

class CourseDisplay(object):
  no_banner = pygame.image.load(NO_BANNER)
  no_banner.set_colorkey(no_banner.get_at([0, 0]))

  def __init__(self, course, recordkeys, game): # A CRSFile object
    self.banner_fn = course.banner
    self.course = course
    self.mixname = course.mixname
    self.name = course.name
    self.banner = None
    self.isfolder = False
    self.folder = {}
    self.banner = None
    self.clip = None
    self._songs = []
    self.generate_songlist(recordkeys, game)

  # Note that we don't need to worry about player's best/worst/etc changing
  # while playing courses, since per-song records don't change.
  def generate_songlist(self, recordkeys, game):
    i = 1
    for name, diff, mods in self.course.songs:
      if "*" in name: name, subtitle = "??????????", ""
      elif name[0] == "BEST":
        song = recordkeys.get(records.best(name[1], diff, game))
        if song:
          subtitle = (song.info["subtitle"] or "") + (" (Best #%d)" % name[1])
          name = song.info["title"]
        else:
          name = "Player's Best Unavailable"
          subtitle = "(You need to play more songs!)"

      elif name[0] == "WORST":
        song = recordkeys.get(records.best(name[1], diff, game))
        if song:
          subtitle = (song.info["subtitle"] or "") + (" (Worst #%d)" % name[1])
          name = song.info["title"]
        else:
          name = "Player's Worst Unavailable"
          subtitle = "(You need to play more songs!)"

      elif name[0] == "LIKES":
        song = recordkeys.get(records.like(name[1], diff, game))
        if song:
          subtitle = (song.info["subtitle"] or "") + (" (Likes #%d)" % name[1])
          name = song.info["title"]
        else:
          name = "Player's Likes Unavailable"
          subtitle = "(You need to play more songs!)"

      elif name[0] == "DISLIKES":
        song = recordkeys.get(records.dislike(name[1], diff, game))
        if song:
          subtitle = (song.info["subtitle"] or "") + (" (Dislikes #%d)" % name[1])
          name = song.info["title"]
        else:
          name = "Player's Dislikes Unavailable"
          subtitle = "(You need to play more songs!)"

      else: name, subtitle = util.find_subtitle(name.split("/")[-1])

      if "." in diff: diff = "?"

      name = ("%d. " % i) + name
      self._songs.append([name, subtitle, diff])
      i += 1

  def render(self):
    if self.banner: return
    font = fontfx.WrapFont(28, 320)
    small_font = fontfx.WrapFont(18, 250)
    ls = font.get_linesize()
    y = ls * 3
    for name, subtitle, diff in self._songs:
      y += font.lines(name, indent = "    ") * ls
      y += font.lines(subtitle, indent = "    ") * (ls / 4)

    self.image = pygame.Surface([340, y], SRCALPHA, 32)
    self.image.fill([0, 0, 0, 0])

    y_off = 0
    for i in range(len(self._songs)):
      t3 = None
      name, subtitle, diff = self._songs[i]
      t1 = font.render(name, color = colors.WHITE, indent = "    ")
      if subtitle:
        t3 = small_font.render(subtitle, color = [190, 190, 190],
                               indent = "    ")

      if isinstance(diff, list): d = diff[0]
      else: d = diff
      t2 = fontfx.shadow(d[0], 28, DIFF_COLORS.get(d, colors.WHITE))

      r1 = t1.get_rect()
      r2 = t2.get_rect()
      r1.top = r2.top = y_off
      r1.left = 0
      r2.right = 340
      y_off += t1.get_height()
      self.image.blit(t1, r1)
      self.image.blit(t2, r2)

      if t3:
        r3 = t3.get_rect()
        r3.left = 30
        ls = small_font.get_linesize()
        r3.top = y_off - 3 * ls / 4
        y_off += ls / 4
        self.image.blit(t3, r3)

    if self.banner_fn and os.path.exists(self.banner_fn):
      self.banner, self.clip = load_banner(self.banner_fn)
    else: self.banner = CourseDisplay.no_banner

class FolderDisplay(object):
  def __init__(self, name, type, count):
    self.name = name
    self.fullname = folder_name(name, type)
    self._type = type
    self.isfolder = True
    self.banner = None
    self.clip = None
    self.info = {}
    self.mixname = "%d songs" % count
    self.image = pygame.Surface([0, 0])

  def render(self):
    if self.banner: return

    name = self.name.encode("ascii", "ignore")
    for path in [rc_path, pydance_path]:
      filename = os.path.join(path, "banners", self._type, name+".png")
      if os.path.exists(filename):
        self.banner, self.clip = load_banner(filename)
        break

    else:
      if self._type == "mix":
        for dir in mainconfig["coursedir"].split(os.pathsep):
          dir = os.path.expanduser(dir)
          fn = os.path.join(dir, self.name + ".png")
          if os.path.exists(fn): self.banner, self.clip = load_banner(fn)

    if self.banner == None: self.banner = CourseDisplay.no_banner

class CourseSelector(InterfaceWindow):
  def __init__(self, songs, courses, screen, game):
    InterfaceWindow.__init__(self, screen, "courseselect-bg.png")

    recordkeys = dict([(k.info["recordkey"], k) for k in songs])

    self._courses = [CourseDisplay(c, recordkeys, game) for c in courses]
    self._all_courses = self._courses
    self._index = 0
    self._clock = pygame.time.Clock()
    self._game = game
    self._config = dict(game_config)
    self._configs = []

    self._list = ListBox(pygame.font.Font(None, 28),
                         [255, 255, 255], 32, 10, 256, [373, 150])
    if len(self._courses) > 60 and mainconfig["folders"]:
      self._create_folders()
      self._create_folder_list()
    else:
      self._folders = None
      self._base_text = "All Courses"
      self._courses.sort(SORTS[SORT_NAMES[mainconfig["sortmode"] % NUM_SORTS]])
      self._list.set_items([s.name for s in self._courses])

    self._course = self._courses[self._index]
    self._course.render()

    players = games.GAMES[game].players

    for i in range(players):
      self._configs.append(dict(player_config))

    ActiveIndicator([368, 306], height = 32, width = 266).add(self._sprites)
    HelpText(CS_HELP, [255, 255, 255], [0, 0, 0], pygame.font.Font(None, 20),
             [186, 20]).add(self._sprites)

    self._list_gfx = ScrollingImage(self._course.image, [15, 80], 390)
    self._coursetitle = TextDisplay(28, [345, 28], [20, 56])
    self._title = TextDisplay(30, [240, 28], [377, 27])
    self._banner = ImageDisplay(self._course.banner, [373, 56])
    self._sprites.add([self._list, self._list_gfx, self._title,
                       self._coursetitle, self._banner])
    self._screen.blit(self._bg, [0, 0])
    pygame.display.update()
    self.loop()
    music.fadeout(500)
    pygame.time.wait(500)
    # FIXME Does this belong in the menu code? Probably.
    music.load(os.path.join(sound_path, "menu.ogg"))
    music.set_volume(1.0)
    music.play(4, 0.0)
    player_config.update(self._configs[0]) # Save p1's settings

  def loop(self):
    pid, ev = ui.ui.poll()
    root_idx = 0
    self._list.set_index(self._index)
    self._title.set_text(self._base_text + " - %d/%d" % (self._index + 1,
                                                         len(self._courses)))
    while not (ev == ui.CANCEL and (not self._folders or self._course.isfolder)):
      if pid >= len(self._configs): pass # Inactive player
      
      elif ev == ui.UP: self._index -= 1
      elif ev == ui.DOWN: self._index += 1

      elif ev == ui.SELECT:
        self._index = random.randrange(len(self._courses))

      elif ev == ui.SORT:
        s = self._courses[self._index]
        mainconfig["sortmode"] = (mainconfig["sortmode"] + 1) % NUM_SORTS
        if self._folders:
          if s.isfolder:
            self._create_folder_list()
          else:
            self._create_course_list(s.folder[SORT_NAMES[mainconfig["sortmode"]]])
            self._index = self._courses.index(s)
        else:
          self._courses.sort(SORTS[SORT_NAMES[mainconfig["sortmode"]]])
          self._index = self._courses.index(s)
          self._list.set_items([s.name for s in self._courses])

      elif ev == ui.START:
        options.OptionScreen(self._configs, self._config, self._screen)
        self._screen.blit(self._bg, [0, 0])
        self.update()
        pygame.display.update()

      elif ev == ui.CONFIRM:
        if self._course.isfolder:
          self._create_course_list(self._course.name)
          root_idx = self._index
          self._index = 0
        else:
          music.fadeout(500)
          course = self._course.course
          course.setup(self._screen, self._configs, self._config, self._game)
          dance.play(self._screen, course, self._configs,
                     self._config, self._game)
          course.done()
          music.fadeout(500) # The just-played song
          self._screen.blit(self._bg, [0, 0])
          pygame.display.update()
          ui.ui.empty()
          ui.ui.clear()

      elif ev == ui.CANCEL:
        self._create_folder_list()
        self._index = root_idx

      elif ev == ui.FULLSCREEN:
        pygame.display.toggle_fullscreen()
        mainconfig["fullscreen"] ^= 1

      self._index %= len(self._courses)
      self._course = self._courses[self._index]

      if ev in [ui.CANCEL, ui.UP, ui.DOWN, ui.SELECT, ui.CONFIRM, ui.SORT]:
        if ev == ui.UP: self._list.set_index(self._index, -1)
        elif ev == ui.DOWN: self._list.set_index(self._index, 1)
        else: self._list.set_index(self._index, 0) # don't animate
        self._course.render()
        self._coursetitle.set_text(self._course.name)
        self._banner.set_image(self._course.banner)
        self._list_gfx.set_image(self._course.image)
        self._title.set_text(self._base_text + " - %d/%d" % (self._index + 1,
                                                             len(self._courses)))
      self.update()
      pid, ev = ui.ui.poll()

  def _create_folders(self):
    mixes = {}
    titles = {}

    for s in self._all_courses:
      if s.mixname not in mixes: mixes[s.mixname] = []
      mixes[s.mixname].append(s)
      s.folder["mix"] = s.mixname

      label = s.name[0].capitalize()
      if label not in titles: titles[label] = []
      titles[label].append(s)
      s.folder["title"] = label

    self._folders = { "mix": mixes, "title": titles }

  def _create_folder_list(self):
    sort = SORT_NAMES[mainconfig["sortmode"] % NUM_SORTS]
    lst = self._folders[sort].keys()
    lst.sort(lambda x, y: cmp(x.lower(), y.lower()))
    new_courses = [FolderDisplay(folder, sort,
                                 len(self._folders[sort][folder])) for
                   folder in lst]
    self._courses = new_courses
    self._list.set_items([s.fullname for s in self._courses])
    
    self._base_text = "Sort by %s" % sort.capitalize()
    
  def _create_course_list(self, folder):
    sort = SORT_NAMES[mainconfig["sortmode"] % NUM_SORTS]
    courselist = self._folders[sort][folder]
    courselist.sort(SORTS[sort])

    self._courses = courselist
    self._list.set_items([s.name for s in self._courses])
    self._base_text = folder_name(folder, sort)
