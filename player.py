# -*- encoding: UTF-8 -*-

#
#
# - **GET `/play/http://sounds.com/example.ogg`**      : download and play
# - **GET `/loop/http://sounds.com/example-loop.ogg`** : download and play this sound as loop
#
#

import os
import sys
import time
import logging
import urllib
import urllib2
from cStringIO import StringIO
import pygame

from bottle import route, run, static_file


SUCCESS = {'success': True}
ERROR = {'success': False}

LOOP_VOLUME_HIGH     = 0.5
LOOP_VOLUME_LOW      = 0 # while another sound is playing
FX_VOLUME            = 1

HTTP_TIMEOUT         = 30

# logging setup
FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT
)
log = logging.getLogger(__name__)


loop_sound = None
fx_sound = None

# cache to speed up next plays
CACHE={}

def get_sound_from_url(url):
  return (urllib2.urlopen(url, timeout=HTTP_TIMEOUT).read())

def play_sound(url, loops=0, volume=None, on_ready=None):
  log.info('play_sound #{0} {1}'.format(loops, url))
  key = url

  if not key in CACHE:
    sound = pygame.mixer.Sound(StringIO(get_sound_from_url(url)))
    CACHE[key] = sound

  sound = CACHE.get(key)

  if on_ready:
    on_ready()
  if volume:
    log.info('set_volume {0} {1}'.format(volume, url))
    sound.set_volume(volume)
  sound.play(loops=loops)
  return sound

def start_loop(url):
  global loop_sound
  log.info('start loop {0}'.format(url))
  if loop_sound:
    loop_sound.stop()
    loop_sound = None
  loop_sound = play_sound(url, loops=-1, volume=LOOP_VOLUME_HIGH)

def set_loop_volume(volume):
  log.info('set_loop_volume {0}'.format(volume))
  global loop_sound
  if loop_sound:
    loop_sound.set_volume(volume)

def play_url(url):
  global fx_sound
  log.info('play_url {0}'.format(url))

  def on_ready():
    set_loop_volume(LOOP_VOLUME_LOW)
    time.sleep(0.5)

  if fx_sound:
    fx_sound.stop()

  fx_sound = play_sound(url, volume=FX_VOLUME, on_ready=on_ready)

  # wait end before changing sound again (prevent overlaps)
  wait_timeout = min(100, fx_sound.get_length())
  log.info('wait {0}'.format(wait_timeout))
  time.sleep(wait_timeout)
  set_loop_volume(LOOP_VOLUME_HIGH)


#
# SERVER
#

def fix_path(sound_path):
  parts = sound_path.split('/')
  return '/'.join(parts[:-1]) + '/' + urllib.pathname2url(parts[-1])

@route('/play/<sound:path>')
def play(sound):
    log.info('play sound {0}'.format(sound))
    play_url(fix_path(sound))
    return static_file('pixel.gif', '.')

@route('/loop/<sound:path>')
def loop(sound):
    log.info('loop sound {0}'.format(sound))
    start_loop(fix_path(sound))
    return static_file('pixel.gif', '.')


@route('/debug')
def debug():
    return {
      'fx': fx_sound and fx_sound.get_volume() or None,
      'loop': loop_sound and loop_sound.get_volume() or None
    }


if __name__ == '__main__':

  os.environ["SDL_VIDEODRIVER"] = "dummy"

  pygame.mixer.init()

  if len(sys.argv) > 1:
    loop_url = sys.argv[1]
    try:
      start_loop(loop_url)
    except Exception, e:
      log.exception('invalid loop_url ' + loop_url)
      log.exception(e)

  log.info('RUNNING on port 8082')
  run(host='0.0.0.0', port=8082, server='cherrypy')
