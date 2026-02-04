import time
import threading
from just_playback import Playback
# import pygame
# import pygame.midi
# import mido

class Player:
    def __init__(self, session):
        self.session = session
        self.ambience_playback = Playback()
        self.music_playback = Playback()
        
        # self.midi_player = None
        # self.midi_notes = []
        # self.midi_index = 0
        
        self.mode = "adaptive" # "background", "adaptive"
        
        # Volume state
        self.ambience_volume = 1.0
        self.music_volume = 0.0
        self.target_ambience_volume = 1.0
        self.target_music_volume = 0.0
        
        self.is_playing = False
        self.smoothing_step = 0.05 # Volume change per update

    def load_tracks(self, ambience_path=None, music_path=None):
        if ambience_path:
            try:
                self.ambience_playback.load_file(ambience_path)
                self.ambience_playback.loop_at_end(True)
                print(f"Loaded ambience: {ambience_path}")
            except Exception as e:
                print(f"Error loading ambience: {e}")
        
        if music_path:
            try:
                self.music_playback.load_file(music_path)
                self.music_playback.loop_at_end(True)
                print(f"Loaded music: {music_path}")
            except Exception as e:
                print(f"Error loading music: {e}")

    def play(self):
        if not self.is_playing:
            # Just call play(), just_playback handles if no file is loaded (usually safe, or we can add try/except)
            # But better to rely on our own loaded state if we had one. 
            # For now, let's just call play() and catch potential errors if needed, 
            # but just_playback.play() is generally safe if empty.
            try:
                self.ambience_playback.play()
            except:
                pass
                
            try:
                self.music_playback.play()
            except:
                pass

            self.is_playing = True
            self.update_volumes()

    def stop(self):
        if self.is_playing:
            self.ambience_playback.stop()
            self.music_playback.stop()
            self.is_playing = False

    def set_intensity(self, intensity):
        """
        Sets the target volumes based on intensity (0.0 to 1.0).
        Intensity is roughly proportional to WPM.
        """
        intensity = max(0.0, min(1.0, intensity))
        
        # Music volume scales with intensity
        # If intensity is 0, music volume is 0.
        self.target_music_volume = intensity
        
        # Ambience volume scales inversely
        # self.target_ambience_volume = 1.0 - (intensity) 

    def update_volumes(self):
        """
        Smoothly transitions current volumes to target volumes.
        Should be called periodically.
        """
        # Smooth music volume
        if self.music_volume < self.target_music_volume:
            self.music_volume = min(self.music_volume + self.smoothing_step, self.target_music_volume)
        elif self.music_volume > self.target_music_volume:
            self.music_volume = max(self.music_volume - self.smoothing_step, self.target_music_volume)
            
        # Ambience volume scales inversely
        self.ambience_volume = 1.0 - self.music_volume

        # Apply volumes
        # We set volume regardless of active state so it's ready when it starts or if it's playing
        self.music_playback.set_volume(self.music_volume)
        self.ambience_playback.set_volume(self.ambience_volume)

    def get_progress(self):
        """Returns progress info for tracks."""
        return {
            "ambience": {
                "current": self.ambience_playback.curr_pos,
                "total": self.ambience_playback.duration
            },
            "music": {
                "current": self.music_playback.curr_pos,
                "total": self.music_playback.duration
            }
        }

    def cleanup(self):
        self.stop()
        # if self.midi_player:
        #     del self.midi_player
        #     pygame.midi.quit()
        #     pygame.quit()

