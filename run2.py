import tkinter as tk
from tkinter import filedialog, messagebox
import os
import mido
import pyautogui
import time
import threading

class MidiPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TROUBADOR")
        self.root.geometry("420x400")
        self.root.attributes('-topmost', True)
        self.pitch_value = 0
        self.file_path = ""
        self.popup_active = False
        self.play_thread = None
        self.is_playing = False
        self.imported_files = []
        self.file_path_dict = {}
        self.midi_length = 0
        self.selected_item = None
        self.bpm_value = 120
        self.files_to_play = []
        self.marquee_after_id = None
        self.is_paused = False
        self.midi_out = mido.open_output()
        self.setup_ui()

    def setup_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=1)
        self.root.columnconfigure(3, weight=0)
        self.root.rowconfigure(2, weight=1)

        self.listbox = tk.Listbox(self.root, height=6, width=40)
        self.listbox.grid(row=2, column=0, padx=5, pady=5, sticky='nsew', columnspan=3)
        self.listbox.bind('<<ListboxSelect>>', self.on_listbox_select)

        vertical_scrollbar = tk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.listbox.yview)
        vertical_scrollbar.grid(row=2, column=3, sticky='ns')
        self.listbox.config(yscrollcommand=vertical_scrollbar.set)

        horizontal_scrollbar = tk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.listbox.xview)
        horizontal_scrollbar.grid(row=3, column=0, sticky='ew', columnspan=3)
        self.listbox.config(xscrollcommand=horizontal_scrollbar.set)

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ℹ️ Help", menu=help_menu)
        help_menu.add_command(label="Show Help", command=self.show_help)

        self.open_file_button = tk.Button(self.root, text="📂 Import midi to library ", command=self.open_file_dialog, relief="solid", bd=1, bg="#FFFFFF")
        self.open_file_button.grid(row=1, column=0, sticky='w', padx=5, pady=5)

        self.delete_button = tk.Button(self.root, text="♻️ Delete ", command=self.delete_selected_item,relief="solid", bd=1, bg="#FFFFFF")
        self.delete_button.grid(row=1, column=1, padx=5, pady=5)

        # Custom Play Button with styles
        self.play_button = tk.Button(self.root, text="▶️ Play ", command=self.toggle_play, relief="solid", bd=1, bg="#FFFFFF")
        self.play_button.grid(row=1, column=2, padx=5, pady=5)

        pitch_label = tk.Label(self.root, text="Pitch: ")
        pitch_label.grid(row=4, column=0, sticky='w', padx=5, pady=5)

        self.spinbox = tk.Spinbox(self.root, from_=-12, to=24, increment=1, width=5)
        self.spinbox.grid(row=4, column=0, sticky='w', padx=50, pady=5)
        self.spinbox.delete(0, 'end')
        self.spinbox.insert(0, "0")

        bpm_label = tk.Label(self.root, text="BPM: ")
        bpm_label.grid(row=4, column=1, sticky='w', padx=5, pady=5)

        self.bpm_spinbox = tk.Spinbox(self.root, from_=20, to=300, increment=1, width=5)
        self.bpm_spinbox.grid(row=4, column=1, sticky='w', padx=50, pady=5)
        self.bpm_spinbox.delete(0, 'end')
        self.bpm_spinbox.insert(0, "120")

        self.loading_label = tk.Label(self.root, text="")
        self.loading_label.grid(row=6, column=0, sticky='w', padx=5, pady=5)

        self.label = tk.Label(self.root, text="", anchor='w')
        self.label.grid(row=6, column=0, sticky='w', padx=100, columnspan=3, pady=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.load_saved_files()
        self.bind_hover_events([self.open_file_button, self.delete_button, self.play_button])

    def bind_hover_events(self, widgets):
        for widget in widgets:
            widget.bind("<Enter>", self.on_enter)
            widget.bind("<Leave>", self.on_leave)
    def on_enter(self, event):
        event.widget.config(relief="solid", bd=1, bg="#E2F0FF")

    def on_leave(self, event):
        event.widget.config(relief="solid", bd=1, bg="#FFFFFF")

    def open_file_dialog(self):
        self.popup_active = False
        self.file_path = filedialog.askopenfilename()
        self.popup_active = True
        if self.file_path and self.file_path not in self.imported_files:
            try:
                midi = mido.MidiFile(self.file_path)
                self.midi_length = midi.length
                file_name = os.path.basename(self.file_path)
                self.imported_files.append(self.file_path)
                print("File yang dipilih:", file_name)
                self.label.config(text="imported")
                self.spinbox.delete(0, "end")
                self.spinbox.insert(0, 0)
                self.file_path_dict[file_name] = self.file_path
                self.save_files()
                self.load_saved_files()
                original_tempo = self.get_original_tempo(midi)
                self.bpm_value = mido.tempo2bpm(original_tempo)
                self.bpm_spinbox.delete(0, 'end')
                self.bpm_spinbox.insert(0, int(self.bpm_value))
                messagebox.showinfo("Success", "Midi file loaded!")
            except (OSError, Exception) as e:
                print(f"Error loading MIDI file: {e}")
                self.root.after(0, messagebox.showerror, "Error", "Invalid MIDI file. Please choose a valid MIDI file.")

    def delete_selected_item(self):
        selected_indices = self.listbox.curselection()
        if selected_indices:
            for index in selected_indices:
                selected_item = self.listbox.get(index).split(' - ', 1)[1]
                confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{selected_item}'?")
                if confirm:
                    file_path = self.file_path_dict.get(selected_item)
                    if file_path in self.imported_files:
                        self.imported_files.remove(file_path)
                    self.listbox.delete(index)
                    del self.file_path_dict[selected_item]
            self.save_files()
            self.load_saved_files()

    def save_files(self):
        with open('midi_files.txt', 'w') as file:
            for item in self.imported_files:
                file.write(item + '\n')

    def load_saved_files(self):
        self.listbox.delete(0, "end")
        self.file_path_dict.clear()
        try:
            with open('midi_files.txt', 'r') as file:
                existing_files = [line.strip() for line in file]
            unique_files = list(set(existing_files))
            unique_files = [file_path.lower() for file_path in unique_files]
            unique_files.sort(key=lambda x: os.path.basename(x))
            max_index_length = len(str(len(unique_files)))
            for idx, file_path in enumerate(unique_files, start=1):
                file_name = os.path.basename(file_path)
                padded_index = str(idx).rjust(max_index_length)
                self.listbox.insert(tk.END, f" {padded_index} - {file_name}")
                self.imported_files.append(file_path)
                self.file_path_dict[file_name] = file_path
            with open('midi_files.txt', 'w') as file:
                file.write('\n'.join(unique_files))
        except FileNotFoundError:
            pass

    def show_help(self):
        help_message = "TROUBADOR Help:\n\n- To open a MIDI file, click 'Import midi' and select the file.\n\nEnjoy playing music with TROUBADOR!"
        messagebox.showinfo("Help", help_message)

    def change_tempo(self, midi, new_tempo):
        for track in midi.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    msg.tempo = new_tempo
        return midi

    def get_original_tempo(self, midi):
        for track in midi.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    return msg.tempo
        return 500000  # Default tempo if not found

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
        return change_G, piano_keymap[note - baseline]

    def play_midi(self):
        self.pitch_value = int(self.spinbox.get())
        print(self.pitch_value)
        if not self.selected_item:
            messagebox.showerror("Error", "Please select a MIDI file first!")
            return False
        print("Selected Item:", self.selected_item)
        self.file_path = self.file_path_dict.get(self.selected_item)
        if not self.file_path:
            messagebox.showerror("Error", "Please select a valid MIDI file!")
            return False
        try:
            midi = mido.MidiFile(self.file_path)
            filename = os.path.basename(self.file_path)
            name, extension = os.path.splitext(filename)
            print("Name:", name)
            print(f"MIDI File parsed.")
            curr_pitch = 'f2'
            pyautogui.press(curr_pitch)
            pyautogui.PAUSE = 0
            
            original_tempo = self.get_original_tempo(midi)
            print(f"Original Tempo: {original_tempo} us/beat")
            new_tempo = mido.bpm2tempo(self.bpm_value)
            print(f"New Tempo: {new_tempo} us/beat")
            midi = self.change_tempo(midi, new_tempo)
            
            for msg in midi.play():
                while self.is_paused:
                    if not self.is_playing:
                        return False  # Menghentikan pemutaran jika is_playing menjadi False
                    time.sleep(0.1)  # Kurangi waktu sleep untuk responsivitas yang lebih baik
                if not self.is_playing:
                    break  # Menghentikan pemutaran jika is_playing menjadi False
                if msg.type == 'note_on' and msg.velocity != 0:
                    pitch, key = self.map_piano_note_to_key(msg.note + self.pitch_value)
                    if curr_pitch != pitch:
                        pyautogui.press(pitch)
                        curr_pitch = pitch
                    pyautogui.press(key)
            
            if self.is_playing:
                print("Finished")
                self.is_playing = False  # Set is_playing to False when finished
                self.play_button.config(text="▶️ Play ")  # Update play button text
                self.loading_label.config(text="Finished")  # Update label text
                self.items_config(enable_items=True)  # Re-enable UI items
                return True  # Indicate that the MIDI file finished playing
        except OSError as e:
            print(e)
            messagebox.showerror("Error", "An error occurred while playing the MIDI file.")
            return False  # Indicate that an error occurred
        finally:
            self.is_playing = False  # Ensure is_playing is set to False in case of an error

    def toggle_play(self):
        if self.is_playing:
            if self.is_paused:
                self.is_paused = False
                self.play_button.config(text="⏸️ Pause ")
                self.loading_label.config(text="Playing")
                self.items_config(enable_items=False)
                print("Resumed")
            else:
                self.is_paused = True
                self.play_button.config(text="▶️ Play ")
                self.loading_label.config(text="Paused")
                self.items_config(enable_items=True)
                print("Paused")
        else:
            selected_indices = self.listbox.curselection()
            if not selected_indices:
                messagebox.showerror("Error", "Please select a MIDI file first.")
                self.label.config(text="")
                return
            self.selected_item = self.listbox.get(selected_indices[0]).split(' - ', 1)[1]
            self.set_bpm()  # Pastikan BPM diatur sebelum memulai pemutaran
            self.is_playing = True
            self.is_paused = False
            self.play_button.config(text="⏸️ Pause ")
            self.loading_label.config(text="Playing")
            self.items_config(enable_items=False)
            self.play_thread = threading.Thread(target=self.play_midi)
            self.play_thread.start()

    def set_bpm(self):
        self.bpm_value = int(self.bpm_spinbox.get())
        print(f"BPM set to: {self.bpm_value}")

    def on_listbox_select(self, event):
        # Hentikan pemutaran saat ini jika ada
        if self.is_playing:
            self.is_playing = False
            self.is_paused = False
            if self.play_thread and self.play_thread.is_alive():
                self.play_thread.join()  # Tunggu thread selesai
            self.play_button.config(text="▶️ Play ")
            self.loading_label.config(text="Finished")
            self.items_config(enable_items=True)

        selected_indices = self.listbox.curselection()
        if selected_indices:
            self.selected_item = self.listbox.get(selected_indices[0]).split(' - ', 1)[1]
            file_path = self.file_path_dict.get(self.selected_item)
            if file_path:
                try:
                    midi = mido.MidiFile(file_path)
                    original_tempo = self.get_original_tempo(midi)
                    self.bpm_value = mido.tempo2bpm(original_tempo)
                    self.bpm_spinbox.delete(0, 'end')
                    self.bpm_spinbox.insert(0, int(self.bpm_value))
                    
                    if self.marquee_after_id is not None:
                        self.label.after_cancel(self.marquee_after_id)
                        self.marquee_after_id = None
                    
                    if len(self.selected_item) > 25:
                        self.marquee_text(self.label, self.selected_item)
                    else:
                        self.label.config(text=self.selected_item)
                    
                    self.loading_label.config(text="Selected:")
                except (OSError, Exception) as e:
                    print(f"Error loading MIDI file: {e}")

    def items_config(self, enable_items):
        state = "normal" if enable_items else "disabled"
        self.bpm_spinbox.config(state=state)
        self.spinbox.config(state=state)
        self.listbox.config(state=state)
        self.open_file_button.config(state=state)
        self.delete_button.config(state=state)

    def on_closing(self):
        if self.is_playing:
            self.is_playing = False
            if self.play_thread and self.play_thread.is_alive():
                self.play_thread.join()  # Tunggu thread selesai
        print("closed")
        self.midi_out.close()
        self.root.destroy()

    def marquee_text(self, label, text, max_length=25, delay=100):
        text += ' - '  # Tambahkan spasi di akhir teks
        def update_text():
            nonlocal text  # Deklarasikan text sebagai nonlocal
            display_text = text[:max_length]
            label.config(text=display_text)
            text = text[1:] + text[0]
            self.marquee_after_id = label.after(delay, update_text)
        update_text()

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiPlayerApp(root)
    root.mainloop()
