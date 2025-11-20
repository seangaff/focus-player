import pygame
import pygame.midi
from pynput import keyboard
import mido

class TypingMusicPlayer:
    def __init__(self, midi_file_path):
        """
        Initialize the music player with a MIDI file.
        
        Args:
            midi_file_path: Path to the .mid file
        """
        pygame.init()
        pygame.midi.init()
        
        self.player = pygame.midi.Output(0)
        self.player.set_instrument(0)  # Piano
        
        # Load MIDI file and extract notes
        self.notes = self.load_midi_notes(midi_file_path)
        self.current_index = 0
        
        print(f"Loaded {len(self.notes)} notes from {midi_file_path}")
        
    def load_midi_notes(self, midi_file_path):
        """
        Extract note information from a MIDI file.
        
        Returns:
            List of tuples: [(note_number, velocity, duration), ...]
        """
        mid = mido.MidiFile(midi_file_path)
        notes = []
        
        # Merge all tracks
        for msg in mid:
            if msg.type == 'note_on' and msg.velocity > 0:
                # Store note number, velocity, and a default duration
                notes.append({
                    'note': msg.note,
                    'velocity': msg.velocity,
                    'duration': 200  # milliseconds
                })
        
        return notes
    
    def play_next_note(self):
        """Play the next note in the sequence"""
        if self.current_index < len(self.notes):
            note_info = self.notes[self.current_index]
            note = note_info['note']
            velocity = note_info['velocity']
            duration = note_info['duration']
            
            # Play the note
            self.player.note_on(note, velocity)
            pygame.time.wait(duration)
            self.player.note_off(note, velocity)
            
            self.current_index += 1
            
            # Loop back to start if we reach the end
            if self.current_index >= len(self.notes):
                print("\nReached end of song, looping back to start...")
                self.current_index = 0
    
    def on_key_press(self, key):
        """Callback for key press events"""
        # Stop on ESC key
        if key == keyboard.Key.esc:
            return False
        
        self.play_next_note()
    
    def start_listening(self):
        """Start listening for keyboard input"""
        print("Start typing to play the song...")
        print("Press ESC to stop")
        print(f"Progress: 0/{len(self.notes)} notes")
        
        with keyboard.Listener(on_press=self.on_key_press) as listener:
            listener.join()
    
    def cleanup(self):
        """Clean up resources"""
        del self.player
        pygame.midi.quit()
        pygame.quit()


# Example usage
if __name__ == "__main__":
    # Replace with your MIDI file path
    midi_file = "/Users/seangaffney/Downloads/Evangelion - Cruel Angel's Thesis.mid"
    
    player = TypingMusicPlayer(midi_file)
    
    try:
        player.start_listening()
    except KeyboardInterrupt:
        print("\nStopping...")
    except FileNotFoundError:
        print(f"Error: Could not find MIDI file '{midi_file}'")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        player.cleanup()