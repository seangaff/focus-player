import time
import threading
from just_playback import Playback
from session import Session
import os
# import pygame
# import pygame.midi
# import mido

class Player:
    def __init__(self, session):
        self.session = session

        self.foreground_playback = Playback()
        self.background_playback = Playback()
        self.alert_playback = Playback()
        
        self.load_default_tracks()

        self.mode = "adaptive" # "background", "adaptive"
        
        # Volume state
        self.background_volume = 1.0
        self.foreground_volume = 0.0
        self.target_background_volume = 1.0
        self.target_foreground_volume = 0.0
        
        self.is_playing = False
        self.smoothing_step = 0.05 # Volume change per update

    def play_alert(self):
        self.alert_playback.play()

    def load_default_tracks(self):
        foreground_path = self.get_abs_path(self.session.config["player"]["foreground"]["folder"], self.session.config["player"]["foreground"]["default_song"])
        background_path = self.get_abs_path(self.session.config["player"]["background"]["folder"], self.session.config["player"]["background"]["default_song"])
        
        self.load_track(self.foreground_playback, foreground_path)
        self.load_track(self.background_playback, background_path)
        self.load_track(self.alert_playback, self.session.config["player"]["alert_sound"])

    def get_abs_path(self, folder, filename):
        return os.path.join(os.path.expanduser(folder), filename)

    def load_track(self, playback: Playback, path: str):
        try:
            playback.load_file(path)
        except Exception as e:
            print(f"Error loading track: {e}")

    # def load_tracks(self, ambience_path=None, music_path=None):
    #     if ambience_path:
    #         try:
    #             self.background_playback.load_file(ambience_path)
    #             self.background_playback.loop_at_end(True)
    #             print(f"Loaded ambience: {ambience_path}")
    #         except Exception as e:
    #             print(f"Error loading ambience: {e}")
        
    #     if music_path:
    #         try:
    #             self.foreground_playback.load_file(music_path)
    #             self.foreground_playback.loop_at_end(True)
    #             print(f"Loaded music: {music_path}")
    #         except Exception as e:
    #             print(f"Error loading music: {e}")

    def play(self):
        if not self.is_playing:
            # Just call play(), just_playback handles if no file is loaded (usually safe, or we can add try/except)
            # But better to rely on our own loaded state if we had one. 
            # For now, let's just call play() and catch potential errors if needed, 
            # but just_playback.play() is generally safe if empty.
            try:
                self.background_playback.play()
            except:
                pass
                
            try:
                self.foreground_playback.play()
            except:
                pass

            self.is_playing = True
            self.update_volumes()

    def stop(self):
        if self.is_playing:
            self.background_playback.stop()
            self.foreground_playback.stop()
            self.alert_playback.stop()
            self.is_playing = False

    def tick(self):
        """
        Reads data from session to determine target intensity, 
        then smooths volumes towards target.
        """
        # Calculate intensity based on session WPM
        wpm = self.session.current_wpm
        # Cap at 100 WPM for max intensity, mapping 0-100 to 0.0-1.0
        intensity = min(max(wpm / 100.0, 0.0), 1.0)
        
        # Music volume scales with intensity
        self.target_foreground_volume = intensity
        
        self.update_volumes()

    def update_volumes(self):
        """
        Smoothly transitions current volumes to target volumes.
        Should be called periodically.
        """
        # Smooth music volume
        if self.foreground_volume < self.target_foreground_volume:
            self.foreground_volume = min(self.foreground_volume + self.smoothing_step, self.target_foreground_volume)
        elif self.foreground_volume > self.target_foreground_volume:
            self.foreground_volume = max(self.foreground_volume - self.smoothing_step, self.target_foreground_volume)
            
        # Ambience volume scales inversely
        self.background_volume = 1.0 - self.foreground_volume

        # Apply volumes
        # We set volume regardless of active state so it's ready when it starts or if it's playing
        self.foreground_playback.set_volume(self.foreground_volume)
        self.background_playback.set_volume(self.background_volume)

    def get_progress(self):
        """Returns progress info for tracks."""
        return {
            "ambience": {
                "current": self.background_playback.curr_pos,
                "total": self.background_playback.duration
            },
            "music": {
                "current": self.foreground_playback.curr_pos,
                "total": self.foreground_playback.duration
            }
        }

    def cleanup(self):
        self.stop()
        # if self.midi_player:
        #     del self.midi_player
        #     pygame.midi.quit()
        #     pygame.quit()


if __name__ == "__main__":
    session = Session("../sampleConfig.toml")
    player = Player(session)
    player.play_alert()
    time.sleep(10)
    # player.stop()
    

