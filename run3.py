import tkinter as tk
from tkinter import filedialog, messagebox
import os
import mido
import pyautogui
import time
import threading
import keyboard

class MidiPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TROUBADOR MACRO")
        self.root.geometry("450x450")
        self.root.attributes('-topmost', True)
        self.pitch_value = 0
        self.file_path = ""
        self.play_thread = None
        self.is_playing = False
        self.imported_files = []
        self.file_path_dict = {}
        self.selected_item = None
        self.auto_play = False
        self.current_index = 0
        self.setup_ui()
        self.setup_hotkeys()

    def setup_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=1)
        self.root.columnconfigure(3, weight=0)
        self.root.rowconfigure(2, weight=1)

        # Title
        title_label = tk.Label(self.root, text="🎹 TROUBADOR MACRO", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Buttons
        self.open_file_button = tk.Button(self.root, text="📂 Import MIDI", command=self.open_file_dialog, 
                                          relief="solid", bd=1, bg="#FFFFFF", width=15)
        self.open_file_button.grid(row=1, column=0, padx=5, pady=5)

        self.simplify_button = tk.Button(self.root, text="✂️ Simplify", command=self.simplify_midi,
                                         relief="solid", bd=1, bg="#FFFFCC", width=10)
        self.simplify_button.grid(row=1, column=1, padx=5, pady=5)

        self.delete_button = tk.Button(self.root, text="♻️ Delete", command=self.delete_selected_item,
                                       relief="solid", bd=1, bg="#FFFFFF", width=10)
        self.delete_button.grid(row=1, column=2, padx=5, pady=5)

        self.stop_button = tk.Button(self.root, text="⏹️ Stop (F6)", command=self.stop_playing,
                                     relief="solid", bd=1, bg="#FFCCCC", width=12)
        self.stop_button.grid(row=1, column=3, padx=5, pady=5)

        # Listbox
        self.listbox = tk.Listbox(self.root, height=8, width=50)
        self.listbox.grid(row=2, column=0, padx=5, pady=5, sticky='nsew', columnspan=3)
        self.listbox.bind('<<ListboxSelect>>', self.on_listbox_select)
        self.listbox.bind('<Double-Button-1>', self.on_double_click)

        # Scrollbars
        v_scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.listbox.yview)
        v_scrollbar.grid(row=2, column=3, sticky='ns')
        self.listbox.config(yscrollcommand=v_scrollbar.set)

        # Pitch control
        pitch_frame = tk.Frame(self.root)
        pitch_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        pitch_label = tk.Label(pitch_frame, text="Pitch Shift:")
        pitch_label.pack(side=tk.LEFT, padx=5)

        self.spinbox = tk.Spinbox(pitch_frame, from_=-24, to=24, increment=1, width=8)
        self.spinbox.pack(side=tk.LEFT, padx=5)
        self.spinbox.delete(0, 'end')
        self.spinbox.insert(0, "0")

        # BPM Speed control
        speed_label = tk.Label(pitch_frame, text="Speed:")
        speed_label.pack(side=tk.LEFT, padx=10)

        self.speed_spinbox = tk.Spinbox(pitch_frame, from_=50, to=150, increment=5, width=6)
        self.speed_spinbox.pack(side=tk.LEFT, padx=5)
        self.speed_spinbox.delete(0, 'end')
        self.speed_spinbox.insert(0, "95")  # Default 95% (5% slower)
        
        speed_percent = tk.Label(pitch_frame, text="%")
        speed_percent.pack(side=tk.LEFT)

        # Auto-play checkbox
        self.auto_play_var = tk.BooleanVar()
        self.auto_play_check = tk.Checkbutton(self.root, text="Auto-play next", 
                                              variable=self.auto_play_var,
                                              command=self.toggle_auto_play)
        self.auto_play_check.grid(row=4, column=0, columnspan=3, pady=5)

        # Status labels
        self.status_label = tk.Label(self.root, text="Press F5 to play selected MIDI", 
                                     font=("Arial", 10), fg="blue")
        self.status_label.grid(row=5, column=0, columnspan=3, pady=5)

        self.file_label = tk.Label(self.root, text="", font=("Arial", 9, "italic"))
        self.file_label.grid(row=6, column=0, columnspan=3, pady=5)

        # Instructions
        info_text = "Hotkeys: F5 = Play | F6 = Stop | Double-click = Play"
        info_label = tk.Label(self.root, text=info_text, font=("Arial", 8), fg="gray")
        info_label.grid(row=7, column=0, columnspan=3, pady=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.load_saved_files()

    def setup_hotkeys(self):
        keyboard.add_hotkey('f5', self.hotkey_play)
        keyboard.add_hotkey('f6', self.hotkey_stop)

    def hotkey_play(self):
        if not self.is_playing:
            self.start_playing()

    def hotkey_stop(self):
        self.stop_playing()

    def toggle_auto_play(self):
        self.auto_play = self.auto_play_var.get()
        print(f"Auto-play: {self.auto_play}")

    def on_double_click(self, event):
        if not self.is_playing:
            self.start_playing()

    def open_file_dialog(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid *.midi")])
        if self.file_path and self.file_path not in self.imported_files:
            try:
                midi = mido.MidiFile(self.file_path)
                file_name = os.path.basename(self.file_path)
                self.imported_files.append(self.file_path)
                self.file_path_dict[file_name] = self.file_path
                self.save_files()
                self.load_saved_files()
                messagebox.showinfo("Success", f"Added: {file_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid MIDI file: {e}")

    def delete_selected_item(self):
        selected_indices = self.listbox.curselection()
        if selected_indices:
            index = selected_indices[0]
            selected_item = self.listbox.get(index).split(' - ', 1)[1]
            confirm = messagebox.askyesno("Confirm", f"Delete '{selected_item}'?")
            if confirm:
                file_path = self.file_path_dict.get(selected_item)
                if file_path in self.imported_files:
                    self.imported_files.remove(file_path)
                del self.file_path_dict[selected_item]
                self.save_files()
                self.load_saved_files()

    def save_files(self):
        with open('midi_files.txt', 'w', encoding='utf-8') as file:
            for item in self.imported_files:
                file.write(item + '\n')

    def load_saved_files(self):
        self.listbox.delete(0, "end")
        self.file_path_dict.clear()
        try:
            with open('midi_files.txt', 'r', encoding='utf-8') as file:
                existing_files = [line.strip() for line in file]
            unique_files = list(set(existing_files))
            unique_files.sort(key=lambda x: os.path.basename(x).lower())
            
            for idx, file_path in enumerate(unique_files, start=1):
                file_name = os.path.basename(file_path)
                self.listbox.insert(tk.END, f" {idx} - {file_name}")
                self.imported_files.append(file_path)
                self.file_path_dict[file_name] = file_path
                
            with open('midi_files.txt', 'w', encoding='utf-8') as file:
                file.write('\n'.join(unique_files))
        except FileNotFoundError:
            pass

    def simplify_midi(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select a MIDI file first!")
            return
        
        selected_item = self.listbox.get(selected_indices[0]).split(' - ', 1)[1]
        file_path = self.file_path_dict.get(selected_item)
        
        if not file_path:
            return
        
        try:
            midi = mido.MidiFile(file_path)
            new_midi = mido.MidiFile()
            
            for track in midi.tracks:
                new_track = mido.MidiTrack()
                new_midi.tracks.append(new_track)
                
                last_note_time = 0
                current_time = 0
                active_notes = []
                min_interval = 50  # Minimum ticks between notes
                
                for msg in track:
                    current_time += msg.time
                    
                    # Keep all non-note messages (tempo, control, etc)
                    if msg.type not in ['note_on', 'note_off']:
                        new_track.append(msg.copy())
                        continue
                    
                    # Skip notes that are too close together (fast runs/ornaments)
                    if msg.type == 'note_on' and msg.velocity > 0:
                        if current_time - last_note_time < min_interval:
                            continue  # Skip this note
                        
                        # Limit simultaneous notes to 3 max
                        if len(active_notes) >= 3:
                            continue  # Skip if already 3 notes playing
                        
                        active_notes.append(msg.note)
                        last_note_time = current_time
                        new_track.append(msg.copy())
                    
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        if msg.note in active_notes:
                            active_notes.remove(msg.note)
                        new_track.append(msg.copy())
            
            # Save simplified version
            base_name = os.path.splitext(file_path)[0]
            simplified_path = f"{base_name}_SIMPLE.mid"
            new_midi.save(simplified_path)
            
            # Add to library
            if simplified_path not in self.imported_files:
                self.imported_files.append(simplified_path)
                file_name = os.path.basename(simplified_path)
                self.file_path_dict[file_name] = simplified_path
                self.save_files()
                self.load_saved_files()
            
            messagebox.showinfo("Success", f"Simplified! Saved as:\n{os.path.basename(simplified_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to simplify: {e}")

    def on_listbox_select(self, event):
        selected_indices = self.listbox.curselection()
        if selected_indices:
            self.selected_item = self.listbox.get(selected_indices[0]).split(' - ', 1)[1]
            self.file_label.config(text=f"Selected: {self.selected_item}")
            self.current_index = selected_indices[0]

    def map_piano_note_to_key(self, note):
        piano_G = ['f1', 'f2', 'f3']
        piano_keymap = ['q', '1', 'w', '2', 'e', 'r', '3', 't', '4', 'y', '5',
                        'u', 'i', '6', 'o', '7', 'p', '[', '8', ']', '9', '\\', '0', '-', '=']
        if not (36 <= note <= 96):
            return '', ''

        if 36 <= note <= 59:
            change_G = piano_G[0]
            baseline = 36
        elif 60 <= note <= 83:
            change_G = piano_G[1]
            baseline = 60
        else:
            change_G = piano_G[2]
            baseline = 84
        
        key_index = note - baseline
        if 0 <= key_index < len(piano_keymap):
            return change_G, piano_keymap[key_index]
        return '', ''

    def play_midi(self):
        if not self.selected_item:
            return
            
        file_path = self.file_path_dict.get(self.selected_item)
        if not file_path:
            return

        try:
            self.pitch_value = int(self.spinbox.get())
            speed_percent = int(self.speed_spinbox.get()) / 100.0  # Get speed multiplier
            
            midi = mido.MidiFile(file_path)
            
            print(f"Playing: {self.selected_item} at {int(speed_percent*100)}% speed")
            self.status_label.config(text=f"▶️ Playing at {int(speed_percent*100)}% speed... (F6 to stop)", fg="green")
            
            # Initial setup
            time.sleep(0.5)
            curr_pitch = 'f2'
            pyautogui.press(curr_pitch)
            pyautogui.PAUSE = 0
            
            for msg in midi.play():
                if not self.is_playing:
                    break
                
                # Adjust timing based on speed
                if msg.time > 0:
                    time.sleep(msg.time * (1.0 / speed_percent))
                    
                if msg.type == 'note_on' and msg.velocity != 0:
                    pitch, key = self.map_piano_note_to_key(msg.note + self.pitch_value)
                    if curr_pitch != pitch:
                        pyautogui.press(pitch)
                        curr_pitch = pitch
                    if key:
                        pyautogui.press(key)
            
            # Finished playing
            if self.is_playing:
                print("Finished")
                self.is_playing = False
                self.status_label.config(text="✅ Finished! Press F5 to play again", fg="blue")
                
                # Auto-play next
                if self.auto_play and self.current_index < self.listbox.size() - 1:
                    time.sleep(1)
                    self.current_index += 1
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(self.current_index)
                    self.listbox.see(self.current_index)
                    self.on_listbox_select(None)
                    time.sleep(0.5)
                    self.start_playing()
                    
        except Exception as e:
            print(f"Error: {e}")
            self.status_label.config(text=f"❌ Error: {e}", fg="red")
            self.is_playing = False

    def start_playing(self):
        if self.is_playing:
            return
            
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select a MIDI file first!")
            return
            
        self.selected_item = self.listbox.get(selected_indices[0]).split(' - ', 1)[1]
        self.current_index = selected_indices[0]
        self.is_playing = True
        
        self.play_thread = threading.Thread(target=self.play_midi, daemon=True)
        self.play_thread.start()

    def stop_playing(self):
        if self.is_playing:
            self.is_playing = False
            self.status_label.config(text="⏹️ Stopped. Press F5 to play", fg="red")
            print("Stopped")

    def on_closing(self):
        self.is_playing = False
        keyboard.unhook_all()
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=1)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiPlayerApp(root)
    root.mainloop()
