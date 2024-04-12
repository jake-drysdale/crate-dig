import sys
import tkinter as tk
from tkinter import StringVar, IntVar, HORIZONTAL, END, Tk, Frame
from tkinter import filedialog, messagebox
from tkinter.ttk import Notebook

from sample_finder_SA_inter import (
    load_embeddings_index,
    process_new_audio_sample,
    find_wav_files,
    build_embeddings_index,
    save_embeddings_index,
)
import os
import argparse
import customtkinter


customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("dark-blue")


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
    process_new_audio_sample(
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
                "font": (self.default_theme["font"], self.default_theme["font_size"], "bold"),
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
        
        if parent == 0:
            self.widget = Tk()
            self.widget.title("Sample Finder")
            self.widget.geometry("500x560")
        else:
            self.widget = Frame(parent)
            self.widget.place(x=0, y=0, width=500, height=560)

        offset = 10

        self.input_type_var = StringVar()
        self.n_samples_var = IntVar()
        self.destination_folder_var = StringVar()
        self.embedding_map_dir_var = StringVar()

        self.audio_collection_var = StringVar()
        self.emap_name_entry = StringVar(value="embeddings")

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

                n_samples = int(self.n_samples_var.get())
                destination_folder = self.destination_folder_var.get()
                embedding_map_dir = self.embedding_map_dir_var.get()

                args = CLIArgs(
                    input_value,
                    n_samples,
                    destination_folder,
                    embedding_map_dir,
                    is_text=(input_type == "Text"),
                )
                run_sample_finder_cli(args)

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
            emap_name = self.library_name.get()
            save_emap_location = self.save_emap_location_entry.get()

            if not audio_collection_dir or not emap_name or not save_emap_location:
                messagebox.showwarning("Warning", "Please fill in all required fields.")
                return

            save_emap_full_path = os.path.join(save_emap_location, emap_name)
            os.makedirs(save_emap_full_path, exist_ok=True)

            try:
                wav_files = find_wav_files(audio_collection_dir, file_type)
                embeddings_index, path_map = build_embeddings_index(
                    wav_files, os.path.join(save_emap_full_path, "embeddings_list.npy")
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

        self.app_notebook = Notebook(self.widget)
        self.app_notebook.place(x=0, y=0, width=500, height=560)

        self.sample_finder_tab = Frame(self.app_notebook)
        self.sample_finder_tab.configure(bg=self.default_theme["bg_accent"])
        self.sample_finder_tab.place(x=0, y=0, width=500, height=560)

        self.analyse_new_library_tab = Frame(self.app_notebook)
        self.analyse_new_library_tab.configure(bg=self.default_theme["bg_accent"])
        self.analyse_new_library_tab.place(x=0, y=0, width=500, height=560)

        # --------------------- Sample Finder ---------------------
        self.input_mode_notebook = Notebook(self.sample_finder_tab)
        self.input_mode_notebook.place(x=8, y=66, width=480, height=460)

        self.search_by_text_tab = Frame(self.input_mode_notebook)
        self.search_by_text_tab.configure(bg=self.default_theme["bg_accent"])
        self.search_by_text_tab.place(x=0, y=0, width=476, height=372)

        self.search_for_samples_label = customtkinter.CTkLabel(
            self.sample_finder_tab,
            text="Search for Samples",
            **self.common_configs["labelLarge"],
        )
        self.search_for_samples_label.place(x=18, y=6)

        self.text_prompt_label = customtkinter.CTkLabel(
            self.search_by_text_tab,
            text="Text Prompt",
            **self.common_configs["label"],
            width=210,
            height=22,
        )
        self.text_prompt_label.place(x=20, y=10 + offset)
        self.text_prompt_entry = customtkinter.CTkEntry(
            self.search_by_text_tab,
            **self.common_configs["entry"],
            width=440,
            height=22,
        )
        self.text_prompt_entry.place(x=18, y=44 + offset)

        self.n_samples_label = customtkinter.CTkLabel(
            self.search_by_text_tab,
            text="Number of samples to retrieve",
            **self.common_configs["label"],
            width=300,
            height=22,
        )
        self.n_samples_label.place(x=20, y=86 + offset)

        self.n_samples_text_slider = customtkinter.CTkSlider(
            self.search_by_text_tab,
            from_=0,
            to=100,
            orientation=HORIZONTAL,
            fg_color=self.default_theme["bg_dark"],
            cursor="arrow",
            state="normal",
            width=320,
            height=22,
            variable=self.n_samples_var,
        )
        self.n_samples_text_slider.place(x=138, y=120 + offset)
        self.n_samples_text_textbox = customtkinter.CTkEntry(
            self.search_by_text_tab,
            **self.common_configs["entry"],
            width=110,
            height=22,
            textvariable=self.n_samples_var,
        )
        self.n_samples_text_textbox.place(x=20, y=120 + offset)

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
            width=320,
            height=22,
            textvariable=self.destination_folder_var,
        )
        self.destination_folder_text_entry.place(x=20, y=188 + offset * 2)
        self.exportdirbutton = customtkinter.CTkButton(
            self.search_by_text_tab,
            **self.common_configs["buttonBrowse"],
            width=110,
            height=22,
            command=lambda: browse_folder(self.destination_folder_text_entry),
        )
        self.exportdirbutton.place(x=350, y=188 + offset * 2)

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
            width=320,
            height=22,
            textvariable=self.embedding_map_dir_var,
        )
        self.liblocentry.place(x=20, y=250 + offset * 3)
        self.liblocbrowse = customtkinter.CTkButton(
            self.search_by_text_tab,
            **self.common_configs["buttonBrowse"],
            width=110,
            height=22,
            command=lambda: browse_folder(self.liblocentry),
        )
        self.liblocbrowse.place(x=350, y=250 + offset * 3)

        self.searchbytextbutton = customtkinter.CTkButton(
            self.search_by_text_tab,
            text="Run Sample Finder",
            **self.common_configs["buttonMain"],
            width=300,
            height=44,
            command=lambda: validate_and_run("text"),
        )
        self.searchbytextbutton.place(x=90, y=300 + offset * 5)
        self.onHover(self.searchbytextbutton)

        self.input_mode_notebook.add(self.search_by_text_tab, text="Search By Text")

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
            width=320,
            height=22,
        )
        self.audio_file_entry.place(x=20, y=44 + offset)
        self.base_audio_browse = customtkinter.CTkButton(
            self.search_by_audio_tab,
            **self.common_configs["buttonBrowse"],
            width=110,
            height=22,
            command=lambda: browse_file(self.audio_file_entry),
        )
        self.base_audio_browse.place(x=350, y=44 + offset)

        self.n_samples_audio_label = customtkinter.CTkLabel(
            self.search_by_audio_tab,
            text="Number of samples to retrieve",
            **self.common_configs["label"],
            width=300,
            height=22,
        )
        self.n_samples_audio_label.place(x=20, y=86 + offset)
        self.n_samples_audio_slider = customtkinter.CTkSlider(
            self.search_by_audio_tab,
            from_=0,
            to=100,
            orientation=HORIZONTAL,
            fg_color=self.default_theme["bg_dark"],
            cursor="arrow",
            state="normal",
            width=320,
            height=22,
            variable=self.n_samples_var,
        )
        self.n_samples_audio_slider.place(x=138, y=120 + offset)
        self.n_samples_audio_textbox = customtkinter.CTkEntry(
            self.search_by_audio_tab,
            **self.common_configs["entry"],
            width=110,
            height=22,
            textvariable=self.n_samples_var,
        )
        self.n_samples_audio_textbox.place(x=20, y=120 + offset)

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
            width=320,
            height=22,
            textvariable=self.destination_folder_var,
        )
        self.destination_folder_audio_entry.place(x=20, y=188 + offset * 2)
        self.export_dir_button_audio = customtkinter.CTkButton(
            self.search_by_audio_tab,
            **self.common_configs["buttonBrowse"],
            width=110,
            height=22,
            command=lambda: browse_folder(self.destination_folder_audio_entry),
        )
        self.export_dir_button_audio.place(x=350, y=188 + offset * 2)

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
            width=320,
            height=22,
            textvariable=self.embedding_map_dir_var,
        )
        self.liblocentry_audio.place(x=20, y=250 + offset * 3)
        self.liblocbrowse_audio = customtkinter.CTkButton(
            self.search_by_audio_tab,
            **self.common_configs["buttonBrowse"],
            width=110,
            height=22,
            command=lambda: browse_folder(self.liblocentry),
        )
        self.liblocbrowse_audio.place(x=350, y=250 + offset * 3)

        self.searchbyaudio_button = customtkinter.CTkButton(
            self.search_by_audio_tab,
            text="Run Sample Finder",
            **self.common_configs["buttonMain"],
            width=300,
            height=44,
            command=lambda: validate_and_run("audio"),
        )
        self.searchbyaudio_button.place(x=90, y=300 + offset * 5)
        self.onHover(self.searchbyaudio_button)

        self.input_mode_notebook.add(self.search_by_audio_tab, text="Search By Audio")

        self.app_notebook.add(self.sample_finder_tab, text="Sample Finder")

        # --------------------- Analyse New Library ---------------------
        self.extraction_notebook = Notebook(self.analyse_new_library_tab)
        self.extraction_notebook.place(x=8, y=66, width=480, height=460)

        self.embedding_extraction_tab = Frame(self.extraction_notebook)
        self.embedding_extraction_tab.configure(bg=self.default_theme["bg_accent"])
        self.embedding_extraction_tab.place(x=0, y=0, width=476, height=372)

        self.analyse_new_library_label = customtkinter.CTkLabel(
            self.analyse_new_library_tab,
            text="Analyse A New Library",
            **self.common_configs["labelLarge"],
        )
        self.analyse_new_library_label.place(x=18, y=6)

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
            width=320,
            height=22,
            textvariable=self.audio_collection_var,
        )
        self.audio_collection_entry.place(x=20, y=44 + offset)
        self.libpath_browse_button = customtkinter.CTkButton(
            self.embedding_extraction_tab,
            **self.common_configs["buttonBrowse"],
            width=110,
            height=22,
            command=lambda: browse_folder(self.audio_collection_entry),
        )
        self.libpath_browse_button.place(x=350, y=44 + offset)

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
            width=320,
            height=22,
        )
        self.save_emap_location_entry.place(x=20, y=120 + offset)
        self.libindex_savepath_button = customtkinter.CTkButton(
            self.embedding_extraction_tab,
            **self.common_configs["buttonBrowse"],
            width=110,
            height=22,
            command=lambda: browse_folder(self.save_emap_location_entry),
        )
        self.libindex_savepath_button.place(x=350, y=120 + offset)

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
            width=440,
            height=22,
        )
        self.library_name.place(x=20, y=188 + offset * 2)

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
            width=110,
            height=22,
            values=["any", ".wav", ".flac", ".mp3"],
        )
        self.file_type_entry.place(x=350, y=250 + offset * 3)

        self.analyse_button = customtkinter.CTkButton(
            self.embedding_extraction_tab,
            text="Analyze and Save Collection",
            **self.common_configs["buttonMain"],
            width=340,
            height=44,
            command=analyze_audio_collection,
        )
        self.analyse_button.place(x=90, y=300 + offset * 5)
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
        a = App(0)
        a.widget.mainloop()
