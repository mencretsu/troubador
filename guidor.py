import tkinter as tk
from tkinter import filedialog, messagebox
import os
import mido
import pyautogui                                                  
import time
import threading
pitch_value = 0
file_path = ""
popup_active = False 
root = tk.Tk()
root.iconbitmap(default='')
root.title("TROUBADOR")
root.attributes('-topmost', True)
def change_pitch(event):
    new_pitch = int(pitch_var.get())
    pitch_label.config(text=f"Pitch: {new_pitch}")
    print(new_pitch)
def map_piano_note_to_key(note):
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

def toggle_play():
    global is_playing, play_thread
    if is_playing:
        is_playing = False
        play_button.config(text="Play")
        loading_label.config(text="-- Stoped --")
    else:
        is_playing = True
        play_button.config(text="Stop")
        play_thread = threading.Thread(target=play_midi)
        play_thread.start()
def open_file_dialog():
    global file_path, popup_active 
    popup_active = True
    root.attributes('-topmost', False) 
    file_path = filedialog.askopenfilename()
    popup_active = False
    root.attributes('-topmost', True)
    if file_path:
        file_name = os.path.basename(file_path)
        print("File yang dipilih:", file_name)
        label.config(text=file_name)
        spinbox.delete(0, "end")
        spinbox.insert(0, 0)
def show_help():
    help_message = "TROUBADOR Help:\n\n- To change the instrument, select 'Change Instrument' from the menu and choose the desired instrument.\n- To open a MIDI file, click 'Input midi' and select the file.\n\nEnjoy playing music with TROUBADOR!"
    messagebox.showinfo("Help", help_message)

def play_midi():
    global file_path, is_playing, pitch_value
    pitch_value = int(spinbox.get())
    print(pitch_value)
    if not file_path:
        print("Pilih file MIDI terlebih dahulu")
        messagebox.showerror("SHIT", "Please input a midi file!")
        is_playing = False
        play_button.config(text="Play")
        return
    open_file_button.config(state="disabled")
    spinbox.config(state="disabled")
    selected_instrument = instrument_var.get()  # Mendapatkan instrumen yang dipilih
    
    if selected_instrument == "Piano":
        # Lakukan sesuatu untuk pemutaran instrumen piano
        print("piano play")
        pass
    elif selected_instrument == "Guitar":
        # Lakukan sesuatu untuk pemutaran instrumen gitar
        pass
    elif selected_instrument == "Keytar":
        # Lakukan sesuatu untuk pemutaran instrumen keytar
        pass
    elif selected_instrument == "Drum":
        # Lakukan sesuatu untuk pemutaran instrumen drum
        pass
    try:
        loading_label.config(text="-- Crafting --")
        midi = mido.MidiFile(file_path)
        print(f"MIDI File parsed.")
        time.sleep(5)
        loading_label.config(text=f"-- Pitch + {pitch_value} --")
        curr_pitch = 'f2'
        pyautogui.press(curr_pitch)
        pyautogui.PAUSE = 0
        loading_label.config(text="-- Playing --")
        for msg in midi.play():
            if not is_playing:
                break
            if msg.type == 'note_on' and msg.velocity != 0:
                pitch, key = map_piano_note_to_key(msg.note + pitch_value)
                if curr_pitch != pitch:
                    pyautogui.press(pitch)
                    curr_pitch = pitch
                pyautogui.press(key)
        is_playing = False
        play_button.config(text="Play")
        loading_label.config(text="--")
    except OSError as e:
        messagebox.showerror("Error", "Midi File is broken. Please choose another file!.")
        play_button.config(text="Play")
        loading_label.config(text="-- Error --")
    open_file_button.config(state="normal")
    spinbox.config(state="normal")
def play_midi_instrument():
    pass
def update_popup_position():
    if not popup_active:
        root.update()
        root.after(10, update_popup_position)
def set_instrument(instrument):
    instrument_var.set(instrument)

menubar = tk.Menu(root)
root.config(menu=menubar)

# Membuat menu "Change Instrument"
change_instrument_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="🛠️ Change Instrument", menu=change_instrument_menu)
instrument_var = tk.StringVar(root)
change_instrument_menu.add_command(label="🎹 Piano", command=lambda: set_instrument("Piano"))
change_instrument_menu.add_command(label="🎸 Guitar/accordion/bass, etc", command=lambda: set_instrument("Guitar"))
change_instrument_menu.add_command(label="🎼 Keytar", command=lambda: set_instrument("Keytar"))
change_instrument_menu.add_command(label="🥁 Drum", command=lambda: set_instrument("Drum"))


help_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="ℹ️ Help", menu=help_menu)
help_menu.add_command(label="Show Help", command=show_help)

open_file_button = tk.Button(root, text="📂Input midi", command=open_file_dialog)
open_file_button.grid(row=1, column=0, sticky='w', padx=20, pady=20)

label = tk.Label(root, text="--")
label.grid(row=1, column=1, sticky='w', padx=20, columnspan=10)

pitch_label = tk.Label(root, text=f"Set pitch")
pitch_label.grid(row=2, column=0, sticky='w', padx=20)

spinbox = tk.Spinbox(root, from_=-12, to=24, increment=1, width=5)
spinbox.grid(row=2, column=1, sticky='w', padx=20)
spinbox.bind("<FocusOut>", change_pitch)

spinbox.delete(0, 'end')
spinbox.insert(0, "0")

is_playing = False
play_button = tk.Button(root, text="▶️Play", command=toggle_play)
play_button.grid(row=4, column=0, sticky='w', padx=20, pady=20)

loading_label = tk.Label(root, text=" -- ")
loading_label.grid(row=4, column=1, sticky='w')

midi_player = None
root.geometry("400x300")
root.mainloop()
# -------------------------------------------------------