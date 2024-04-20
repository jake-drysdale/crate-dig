import sys
import json
import tkinter as tk
from tkinter import DoubleVar, StringVar, IntVar, HORIZONTAL, END, Frame
import tkinter.font
from tkinter import filedialog, messagebox
from tkinter.ttk import Notebook
from sample_finder_SA_inter import (
    load_embeddings_index,
    process_new_audio_sample,
    find_wav_files,
    build_embeddings_index,
    save_embeddings_index,
)

# from sample_finder_SA_inter import process_iterative_samples as process_new_audio_sample
import os
import argparse
import customtkinter


customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("dark-blue")

LAST_STATE_FILE_SF = "UserLibrary/state/last_state_samplefinder.json"
LAST_STATE_FILE_ANL = "UserLibrary/state/last_state_analyse_new_library.json"


class CLIArgs:
    def __init__(
        self,
        input_value,
        n_samples,
        destination_folder,
        embedding_map_dir,
        is_text=True,
    ):
        self.input_value = input_value
        self.n_samples = n_samples
        self.destination_folder = destination_folder
        self.embedding_map_dir = embedding_map_dir
        self.is_text = is_text

    def __repr__(self) -> str:
        return f"CLIArgs(input_value={self.input_value}, n_samples={self.n_samples}, destination_folder={self.destination_folder}, embedding_map_dir={self.embedding_map_dir}, is_text={self.is_text})"


def run_sample_finder_cli(args):

    embeddings_index, path_map = load_embeddings_index(args.embedding_map_dir)
    return process_new_audio_sample(
        args.input_value,
        embeddings_index,
        path_map,
        args.n_samples,
        args.destination_folder,
        args.is_text,
    )


class App:
    def __init__(self, parent):
        self.default_theme = {
            "bg_dark": "#38304d",
            "bg_light": "#1f1a30",
            "bg_accent": "#201a30",
            "text": "#ffffff",
            "accent": "#0df5e3",
            "font": "Space Grotesk",
            "font_weight": "bold",  # "bold", "normal", "italic", "roman
            "font_size": 18,
            "button_enter": {
                "text_color": "white",
                "fg_color": "#38304d",
            },
            "button_leave": {
                "text_color": "black",
                "fg_color": "#0df5e3",
            },
        }
        self.common_configs = {
            "label": {
                "anchor": "w",
                "text_color": self.default_theme["text"],
                "bg_color": self.default_theme["bg_light"],
                "font": (
                    self.default_theme["font"],
                    self.default_theme["font_size"],
                    "bold",
                ),
                "state": "normal",
            },
            "labelLarge": {
                "anchor": "w",
                "text_color": self.default_theme["text"],
                "font": (self.default_theme["font"], 22, "bold"),
                "state": "normal",
                "width": 360,
                "height": 52,
            },
            "entry": {
                "fg_color": self.default_theme["bg_dark"],
                "text_color": self.default_theme["text"],
                "font": (self.default_theme["font"], self.default_theme["font_size"]),
                "state": "normal",
            },
            "entryTk": {
                "fg": self.default_theme["bg_dark"],
                "bg": self.default_theme["text"],
                "state": "normal",
            },
            "buttonMain": {
                "fg_color": self.default_theme["accent"],
                "text_color": self.default_theme["bg_dark"],
                "font": (self.default_theme["font"], 18),
                "state": "normal",
            },
            "buttonBrowse": {
                "text": "Browse...",
                "fg_color": self.default_theme["bg_dark"],
                "text_color": self.default_theme["text"],
                "font": (self.default_theme["font"], self.default_theme["font_size"]),
                "state": "normal",
            },
        }

        self.gui(parent)

    def onHover(self, button: customtkinter.CTkButton, before=None, after=None):
        """
        Change the appearance of a button when hovered over.
        """
        if before is None:
            before = self.default_theme["button_leave"]
        if after is None:
            after = self.default_theme["button_enter"]

        button.bind("<Enter>", command=lambda e: button.configure(**after))
        button.bind("<Leave>", command=lambda e: button.configure(**before))

    def gui(self, parent):
        """
        Create the GUI for the application.
        """
        dw = 800
        dh = 860

        if parent == 0:
            self.widget = customtkinter.CTk()
            self.widget.title("Sample Finder")
            self.widget.geometry(f"{dw}x{dh}")
            self.widget.resizable(True, True)
        else:
            self.widget = Frame(parent)
            self.widget.place(x=0, y=0, width=dw, height=dh)

        offset = 10

        with open(LAST_STATE_FILE_SF, "r") as f:
            last_state_sf = json.load(f)
        with open(LAST_STATE_FILE_ANL, "r") as f:
            last_state_anl = json.load(f)

        if last_state_sf.get("embedding_map_dir", "") == "":
            audio_collection_dir = last_state_anl.get("audio_collection_dir", "")
            library_name = last_state_anl.get("emap_name", "")
            if audio_collection_dir != "" and library_name != "":
                last_state_sf["embedding_map_dir"] = os.path.join(
                    last_state_anl["save_emap_location"], library_name
                )

        self.input_type_var = StringVar()
        self.n_samples_var = StringVar(value="1")

        self.destination_folder_var = StringVar(
            value=last_state_sf.get("destination_folder", "")
        )
        self.embedding_map_dir_var = StringVar(
            value=last_state_sf.get("embedding_map_dir", "")
        )
        self.audio_collection_var = StringVar(
            value=last_state_anl.get("audio_collection_dir", "")
        )
        self.save_emap_location_var = StringVar(
            value=last_state_anl.get("save_emap_location", "")
        )
        self.library_name_var = StringVar(value=last_state_anl.get("emap_name", ""))
        self.progress_var = DoubleVar(value=0.0)

        def browse_folder(entry):
            """
            Browse for a folder and insert the path into the entry.
            """
            folder_selected = filedialog.askdirectory()
            entry.delete(0, END)
            entry.insert(0, folder_selected)

        def browse_file(entry):
            """
            Browse for a file and insert the path into the entry.
            """
            file_selected = filedialog.askopenfilename(
                filetypes=[("Audio Files", "*.mp3 *.wav *.flac")]
            )
            entry.delete(0, END)
            entry.insert(0, file_selected)

        def validate_and_run(input_type):
            """
            Validate the input fields and run the sample finder.
            """

            try:
                if input_type == "text":
                    input_value = self.text_prompt_entry.get()
                else:
                    input_value = self.audio_file_entry.get()
                try:
                    n_samples = int(self.n_samples_var.get())
                except ValueError:
                    messagebox.showerror(
                        "Error", "Number of samples must be an integer."
                    )
                    self.n_samples_var.set("1")
                    return
                destination_folder = self.destination_folder_var.get()
                embedding_map_dir = self.embedding_map_dir_var.get()
                with open(LAST_STATE_FILE_SF, "w") as f:
                    json.dump(
                        {
                            "destination_folder": destination_folder,
                            "embedding_map_dir": embedding_map_dir,
                        },
                        f,
                        indent=4,
                    )
                args = CLIArgs(
                    input_value,
                    n_samples,
                    destination_folder,
                    embedding_map_dir,
                    is_text=(input_type == "text"),
                )
                result = run_sample_finder_cli(args)
                self.playlist_textbox_audio.delete("1.0", END)
                self.playlist_textbox_text.delete("1.0", END)
                self.playlist_textbox_audio.insert(
                    "1.0",
                    "\n".join(
                        f"{index+1}. {path}" for index, path in enumerate(result)
                    ),
                )
                self.playlist_textbox_text.insert(
                    "1.0",
                    "\n".join(
                        f"{index+1}. {path}" for index, path in enumerate(result)
                    ),
                )

                messagebox.showinfo("Success", "Operation Completed Successfully")
            except ValueError:
                messagebox.showerror("Error", "Number of samples must be an integer.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

        def analyze_audio_collection():
            """
            Analyze the audio collection and save the embeddings index.
            """
            audio_collection_dir = self.audio_collection_entry.get()
            file_type = self.file_type_entry.get()
            if file_type == "any":
                file_type = (".wav", ".flac", ".mp3")
            emap_name = self.library_name_var.get()
            save_emap_location = self.save_emap_location_var.get()
            with open(LAST_STATE_FILE_ANL, "w") as f:
                json.dump(
                    {
                        "audio_collection_dir": audio_collection_dir,
                        "emap_name": emap_name,
                        "save_emap_location": save_emap_location,
                    },
                    f,
                    indent=4,
                )

            if not audio_collection_dir or not emap_name or not save_emap_location:
                messagebox.showwarning("Warning", "Please fill in all required fields.")
                return

            save_emap_full_path = os.path.join(save_emap_location, emap_name)
            os.makedirs(save_emap_full_path, exist_ok=True)
            self.embedding_map_dir_var.set(save_emap_full_path)

            try:
                wav_files = find_wav_files(audio_collection_dir, file_type)
                embeddings_index, path_map = build_embeddings_index(
                    wav_files,
                    os.path.join(save_emap_full_path, "embeddings_list.npy"),
                    self.analysis_progressbar,
                    self.widget.update_idletasks,
                )
                save_embeddings_index(
                    embeddings_index,
                    path_map,
                    os.path.join(save_emap_full_path, "embeddings.ann"),
                    os.path.join(save_emap_full_path, "path_map.json"),
                )
                messagebox.showinfo(
                    "Success",
                    f"Analysis completed. Embeddings saved to {save_emap_full_path}.",
                )
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
        
        def update_entries_number(entries, new_value):
            for entry in entries:
                entry.set(new_value)

        self.app_notebook = Notebook(self.widget)
        self.app_notebook.place(x=0, y=0, width=dw, height=dh)

        self.sample_finder_tab = Frame(self.app_notebook)
        self.sample_finder_tab.configure(bg=self.default_theme["bg_accent"])
        self.sample_finder_tab.place(
            x=0,
            y=0,
        )

        self.analyse_new_library_tab = Frame(self.app_notebook)
        self.analyse_new_library_tab.configure(bg=self.default_theme["bg_accent"])
        self.analyse_new_library_tab.place(
            x=0,
            y=0,
        )

        # --------------------- Sample Finder ---------------------

        iw = dw - 20
        ih = dh - 100
        xgap = 20
        bw = 110
        rbx = iw - (xgap + bw)
        ew = iw - (3 * xgap + bw)

        self.input_mode_notebook = Notebook(self.sample_finder_tab)
        self.input_mode_notebook.place(x=8, y=66, width=iw, height=ih)

        # --------------------- Sample Finder: Search By Text ---------------------

        self.search_by_text_tab = Frame(self.input_mode_notebook)
        self.search_by_text_tab.configure(bg=self.default_theme["bg_accent"])
        self.search_by_text_tab.place(x=0, y=0)

        self.search_for_samples_label = customtkinter.CTkLabel(
            self.sample_finder_tab,
            text="Search for Samples",
            **self.common_configs["labelLarge"],
        )
        self.search_for_samples_label.place(x=xgap, y=6)

        self.text_prompt_label = customtkinter.CTkLabel(
            self.search_by_text_tab,
            text="Text Prompt",
            **self.common_configs["label"],
            width=210,
            height=22,
        )
        self.text_prompt_label.place(x=xgap, y=10 + offset)
        self.text_prompt_entry = customtkinter.CTkEntry(
            self.search_by_text_tab,
            **self.common_configs["entry"],
            width=iw - (2 * xgap),
            height=22,
        )
        self.text_prompt_entry.place(x=xgap, y=44 + offset)

        self.n_samples_label = customtkinter.CTkLabel(
            self.search_by_text_tab,
            text="Number of samples to retrieve",
            **self.common_configs["label"],
            width=300,
            height=22,
        )
        self.n_samples_label.place(x=xgap, y=86 + offset)

        self.n_samples_text_textbox = customtkinter.CTkEntry(
            self.search_by_text_tab,
            **self.common_configs["entry"],
            width=bw,
            height=22,
            textvariable=self.n_samples_var,
        )
        self.n_samples_text_textbox.place(x=xgap, y=120 + offset)
        self.nsamplestext_var = IntVar(value=1)
        self.n_samples_text_slider = customtkinter.CTkSlider(
            self.search_by_text_tab,
            from_=0,
            to=100,
            orientation=HORIZONTAL,
            fg_color=self.default_theme["bg_dark"],
            cursor="arrow",
            state="normal",
            width=ew,
            height=22,
            command=lambda x: update_entries_number(
                [self.n_samples_var, self.nsamplesaudio_var], int(float(x))
            ),
            variable=self.nsamplestext_var,
        )
        self.n_samples_text_slider.place(x=(2 * xgap + bw), y=120 + offset)

        self.export_dir_label = customtkinter.CTkLabel(
            self.search_by_text_tab,
            text="Export List To",
            **self.common_configs["label"],
            width=300,
            height=22,
        )
        self.export_dir_label.place(x=20, y=154 + offset * 2)
        self.destination_folder_text_entry = customtkinter.CTkEntry(
            self.search_by_text_tab,
            **self.common_configs["entry"],
            width=ew,
            height=22,
            textvariable=self.destination_folder_var,
        )
        self.destination_folder_text_entry.place(x=xgap, y=188 + offset * 2)
        self.exportdirbutton = customtkinter.CTkButton(
            self.search_by_text_tab,
            **self.common_configs["buttonBrowse"],
            width=bw,
            height=22,
            command=lambda: browse_folder(self.destination_folder_text_entry),
        )
        self.exportdirbutton.place(x=rbx, y=188 + offset * 2)

        self.librarylocationlabel = customtkinter.CTkLabel(
            self.search_by_text_tab,
            text="Library Location",
            **self.common_configs["label"],
            width=300,
            height=22,
        )
        self.librarylocationlabel.place(x=20, y=220 + offset * 3)
        self.liblocentry = customtkinter.CTkEntry(
            self.search_by_text_tab,
            **self.common_configs["entry"],
            width=ew,
            height=22,
            textvariable=self.embedding_map_dir_var,
        )
        self.liblocentry.place(x=xgap, y=250 + offset * 3)
        self.liblocbrowse = customtkinter.CTkButton(
            self.search_by_text_tab,
            **self.common_configs["buttonBrowse"],
            width=bw,
            height=22,
            command=lambda: browse_folder(self.liblocentry),
        )
        self.liblocbrowse.place(x=rbx, y=250 + offset * 3)

        textbox_h = 290
        textbox_y = 300 + offset * 8 + 44
        self.playlist_textbox_text = customtkinter.CTkTextbox(
            self.search_by_text_tab,
            **self.common_configs["entry"],
            width=iw - (2 * xgap),
            height=textbox_h,
            wrap="none",
        )
        self.playlist_textbox_text.place(x=xgap, y=textbox_y)

        # --------------------- Run Button ---------------------

        self.searchbytextbutton = customtkinter.CTkButton(
            self.search_by_text_tab,
            text="Run Sample Finder",
            **self.common_configs["buttonMain"],
            width=300,
            height=44,
            command=lambda: validate_and_run("text"),
        )
        self.searchbytextbutton.place(x=round(iw / 2) - 150, y=300 + offset * 5)
        self.onHover(self.searchbytextbutton)

        self.input_mode_notebook.add(self.search_by_text_tab, text="Search By Text")

        # --------------------- Sample Finder: Search By Audio ---------------------

        self.search_by_audio_tab = Frame(self.input_mode_notebook)
        self.search_by_audio_tab.configure(bg=self.default_theme["bg_accent"])
        self.search_by_audio_tab.place(x=0, y=0, width=476, height=372)

        self.base_audio_label = customtkinter.CTkLabel(
            self.search_by_audio_tab,
            text="Base Audio",
            **self.common_configs["label"],
            width=210,
            height=22,
        )
        self.base_audio_label.place(x=20, y=10 + offset)
        self.audio_file_entry = customtkinter.CTkEntry(
            self.search_by_audio_tab,
            **self.common_configs["entry"],
            width=ew,
            height=22,
        )
        self.audio_file_entry.place(x=xgap, y=44 + offset)
        self.base_audio_browse = customtkinter.CTkButton(
            self.search_by_audio_tab,
            **self.common_configs["buttonBrowse"],
            width=bw,
            height=22,
            command=lambda: browse_file(self.audio_file_entry),
        )
        self.base_audio_browse.place(x=rbx, y=44 + offset)

        self.n_samples_audio_label = customtkinter.CTkLabel(
            self.search_by_audio_tab,
            text="Number of samples to retrieve",
            **self.common_configs["label"],
            width=300,
            height=22,
        )
        self.n_samples_audio_label.place(x=20, y=86 + offset)

        self.n_samples_audio_textbox = customtkinter.CTkEntry(
            self.search_by_audio_tab,
            **self.common_configs["entry"],
            width=bw,
            height=22,
            textvariable=self.n_samples_var,
        )
        self.n_samples_audio_textbox.place(x=xgap, y=120 + offset)
        self.nsamplesaudio_var = IntVar(value=1)
        self.n_samples_audio_slider = customtkinter.CTkSlider(
            self.search_by_audio_tab,
            from_=1,
            to=100,
            orientation=HORIZONTAL,
            fg_color=self.default_theme["bg_dark"],
            cursor="arrow",
            state="normal",
            width=ew,
            height=22,
            command=lambda x: update_entries_number(
                [self.n_samples_var, self.nsamplestext_var], int(float(x))
            ),
            variable=self.nsamplesaudio_var,
        )
        self.n_samples_audio_slider.place(x=(2 * xgap + bw), y=120 + offset)

        self.export_dir_audio_label = customtkinter.CTkLabel(
            self.search_by_audio_tab,
            text="Export List To",
            **self.common_configs["label"],
            width=300,
            height=22,
        )
        self.export_dir_audio_label.place(x=20, y=154 + offset * 2)
        self.destination_folder_audio_entry = customtkinter.CTkEntry(
            self.search_by_audio_tab,
            **self.common_configs["entry"],
            width=ew,
            height=22,
            textvariable=self.destination_folder_var,
        )
        self.destination_folder_audio_entry.place(x=xgap, y=188 + offset * 2)
        self.export_dir_button_audio = customtkinter.CTkButton(
            self.search_by_audio_tab,
            **self.common_configs["buttonBrowse"],
            width=bw,
            height=22,
            command=lambda: browse_folder(self.destination_folder_audio_entry),
        )
        self.export_dir_button_audio.place(x=rbx, y=188 + offset * 2)

        self.librarylocationlabel_audio = customtkinter.CTkLabel(
            self.search_by_audio_tab,
            text="Library Location",
            **self.common_configs["label"],
            width=300,
            height=22,
        )
        self.librarylocationlabel_audio.place(x=20, y=220 + offset * 3)
        self.liblocentry_audio = customtkinter.CTkEntry(
            self.search_by_audio_tab,
            **self.common_configs["entry"],
            width=ew,
            height=22,
            textvariable=self.embedding_map_dir_var,
        )
        self.liblocentry_audio.place(x=xgap, y=250 + offset * 3)
        self.liblocbrowse_audio = customtkinter.CTkButton(
            self.search_by_audio_tab,
            **self.common_configs["buttonBrowse"],
            width=bw,
            height=22,
            command=lambda: browse_folder(self.liblocentry),
        )
        self.liblocbrowse_audio.place(x=rbx, y=250 + offset * 3)

        self.playlist_textbox_audio = customtkinter.CTkTextbox(
            self.search_by_audio_tab,
            **self.common_configs["entry"],
            width=iw - (2 * xgap),
            height=textbox_h,
            wrap="none",
        )

        self.playlist_textbox_audio.place(x=xgap, y=textbox_y)

        # --------------------- Run Button ---------------------

        self.searchbyaudio_button = customtkinter.CTkButton(
            self.search_by_audio_tab,
            text="Run Sample Finder",
            **self.common_configs["buttonMain"],
            width=300,
            height=44,
            command=lambda: validate_and_run("audio"),
        )
        self.searchbyaudio_button.place(x=round(iw / 2) - 150, y=300 + offset * 5)
        self.onHover(self.searchbyaudio_button)

        self.input_mode_notebook.add(self.search_by_audio_tab, text="Search By Audio")

        self.app_notebook.add(self.sample_finder_tab, text="Sample Finder")

        # --------------------- Analyse New Library ---------------------

        self.extraction_notebook = Notebook(self.analyse_new_library_tab)
        self.extraction_notebook.place(x=8, y=66, width=iw, height=ih)

        self.embedding_extraction_tab = Frame(self.extraction_notebook)
        self.embedding_extraction_tab.configure(bg=self.default_theme["bg_accent"])
        self.embedding_extraction_tab.place(
            x=0,
            y=0,
        )

        self.analyse_new_library_label = customtkinter.CTkLabel(
            self.analyse_new_library_tab,
            text="Analyse A New Library",
            **self.common_configs["labelLarge"],
        )
        self.analyse_new_library_label.place(x=xgap, y=6)

        self.library_path_label = customtkinter.CTkLabel(
            self.embedding_extraction_tab,
            text="Path To Your Library",
            **self.common_configs["label"],
            width=210,
            height=22,
        )
        self.library_path_label.place(x=20, y=10 + offset)
        self.audio_collection_entry = customtkinter.CTkEntry(
            self.embedding_extraction_tab,
            **self.common_configs["entry"],
            width=ew,
            height=22,
            textvariable=self.audio_collection_var,
        )
        self.audio_collection_entry.place(x=xgap, y=44 + offset)
        self.libpath_browse_button = customtkinter.CTkButton(
            self.embedding_extraction_tab,
            **self.common_configs["buttonBrowse"],
            width=bw,
            height=22,
            command=lambda: browse_folder(self.audio_collection_entry),
        )
        self.libpath_browse_button.place(x=rbx, y=44 + offset)

        self.library_index_saveloc_label = customtkinter.CTkLabel(
            self.embedding_extraction_tab,
            text="Where to save library index",
            **self.common_configs["label"],
            width=280,
            height=22,
        )
        self.library_index_saveloc_label.place(x=20, y=86 + offset)
        self.save_emap_location_entry = customtkinter.CTkEntry(
            self.embedding_extraction_tab,
            **self.common_configs["entry"],
            width=ew,
            height=22,
            textvariable=self.save_emap_location_var,
        )
        self.save_emap_location_entry.place(x=xgap, y=120 + offset)
        self.libindex_savepath_button = customtkinter.CTkButton(
            self.embedding_extraction_tab,
            **self.common_configs["buttonBrowse"],
            width=110,
            height=22,
            command=lambda: browse_folder(self.save_emap_location_entry),
        )
        self.libindex_savepath_button.place(x=rbx, y=120 + offset)

        self.library_name_label = customtkinter.CTkLabel(
            self.embedding_extraction_tab,
            text="Library Name",
            **self.common_configs["label"],
            width=280,
            height=22,
        )
        self.library_name_label.place(x=20, y=154 + offset * 2)
        self.library_name = customtkinter.CTkEntry(
            self.embedding_extraction_tab,
            **self.common_configs["entry"],
            width=iw - (2 * xgap),
            height=22,
            textvariable=self.library_name_var,
        )
        self.library_name.place(x=xgap, y=188 + offset * 2)

        self.fileformat_label = customtkinter.CTkLabel(
            self.embedding_extraction_tab,
            text="Default File Format",
            **self.common_configs["label"],
            width=210,
            height=22,
        )
        self.fileformat_label.place(x=20, y=250 + offset * 3)
        self.file_type_entry = customtkinter.CTkComboBox(
            self.embedding_extraction_tab,
            **self.common_configs["entry"],
            width=bw,
            height=22,
            values=["any", ".wav", ".flac", ".mp3"],
        )
        self.file_type_entry.place(x=rbx, y=250 + offset * 3)

        self.analysis_progressbar = customtkinter.CTkProgressBar(
            self.embedding_extraction_tab,
            width=iw - (2 * xgap),
            height=22,
            variable=self.progress_var,
            progress_color=self.default_theme["accent"],
            bg_color=self.default_theme["bg_light"],
            corner_radius=2,
            determinate_speed=0.1,
            mode="determinate",
        )
        self.analysis_progressbar.place(x=xgap, y=350 + offset * 8)

        self.analyse_button = customtkinter.CTkButton(
            self.embedding_extraction_tab,
            text="Analyze and Save Collection",
            **self.common_configs["buttonMain"],
            width=340,
            height=44,
            command=analyze_audio_collection,
        )
        self.analyse_button.place(x=round(iw / 2) - 170, y=300 + offset * 5)
        self.onHover(self.analyse_button)

        self.extraction_notebook.add(
            self.embedding_extraction_tab, text="Embedding Extraction"
        )

        self.app_notebook.add(self.analyse_new_library_tab, text="Analyse New Library")


if __name__ == "__main__":
    application_path = (
        os.path.dirname(sys.executable)
        if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.abspath(__file__))
    )
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(
            description="Find and copy closest audio samples."
        )
        parser.add_argument(
            "--input_value",
            required=True,
            help="Text prompt or path to the audio file for searching",
        )
        parser.add_argument(
            "--n_samples",
            type=int,
            required=True,
            help="Number of closest samples to find and copy",
        )
        parser.add_argument(
            "--destination_folder",
            default=os.path.join(application_path, "found_samples"),
            help="Folder to copy closest samples to",
        )
        parser.add_argument(
            "--embedding_map_dir",
            default=os.path.join(application_path, "embeddings"),
            help="Path to the folder with embeddings index and path map files",
        )
        parser.add_argument(
            "--is_text", action="store_true", help="Process as text instead of audio"
        )

        args = parser.parse_args()
        run_sample_finder_cli(args)

    else:
        if not os.path.exists(LAST_STATE_FILE_SF):
            os.makedirs(os.path.dirname(LAST_STATE_FILE_SF), exist_ok=True)
            with open(LAST_STATE_FILE_SF, "w") as f:
                json.dump(
                    {
                        "destination_folder": "",
                        "embedding_map_dir": "",
                    },
                    f,
                )
        if not os.path.exists(LAST_STATE_FILE_ANL):
            os.makedirs(os.path.dirname(LAST_STATE_FILE_ANL), exist_ok=True)
            with open(LAST_STATE_FILE_ANL, "w") as f:
                json.dump(
                    {
                        "audio_collection_dir": "",
                        "save_emap_location": "",
                        "emap_name": "",
                    },
                    f,
                )

        a = App(0)
        a.widget.mainloop()
