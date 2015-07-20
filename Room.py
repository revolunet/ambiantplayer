# -*- encoding: UTF-8 -*-

import os
import logging
import time
import pygame

import config
import utils

FORMAT = '%(asctime)-15s %(levelname)-6s %(message)s'
logging.basicConfig(format=FORMAT)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


# sounds[relative_path] = pygame.mixer.Sound(fullname)

class Room(object):
    loop_volume = config.default_loop_volume
    loop_volume_low = config.default_loop_volume_low
    fx_volume = config.default_sound_volume

    def __init__(self, loop_url):
        log.debug('Room.init')
        pygame.mixer.init()
        self.loop_channel = None
        self.preload_sounds()
        if loop_url:
            log.debug('Room start loop')
            self.loop_channel = self.play_sound(loop_url, volume=config.default_loop_volume, loops=-1)

    def preload_sound(self, local_path):
        sound = None
        if local_path.endswith('.ogg') and not local_path in self.sounds:
            sound = pygame.mixer.Sound(local_path)
            self.sounds[local_path] = sound
        return self.sounds.get(local_path)

    def preload_sounds(self):
        ''' preload cache_dir/*.ogg in memory fo faster play '''
        self.sounds = {}
        log.debug('Preload sounds')
        for root, dirs, files in os.walk(config.cache_dir):
            for name in files:
                local_path = os.path.join(config.cache_dir, name)
                self.preload_sound(local_path)
        log.debug('Preloaded %s sounds', len(self.sounds.keys()))
        #return sounds

    def set_loop_volume(self, volume):
        ''' adjust loop volume '''
        #print set_loop_volume
        log.debug('set_loop_volume: %s', volume)
        if self.loop_channel:
            self.loop_channel.set_volume(volume)
            return True
        else:
            return False

    def play_sound(self, sound_url, volume=config.default_sound_volume, loops=0, lower_loop_volume=False):
        ''' play given sound and lower loop volume if needed '''
        channel = None
        log.debug('play_sound %s', sound_url)
        # check if sound cached and download if not
        utils.cache_urls(sound_url)
        local_path = utils.url_to_local_path(sound_url)
        # load sound in pygame
        sound = self.preload_sound(local_path)

        if sound:
            # reduce loop volume
            if lower_loop_volume:
                self.set_loop_volume(config.default_loop_volume_low)
                time.sleep(0.5)

            # play sound channel
            if sound:
                channel = sound.play(loops = loops)
                # adjust sound volume
                #if loops != -1:
                channel.set_volume(volume)

            # restore loop volume
            if lower_loop_volume:
                if channel:
                    while channel.get_busy():
                        time.sleep(0.5)
                self.set_loop_volume(config.default_loop_volume)
        else:
            log.error('cannot play sound %s', sound_url)

        return channel
