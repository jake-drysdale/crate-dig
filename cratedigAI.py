from pprint import pprint
import json
from tkinter import DoubleVar, StringVar, IntVar, Variable, END
from tkinter import filedialog, messagebox

from sample_finder_SA_inter import (
    load_embeddings_index,
    process_new_audio_sample,
    process_iterative_samples,
    find_wav_files,
    build_embeddings_index,
    save_embeddings_index,
)

from utils import playlist

# from sample_finder_SA_inter import process_iterative_samples as process_new_audio_sample
import os
import argparse
import customtkinter
from PIL import Image
import sys

# Check if running as a PyInstaller bundle
if getattr(sys, "frozen", False):
    application_path = sys._MEIPASS  # The path to the temporary folder where PyInstaller unpacks your bundle
else:
    application_path = os.path.dirname(os.path.abspath(__file__))  # The directory of your script

# Define the full path to ableton.json
theme_file_path = os.path.join(application_path, "ableton.json")

# Use the dynamically determined path for setting the theme
customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(theme_file_path)  # Adjusted to use the full path

UINAME = "CrateDig"

UserLibraryPath = __file__.replace("crateDigUI.py", "UserLibrary")
LAST_STATE = os.path.join(UserLibraryPath, "state", "state.json")
AUDIO_FORMATS = (".wav", ".flac", ".mp3")
REKORDBOX_EXT = ".xml"
M3U_EXT = ".m3u"
buttonfontparams = {"size": 14, "weight": "normal"}
labelfontparams = {"size": 16, "weight": "bold"}

XPAD = (10, 10)
YPAD = (10, 20)


class CLIArgs:
    def __init__(
        self,
        input_value,
        n_samples,
        destination_folder,
        embedding_map_dir,
        is_text=True,
        as_playlist=False,
    ):
        self.input_value = input_value
        self.n_samples = n_samples
        self.destination_folder = destination_folder
        self.embedding_map_dir = embedding_map_dir
        self.is_text = is_text
        self.as_playlist = as_playlist

    def __repr__(self) -> str:
        return f"CLIArgs(input_value={self.input_value}, n_samples={self.n_samples}, destination_folder={self.destination_folder}, embedding_map_dir={self.embedding_map_dir}, is_text={self.is_text} as_playlist={self.as_playlist})"


def run_sample_finder_cli(args: CLIArgs):

    embeddings_index, path_map = load_embeddings_index(args.embedding_map_dir)
    print(args)
    if args.as_playlist:
        return process_iterative_samples(
            args.input_value,
            embeddings_index,
            path_map,
            args.n_samples,
            args.destination_folder,
            args.is_text,
        )
    return process_new_audio_sample(
        args.input_value,
        embeddings_index,
        path_map,
        args.n_samples,
        args.destination_folder,
        args.is_text,
    )


DEFAULTS = {
    "AnalysedLibraries": [],
    "LastUsedLibrary": "",
    "UserLibraryPath": UserLibraryPath,
    "PlaylistExportPath": os.path.join(UserLibraryPath, "playlists"),
    "EmbeddingsExportPath": os.path.join(UserLibraryPath, "embeddings"),
    "ExportFilesToPath": os.path.join(UserLibraryPath, "exports"),
    "NMAX": 20,
}


class App(customtkinter.CTk):
    def __init__(self, debug=True):
        super().__init__()
        self.load_state()
        self.debug = debug

        def get_library_path():
            print(self.LastUsedLibrary.get())
            print(self.input_mode.get())
            for libname, libpath in self.AnalysedLibraries.get():
                if libname == self.LastUsedLibrary.get():
                    return libpath
            return ""

        self.progress_var = DoubleVar(value=0.0)
        self.library_visible = Variable(value=False)
        # if last_state_sf.get("embedding_map_dir", "") == "":
        #     audio_collection_dir = last_state_anl.get("audio_collection_dir", "")
        #     library_name = last_state_anl.get("emap_name", "")
        #     if audio_collection_dir != "" and library_name != "":
        #         last_state_sf["embedding_map_dir"] = os.path.join(
        #             last_state_anl["save_emap_location"], library_name
        #         )
        # self.input_type_var = StringVar()
        # self.n_samples_var = StringVar(value="1")

        # self.destination_folder_var = StringVar(
        #     value=last_state_sf.get("destination_folder", "")
        # )
        # self.embedding_map_dir_var = StringVar(
        #     value=last_state_sf.get("embedding_map_dir", "")
        # )
        # self.audio_collection_var = StringVar(
        #     value=last_state_anl.get("audio_collection_dir", "")
        # )
        # self.save_emap_location_var = StringVar(
        #     value=last_state_anl.get("save_emap_location", "")
        # )
        # self.library_name_var = StringVar(value=last_state_anl.get("emap_name", ""))

        # configure window
        self.title(UINAME)
        self.geometry(f"{1100}x{580}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # -------------------------------- Sidebar Frame --------------------------------
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        gap_index = 7
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(gap_index, weight=8)

        # Check if running as a PyInstaller bundle
        if getattr(sys, "frozen", False):
            application_path = sys._MEIPASS  # The path to the temporary folder where PyInstaller unpacks your bundle
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))  # The directory of your script

        # Define the full path to logo.png
        logo_path = os.path.join(application_path, 'assets', 'logo.png')

        logo_image = Image.open(logo_path)
        self.logo = customtkinter.CTkImage(
            dark_image=logo_image, light_image=logo_image, size=(100, 100)
        )
        self.logo_image_label = customtkinter.CTkLabel(
            self.sidebar_frame, image=self.logo, text=""
        )
        self.logo_image_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text=UINAME,
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=1, column=0, padx=20, pady=(0, 10))

        # UI switches

        self.input_mode_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Search by: text/audio", anchor="w"
        )
        self.input_mode_label.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        self.input_mode = Variable(value="text")
        self.input_mode_switch = customtkinter.CTkSwitch(
            self.sidebar_frame,
            textvariable=self.input_mode,
            variable=self.input_mode,
            onvalue="text",
            offvalue="audio",
            switch_width=45,
            command=self.switch_input_mode,
            font=customtkinter.CTkFont(**buttonfontparams),
        )
        self.input_mode_switch.grid(row=3, column=0, padx=20, pady=0, sticky="w")

        self.playlist_mode_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Sort by", anchor="w"
        )
        self.playlist_mode_label.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        self.playlist_mode = Variable(value="Any close match")
        self.playlist_mode_switch = customtkinter.CTkSwitch(
            self.sidebar_frame,
            textvariable=self.playlist_mode,
            variable=self.playlist_mode,
            onvalue= "Best next track",
            offvalue="Any close match",
            switch_width=45,
            font=customtkinter.CTkFont(family="Mono", **buttonfontparams),
        )
        self.playlist_mode_switch.grid(row=5, column=0, padx=20, pady=0, sticky="w")

        # gap

        self.lib_n_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Selected Library",
            anchor="w",
            # font=customtkinter.CTkFont(size=22, weight="bold"),
        )
        self.lib_n_label.grid(row=gap_index+1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.lib_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            textvariable=self.LastUsedLibrary,
            anchor="w",
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )
        self.lib_label.grid(row=gap_index+2, column=0, padx=20, pady=(0, 0), sticky="w")
        self.sidebar_button_1 = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Show Library Info",
            command=self.toggle_library_visibility,
            font=customtkinter.CTkFont(**buttonfontparams),
            width=210-40
        )
        self.sidebar_button_1.grid(row=gap_index+3, column=0, padx=20, pady=10, sticky="w")

        self.scaling_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="UI Scaling:", anchor="w"
        )
        self.scaling_label.grid(row=gap_index+4, column=0, padx=20, pady=(10, 0), sticky="w")
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["100%", "80%", "90%", "110%", "120%"],
            command=self.change_scaling_event,
            width=210-40
        )
        self.scaling_optionemenu.grid(row=gap_index+5, column=0, padx=20, pady=(10, 20), sticky="w")

        
        # -------------------------------- Main Frame --------------------------------


        self.mainframe = customtkinter.CTkFrame(self)
        self.mainframe.grid(
            row=0, column=1, rowspan=3, padx=XPAD, pady=(10, 10), sticky="nsew"
        )
        self.mainframe.grid_columnconfigure(0, weight=9)
        self.mainframe.grid_columnconfigure(1, weight=1)
        self.mainframe.grid_rowconfigure(0, weight=1)
        self.mainframe.grid_rowconfigure(5, weight=9)

        self.title_label = customtkinter.CTkLabel(
            self.mainframe,
            text="Search through your library",
            anchor="w",
            font=customtkinter.CTkFont(size=22, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.rel = 1
        # Text Prompt Entry
        self.text_prompt_label = customtkinter.CTkLabel(
            self.mainframe,
            text="Type A Text Prompt",
            anchor="w",
            font=customtkinter.CTkFont(**labelfontparams),
        )
        self.text_prompt_label.grid(
            row=self.rel + 0, column=0, padx=20, pady=(20, 10), sticky="w"
        )
        self.text_prompt_entry = customtkinter.CTkTextbox(
            self.mainframe,
            wrap="word",
            height=15,
        )
        self.text_prompt_entry.grid(
            row=self.rel + 1,
            column=0,
            columnspan=2,
            padx=20,
            pady=(0, 20),
            sticky="nsew",
        )

        # audio Prompt Entry
        self.audio_prompt_label = customtkinter.CTkLabel(
            self.mainframe,
            text="Pick an audio file to search with".title(),
            anchor="w",
            font=customtkinter.CTkFont(**labelfontparams),
        )
        self.audio_prompt_entry = customtkinter.CTkEntry(
            self.mainframe,
            # wrap="word",
            height=15,
        )
        self.browse_audio_button = customtkinter.CTkButton(
            self.mainframe,
            text="Browse",
            command=lambda: self.browse_file(self.audio_prompt_entry),
            font=customtkinter.CTkFont(**labelfontparams),
        )
        # grid set in switch_input_mode

        # number of samples
        self.n_samples_label = customtkinter.CTkLabel(
            self.mainframe,
            text="Number of Samples:",
            anchor="w",
            font=customtkinter.CTkFont(**labelfontparams),
        )
        self.n_samples_label.grid(
            row=self.rel + 2, column=0, padx=20, pady=(10, 0), sticky="w"
        )
        self.n_samples_var = StringVar(value=1)
        self.n_samples_slider_var = IntVar(value=1)
        self.n_samples_slider = customtkinter.CTkSlider(
            self.mainframe,
            from_=1,
            to=self.NMAX.get(),
            number_of_steps=len(range(1, self.NMAX.get() + 1)),
            variable=self.n_samples_slider_var,
            height=22,
            command=lambda x: self.update_entries_number(
                [self.n_samples_var], int(float(x))
            ),
        )
        self.n_samples_slider.grid(
            row=self.rel + 3, column=0, padx=(20, 0), pady=(0, 20), sticky="nsew"
        )
        self.n_samples_entry = customtkinter.CTkEntry(
            self.mainframe, textvariable=self.n_samples_var
        )
        self.n_samples_entry.grid(
            row=self.rel + 3, column=1, padx=20, pady=(0, 20), sticky="nsew"
        )

        self.result_label = customtkinter.CTkLabel(
            self.mainframe,
            text="Results:",
            anchor="w",
            font=customtkinter.CTkFont(**labelfontparams),
        )
        self.result_label.grid(
            row=self.rel + 4, column=0, padx=20, pady=(10, 10), sticky="w"
        )
        self.playlist_textbox = customtkinter.CTkTextbox(
            self.mainframe,
            wrap="none",
            font=customtkinter.CTkFont(size=16),
        )
        self.playlist_textbox.grid(
            row=self.rel + 5,
            column=0,
            columnspan=2,
            padx=20,
            pady=(0, 20),
            sticky="nsew",
        )

        self.search_button = customtkinter.CTkButton(
            master=self,
            text="Search",
            command=self.validate_and_run,
            font=customtkinter.CTkFont(**buttonfontparams),
        )
        self.search_button.grid(row=3, column=1, padx=10, pady=(0, 20), sticky="nsew")

        # -------------------------------- Library Sidebar --------------------------------

        self.library_sidebar = customtkinter.CTkFrame(self, width=500)
        self.library_sidebar.grid(
            row=0,
            rowspan=4,
            column=3,
            columnspan=2,
            padx=(0, 10),
            pady=YPAD,
            sticky="nsew",
        )

        self.library_sidebar_label = customtkinter.CTkLabel(
            self.library_sidebar,
            text="Your Analysed Libraries",
            font=customtkinter.CTkFont(size=20, weight="bold"),
            anchor="w",
        )
        self.library_sidebar_label.grid(
            row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w"
        )

        self.library_name_label = customtkinter.CTkLabel(
            self.library_sidebar, text="Analysed Libraries:", anchor="w"
        )
        self.library_name_label.grid(
            row=1, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="w"
        )
        self.library_name_entry = customtkinter.CTkOptionMenu(
            self.library_sidebar,
            variable=self.LastUsedLibrary,
            values=[libname for libname, libpath in self.AnalysedLibraries.get()],
            font=customtkinter.CTkFont(size=12),
            width=290,
            anchor="w",
        )
        self.library_name_entry.grid(
            row=2, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="w"
        )

        self.addnewliblabel = customtkinter.CTkLabel(
            self.library_sidebar,
            text="Add A New Library",
            font=customtkinter.CTkFont(size=20, weight="bold"),
            anchor="w",
        )
        self.addnewliblabel.grid(
            row=3, column=0, columnspan=2, padx=20, pady=(50, 10), sticky="w"
        )

        self.library_name_label = customtkinter.CTkLabel(
            self.library_sidebar, text="New Library Name:", anchor="w"
        )
        self.library_name_label.grid(
            row=4, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="w"
        )
        self.new_library_name_entry = customtkinter.CTkTextbox(
            self.library_sidebar,
            width=290,
            height=20,
            wrap="none",
        )
        self.new_library_name_entry.grid(
            row=5, column=0, columnspan=2, padx=(20, 0), pady=(10, 10), sticky="w"
        )

        self.library_path_label = customtkinter.CTkLabel(
            self.library_sidebar, text="New Library Path:", anchor="w"
        )
        self.library_path_label.grid(
            row=6, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="w"
        )
        self.library_path_entry = customtkinter.CTkTextbox(
            self.library_sidebar, width=200, height=20, wrap="none"
        )
        self.library_path_entry.grid(row=7, column=0, padx=(20, 0), pady=(10, 10))
        self.browse_button = customtkinter.CTkButton(
            self.library_sidebar,
            text="Browse",
            width=80,
            command=lambda: self.browse_folder(self.library_path_entry),
            font=customtkinter.CTkFont(**buttonfontparams),
        )
        self.browse_button.grid(row=7, column=1, padx=(10, 20), pady=(10, 10))

        self.libinfo_button = customtkinter.CTkButton(
            self.library_sidebar,
            text="Analyze and Save Collection",
            command=self.analyze_audio_collection,
            width=290,
            font=customtkinter.CTkFont(**buttonfontparams),
        )
        self.libinfo_button.grid(
            row=8,
            column=0,
            padx=20,
            pady=(10, 20),
            columnspan=2,
        )

        self.analysis_progressbar = customtkinter.CTkProgressBar(
            self.library_sidebar,
            width=290,
            height=20,
            variable=self.progress_var,
            mode="determinate",
            corner_radius=5,
        )
        self.analysis_progressbar.grid(
            row=9, column=0, padx=20, pady=(10, 20), columnspan=2, sticky="ew"
        )

    # -------------------------------- Actions --------------------------------

    def validate_and_run(self):
        """
        Validate the input fields and run the sample finder.
        """

        try:
            if self.input_mode.get() == "text":
                input_value = (
                    self.text_prompt_entry.get("1.0", END).strip().replace("\n", " ")
                )
            else:
                input_value = self.audio_prompt_entry.get().strip().replace("\n", "")
            print(input_value)
            if not input_value or input_value.strip() == "":
                messagebox.showerror(
                    "Error", "Please enter a text prompt or select an audio file."
                )
                return

            try:
                n_samples = int(self.n_samples_var.get())
            except ValueError:
                messagebox.showerror("Error", "Number of samples must be an integer.")
                self.n_samples_var.set("1")
                return
            destination_folder = self.ExportFilesToPath.get()
            embedding_map_dir = self.get_last_used_embeddings_dir()
            if not self.debug:
                pprint(self.get_current_state())
            args = CLIArgs(
                input_value,
                n_samples,
                destination_folder,
                embedding_map_dir,
                is_text=(self.input_mode.get() == "text"),
                as_playlist=(self.playlist_mode.get() == "Best next track"),
            )
            result = run_sample_finder_cli(args)
            # file location realtive to library folder indicated in AnalysedLibraries
            library_path = self.get_last_used_library_dir()

            if library_path or library_path != "":
                displayresult = [os.path.relpath(path, library_path) for path in result]
                self.textbox_set(self.playlist_textbox, displayresult)

            print(result)
            self.save_playlist(result, platform="m3u")
            messagebox.showinfo("Success", "Operation Completed Successfully")
            self.save_state()
        except ValueError:
            messagebox.showerror("Error", "Number of samples must be an integer.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def analyze_audio_collection(
        self,
    ):
        """
        Analyze the audio collection and save the embeddings index.
        """
        new_library_path = self.library_path_entry.get("1.0", END).strip()
        new_library_name = self.new_library_name_entry.get("1.0", END).strip()
        if new_library_name in [
            libname for libname, libpath in self.AnalysedLibraries.get()
        ]:
            messagebox.showwarning(
                "Warning",
                "Library with this name already exists. Please choose a different name.",
            )
            return

        default_emap_dir = self.EmbeddingsExportPath.get()

        if not new_library_path or not new_library_name or not default_emap_dir:
            messagebox.showwarning("Warning", "Please fill in all required fields.")
            return

        full_emap_path = os.path.join(default_emap_dir, new_library_name)

        os.makedirs(full_emap_path, exist_ok=True)

        try:
            wav_files = find_wav_files(new_library_path, AUDIO_FORMATS)
            embeddings_index, path_map = build_embeddings_index(
                wav_files,
                os.path.join(full_emap_path, "embeddings_list.npy"),
                self.analysis_progressbar,
                self.library_sidebar.update_idletasks,
            )
            save_embeddings_index(
                embeddings_index,
                path_map,
                os.path.join(full_emap_path, "embeddings.ann"),
                os.path.join(full_emap_path, "path_map.json"),
            )
            self.add_library_to_analyzed(new_library_name, new_library_path)

            # messagebox.showinfo(
            #     "Success",
            #     f"Analysis completed. Embeddings saved to {full_emap_path}.",
            # )
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # -------------------------------- State management --------------------------------

    def add_library_to_analyzed(self, library_name, library_path):
        AnalysedLibraries = self.AnalysedLibraries.get()
        self.AnalysedLibraries.set([*AnalysedLibraries, (library_name, library_path)])
        # update the optionmenu
        self.library_name_entry.configure(
            values=[libname for libname, libpath in self.AnalysedLibraries.get()]
        )
        # set the last used library to the new library
        self.LastUsedLibrary.set(library_name)
        self.save_state()
        messagebox.showinfo("Success", "Library added successfully.")

    def load_state(self, state_path=LAST_STATE):
        if os.path.exists(state_path):
            with open(state_path, "r", encoding="utf-8") as f:
                last_state = json.load(f)
        else:
            last_state = DEFAULTS

        def load_variable(key):
            return (
                last_state.get(key, "")
                if last_state.get(key, "") != ""
                else DEFAULTS[key]
            )

        self.AnalysedLibraries = Variable(value=load_variable("AnalysedLibraries"))
        self.LastUsedLibrary = Variable(value=load_variable("LastUsedLibrary"))
        self.UserLibraryPath = Variable(value=load_variable("UserLibraryPath"))
        self.PlaylistExportPath = Variable(value=load_variable("PlaylistExportPath"))
        self.EmbeddingsExportPath = Variable(
            value=load_variable("EmbeddingsExportPath")
        )
        self.NMAX = IntVar(value=load_variable("NMAX"))
        self.ExportFilesToPath = Variable(value=load_variable("ExportFilesToPath"))
        self.NewLibraryPath = StringVar(value="")

    def get_current_state(self):
        return {
            "AnalysedLibraries": self.AnalysedLibraries.get(),
            "LastUsedLibrary": self.LastUsedLibrary.get(),
            "UserLibraryPath": self.UserLibraryPath.get(),
            "PlaylistExportPath": self.PlaylistExportPath.get(),
            "EmbeddingsExportPath": self.EmbeddingsExportPath.get(),
            "ExportFilesToPath": self.ExportFilesToPath.get(),
            "NMAX": self.NMAX.get(),
        }

    def save_state(self, state_path=LAST_STATE):

        with open(state_path, "w") as f:
            json.dump(
                self.get_current_state(),
                f,
                indent=4,
            )

    def get_last_used_embeddings_dir(self):
        return os.path.join(self.EmbeddingsExportPath.get(), self.LastUsedLibrary.get())

    def get_last_used_library_dir(self):
        libpath = ""
        for libname, path in self.AnalysedLibraries.get():
            if libname == self.LastUsedLibrary.get():
                libpath = path
                break
        return libpath

    def save_playlist(self, result, platform="m3u"):
        if self.input_mode.get() == "text":
            input_value = self.text_prompt_entry.get("1.0", END).strip()
        else:
            input_value = os.path.basename(self.audio_prompt_entry.get().strip())

        playlist_name = (
            f"{self.LastUsedLibrary.get()}_{input_value}_{self.n_samples_var.get()}"
        )
        if platform == "rekordbox":
            playlist_name += REKORDBOX_EXT
        else:
            playlist_name += M3U_EXT

        playlist_path = os.path.join(self.PlaylistExportPath.get(), playlist_name)
        res_playlist = playlist.Playlist(result, savepath=playlist_path)
        res_playlist.write(
            platform,
            pathfunc=lambda x: x.replace(
                "/home/ali/beatoven/recordroom/", "E:\\Music\\calibre\\"
            ).replace("/", "\\"),
            uos="win",
        )
        messagebox.showinfo("Success", f"Playlist saved to {playlist_path}")

    # -------------------------------- UI Events --------------------------------

    def browse_folder(self, entry):
        """
        Browse for a folder and insert the path into the entry.
        """
        folder_selected = filedialog.askdirectory()
        if isinstance(entry, customtkinter.CTkTextbox):
            entry.delete("1.0", END)
            entry.insert("1.0", folder_selected)
        else:
            entry.delete(0, END)
            entry.insert(0, folder_selected)

    def browse_file(self, entry):
        """
        Browse for a file and insert the path into the entry.
        """
        file_selected = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.flac")]
        )
        if isinstance(entry, customtkinter.CTkTextbox):
            entry.delete("1.0", END)
            entry.insert("1.0", file_selected)
        else:
            entry.delete(0, END)
            entry.insert(0, file_selected)

    def textbox_set(self, textbox: customtkinter.CTkTextbox, text):
        textbox.delete("1.0", END)

        if type(text) == str:
            textbox.insert("1.0", text)
        elif type(text) == list:
            textbox.insert(
                "1.0",
                "\n".join(f"{index+1}. {path}" for index, path in enumerate(text)),
            )

    def update_entries_number(self, entries: list, new_value):
        for entry in entries:
            entry.set(new_value)

    def hide_library_info(self):
        # hide the library sidebar frame
        self.library_sidebar.grid_remove()

    def show_library_info(self):
        # show the library sidebar frame
        self.library_sidebar.grid()

    def toggle_library_visibility(self):
        visible = self.library_visible.get()
        if visible:
            self.hide_library_info()
            self.library_visible.set(False)
        else:
            self.show_library_info()
            self.library_visible.set(True)

    def switch_input_mode(self):
        if self.input_mode.get() == "text":
            self.text_prompt_label.grid()
            self.text_prompt_entry.grid()
            self.audio_prompt_label.grid_remove()
            self.audio_prompt_entry.grid_remove()
            self.browse_audio_button.grid_remove()
        else:
            self.text_prompt_label.grid_remove()
            self.text_prompt_entry.grid_remove()
            self.audio_prompt_label.grid(
                row=self.rel + 0, column=0, padx=20, pady=(20, 10), sticky="w"
            )
            self.audio_prompt_entry.grid(
                row=self.rel + 1, column=0, padx=(20, 0), pady=(0, 20), sticky="nsew"
            )
            self.browse_audio_button.grid(
                row=self.rel + 1, column=1, padx=(20, 20), pady=(0, 20), sticky="nsew"
            )

    def open_input_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(
            text="Type in a number:", title="CTkInputDialog"
        )
        print("CTkInputDialog:", dialog.get_input())

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)
        self.switch_input_mode()
        if self.library_visible.get():
            self.show_library_info()
        else:
            self.hide_library_info()


if __name__ == "__main__":
    if not os.path.exists(UserLibraryPath):
        os.makedirs(UserLibraryPath, exist_ok=True)
    if not os.path.exists(os.path.join(UserLibraryPath, "state")):
        os.makedirs(os.path.join(UserLibraryPath, "state"), exist_ok=True)
    if not os.path.exists(os.path.join(UserLibraryPath, "playlists")):
        os.makedirs(os.path.join(UserLibraryPath, "playlists"), exist_ok=True)
    if not os.path.exists(os.path.join(UserLibraryPath, "embeddings")):
        os.makedirs(os.path.join(UserLibraryPath, "embeddings"), exist_ok=True)
    if not os.path.exists(os.path.join(UserLibraryPath, "exports")):
        os.makedirs(os.path.join(UserLibraryPath, "exports"), exist_ok=True)
    if not os.path.exists(os.path.join(UserLibraryPath, "models")):
        os.makedirs(os.path.join(UserLibraryPath, "models"), exist_ok=True)
    # print(DEFAULTS)

    app = App()
    if os.path.exists(LAST_STATE) and len(app.AnalysedLibraries.get()) > 0:
        app.hide_library_info()
        app.library_visible.set(False)
    else:
        # app.show_library_info()
        app.library_visible.set(True)
    app.mainloop()