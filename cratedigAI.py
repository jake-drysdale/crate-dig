print("Importing modules...")
import traceback
import asset_downloader
import os
import sys
import io
from os import environ

environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"


def get_application_dir():
    """
    This function returns the directory where the executable is running
    or the script file in a development environment.
    """
    if getattr(sys, "frozen", False):
        # If the application is run as a bundled executable.
        application_path = os.path.dirname(sys.executable)
    else:
        # If the application is run in a development environment.
        application_path = os.path.dirname(os.path.abspath(__file__))

    return application_path


basepath = get_application_dir()

if not os.path.exists(os.path.join(basepath, "assets")):
    print("Assets not found, downloading assets...")
    asset_downloader.download_assets(basepath)

from datetime import timedelta
import json
import customtkinter
from PIL import Image
from pprint import pprint
from tkinter import DoubleVar, StringVar, IntVar, Variable, END
from tkinter import filedialog, messagebox
import mutagen
from pygame import mixer
from utils import playlist as pl
from utils.inference import (
    load_embeddings_index,
    process_new_audio_sample,
    process_iterative_samples,
    find_wav_files,
    build_embeddings_index,
    save_embeddings_index,
)

# -------------------------------- Constants --------------------------------
UINAME = "CrateDig"
AUDIO_FORMATS = (".wav", ".flac", ".mp3")
REKORDBOX_EXT = ".xml"
M3U_EXT = ".m3u"
buttonfontparams = {"size": 14, "weight": "normal"}
labelfontparams = {"size": 16, "weight": "bold"}
XPAD = (10, 10)
YPAD = (10, 20)


UserLibraryPath = os.path.join(basepath, "UserLibrary")

theme_file_path = os.path.join(basepath, "assets", "theme.json")
customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(theme_file_path)  # Adjusted to use the full path


LAST_STATE = os.path.join(UserLibraryPath, "state", "state.json")
DEFAULTS = {
    "AnalysedLibraries": [],
    "LastUsedLibrary": "",
    "UserLibraryPath": UserLibraryPath,
    "PlaylistExportPath": os.path.join(UserLibraryPath, "playlists"),
    "EmbeddingsExportPath": os.path.join(UserLibraryPath, "embeddings"),
    "ExportFilesToPath": os.path.join(UserLibraryPath, "exports"),
    "NMAX": 20,
    "init_size": f"{1400}x{800}",
}

DEBUG = sys.argv[-1] == "--debug"


def startup():
    print(
        f"""
   _____           _       _____  _                _____ 
  / ____|         | |     |  __ \(_)         /\   |_   _|
 | |     _ __ __ _| |_ ___| |  | |_  __ _   /  \    | |  
 | |    | '__/ _` | __/ _ \ |  | | |/ _` | / /\ \   | |  
 | |____| | | (_| | ||  __/ |__| | | (_| |/ ____ \ _| |_ 
  \_____|_|  \__,_|\__\___|_____/|_|\__, /_/    \_\_____|
                                     __/ |               
                                    |___/                
          
Welcome to CrateDig! This is a tool to search through your music library using text prompts or audio samples.
To get started, please select a folder containing your music library and click 'Analyze and Save Collection'.
This will create an embeddings index of your music library which will be used for searching.

Supported audio formats: .wav, .flac, .mp3          
Keep this terminal open to see debug information and error messages.
"""
    )
    if not os.path.exists(UserLibraryPath):
        os.makedirs(UserLibraryPath, exist_ok=True)
    if not os.path.exists(os.path.join(UserLibraryPath, "state")):
        os.makedirs(os.path.join(UserLibraryPath, "state"), exist_ok=True)
    if not os.path.exists(os.path.join(UserLibraryPath, "playlists")):
        os.makedirs(os.path.join(UserLibraryPath, "playlists"), exist_ok=True)
    if not os.path.exists(os.path.join(UserLibraryPath, "embeddings")):
        os.makedirs(os.path.join(UserLibraryPath, "embeddings"), exist_ok=True)
    # export isnt used yet
    if not os.path.exists(os.path.join(UserLibraryPath, "exports")):
        os.makedirs(os.path.join(UserLibraryPath, "exports"), exist_ok=True)


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


class Icons:
    def __init__(self):
        self.play = customtkinter.CTkImage(
            dark_image=Image.open(os.path.join(basepath, "assets", "play-button.png")),
            light_image=Image.open(os.path.join(basepath, "assets", "play-button.png")),
            size=(30, 30),
        )
        self.pause = customtkinter.CTkImage(
            dark_image=Image.open(os.path.join(basepath, "assets", "pause-button.png")),
            light_image=Image.open(
                os.path.join(basepath, "assets", "pause-button.png")
            ),
            size=(30, 30),
        )


icons = Icons()

mixer.init()

channel = mixer.find_channel()
channel.set_volume(0.7)



class Track(customtkinter.CTkFrame):
    """
    Frame that gets the album art of the track along with the id3 tags and displays them as a long card
    """

    def __init__(
        self,
        master,
        track_path,
        track_number,
        stop_all,
        stop_all_after=None,
        cancel_current_running=None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.track_path = track_path
        self.track_number = track_number
        self.track_tags = self.get_tags()
        self.duration = mutagen.File(self.track_path).info.length
        if self.duration:
            if self.duration > 3600:
                self.duration = str(timedelta(seconds=self.duration))
            else:
                self.duration = str(timedelta(seconds=self.duration)).split(".")[0][2:]
        self.album_art = self.get_album_art()
        self.playing = False
        self.stop_all = stop_all
        self.stop_all_after = stop_all_after
        self.cancel_current_running = cancel_current_running
        self.audio = None
        self.channel = mixer.Channel(0)
        self.create_widgets()

    def get_tags(self):

        tags = {"title": "Unknown Title", "artist": "Unknown Artist"}

        audio = mutagen.File(self.track_path)
        if audio is not None:
            try:
                tagdict = getattr(
                    audio.tags,
                    "as_dict",
                    lambda: {
                        "title": audio.get("TIT2").text,
                        "artist": audio.get("TPE1").text,
                        "album": audio.get("TALB").text,
                    },
                )()

                for key in tagdict:
                    if len(tagdict[key]) > 1:
                        tags[key] = ", ".join(tagdict[key])
                    else:
                        tags[key] = tagdict[key][0]
            except Exception as e:
                print(f"Error getting tags:{self.track_path} {e}")
                print(traceback.format_exc())
                tags = {
                    "title": os.path.basename(self.track_path),
                    "artist": "",
                    "album": os.path.dirname(self.track_path),
                }

        return tags

    def ellipsize(self, text, length=50):
        if len(text) > length:
            return text[:length] + "..."
        return text

    def get_album_art(self):
        audio = mutagen.File(self.track_path)
        if audio is not None:

            if getattr(audio, "pictures", None) is not None and len(audio.pictures) > 0:
                return Image.open(io.BytesIO(audio.pictures[0].data))

            else:
                imgs = [
                    img
                    for img in os.listdir(os.path.dirname(self.track_path))
                    if img.endswith((".jpg", ".png", ".jpeg"))
                ]
                if len(imgs) > 0:
                    return Image.open(
                        os.path.join(os.path.dirname(self.track_path), imgs[0])
                    )
                else:
                    return Image.open(os.path.join(basepath, "assets", "logo.png"))

        return None

    def play(self):

        if self.playing:
            self.stop_all()
            self.cancel_current_running()
            self.play_button.configure(image=icons.play)
            self.playing = False
            if DEBUG:
                print("trying to stop", self.track_path, self.playing)

        else:
            self.cancel_current_running()
            self.stop_all()
            self.audio = mixer.Sound(self.track_path)
            self.channel.play(self.audio)
            self.stop_all_after(self.audio.get_length(), self.track_number - 1)
            self.play_button.configure(image=icons.pause)
            self.playing = True
            if DEBUG:
                print("trying to play", self.track_path, self.playing)

    def stop(self):
        if self.audio:
            self.channel.stop()
            self.audio = None

    def create_widgets(self):
        self.grid_rowconfigure(0, weight=0)
        # for i in range(1, 4):
        #     self.grid_columnconfigure(i, weight=1)
        self.grid_columnconfigure(4, weight=1)
        self.album_art_image = customtkinter.CTkImage(
            dark_image=self.album_art, light_image=self.album_art, size=(50, 50)
        )
        self.album_art_label = customtkinter.CTkLabel(
            self,
            image=self.album_art_image,
            text="",
            # fg_color="#ffdd00",
        )
        self.album_art_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.track_title_label = customtkinter.CTkLabel(
            self,
            text=self.ellipsize(self.track_tags.get("title", "Unknown Title")),
            font=customtkinter.CTkFont(size=16, weight="bold"),
            # fg_color="#ffdd00",
        )
        self.track_title_label.grid(row=0, column=1, padx=(0, 10), sticky="w")

        self.track_artist_label = customtkinter.CTkLabel(
            self,
            text=(
                self.ellipsize(
                    self.track_tags.get("artist", "Unknown Artist")
                    + " • "
                    + self.track_tags.get("album", "Unknown Album")
                )
            ),
            font=customtkinter.CTkFont(size=14),
            text_color="gray",
            # fg_color="#ff0000",
        )
        self.track_artist_label.grid(row=0, column=2, padx=(0, 10), sticky="w")

        # self.track_album_label = customtkinter.CTkLabel(
        #     self, text=self.track_tags.get("album", "Unknown Album")
        # )
        # self.track_album_label.grid(row=2, column=1, sticky="w")

        self.track_dur_label = customtkinter.CTkLabel(
            self,
            text=self.duration,
            # fg_color="green",
        )
        self.track_dur_label.grid(row=0, column=3, padx=(0, 10), sticky="w")

        self.play_button = customtkinter.CTkButton(
            self,
            width=30,
            height=30,
            text="",
            image=icons.play,
            fg_color="transparent",
            # bg_color="transparent",
            # text_color="white",
            # hover_color="transparent",
            hover=False,
            font=customtkinter.CTkFont(size=16),
            command=self.play,
        )
        self.play_button.grid(row=0, column=4, padx=(10, 0), sticky="e")


class Playlist(customtkinter.CTkFrame):
    """
    Frame that displays a list of tracks as cards
    """

    def __init__(
        self,
        master,
        tracks: list,
        stop_all_after=None,
        cancel_current_running=None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.tracks = tracks
        self.track_frames = []
        self.stop_all_after = stop_all_after
        self.cancel_current_running = cancel_current_running
        self.current_playing = None
        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        for index, track in enumerate(self.tracks):
            track_frame = Track(
                self,
                track,
                index + 1,
                stop_all=self.stop_all,
                stop_all_after=self.stop_all_after,
                cancel_current_running=self.cancel_current_running,
            )
            track_frame.grid(row=index, column=0, padx=0, pady=(0, 10), sticky="nsew")
            self.track_frames.append(track_frame)

    def stop_all(self):
        mixer.stop()
        # channel.stop()

        for track in self.track_frames:
            track.stop()
            track.playing = False
            track.play_button.configure(image=icons.play)

    def redraw(self):
        # self.tracks = self.tracks.get()
        self.track_frames = []
        for widget in self.winfo_children():
            widget.destroy()
        self.create_widgets()


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.load_state()
        self.running = None
        self.debug = DEBUG

        self.progress_var = DoubleVar(value=0.0)
        self.library_visible = Variable(value=False)

        # configure window
        self.title(UINAME)
        self.geometry(self.init_size)

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # -------------------------------- Sidebar Frame --------------------------------
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        gap_index = 8
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(gap_index, weight=8)

        logo_path = os.path.join(basepath, "assets", "logo.png")

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
        self.playlist_mode_label.grid(
            row=4, column=0, padx=20, pady=(10, 0), sticky="w"
        )
        self.playlist_mode = Variable(value="Any close match")
        self.playlist_mode_switch = customtkinter.CTkSwitch(
            self.sidebar_frame,
            textvariable=self.playlist_mode,
            variable=self.playlist_mode,
            onvalue="Best next track",
            offvalue="Any close match",
            switch_width=45,
            font=customtkinter.CTkFont(family="Mono", **buttonfontparams),
        )
        self.playlist_mode_switch.grid(row=5, column=0, padx=20, pady=0, sticky="w")

        self.volume = IntVar(value=70)
        self.volume_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Volume", anchor="w"
        )
        self.volume_label.grid(row=6, column=0, padx=20, pady=(10, 0), sticky="w")
        self.volume_slider = customtkinter.CTkSlider(
            self.sidebar_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            variable=self.volume,
            height=22,
            command=self.set_volume,
            width=210 - 40 + 4,
        )
        self.volume_slider.grid(row=7, column=0, padx=20, pady=10, sticky="w")
        # gap

        self.lib_n_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Selected Library",
            anchor="w",
            # font=customtkinter.CTkFont(size=22, weight="bold"),
        )
        self.lib_n_label.grid(
            row=gap_index + 1, column=0, padx=20, pady=(10, 0), sticky="w"
        )
        self.lib_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            textvariable=self.LastUsedLibrary,
            anchor="w",
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )
        self.lib_label.grid(
            row=gap_index + 2, column=0, padx=20, pady=(0, 0), sticky="w"
        )
        self.sidebar_button_1 = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Show Library Info",
            command=self.toggle_library_visibility,
            font=customtkinter.CTkFont(**buttonfontparams),
            width=210 - 40,
        )
        self.sidebar_button_1.grid(
            row=gap_index + 3, column=0, padx=20, pady=10, sticky="w"
        )

        self.scaling_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="UI Scaling:", anchor="w"
        )
        self.scaling_label.grid(
            row=gap_index + 4, column=0, padx=20, pady=(10, 0), sticky="w"
        )
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["100%", "80%", "90%", "110%", "120%"],
            command=self.change_scaling_event,
            width=210 - 40,
        )
        self.scaling_optionemenu.grid(
            row=gap_index + 5, column=0, padx=20, pady=(10, 20), sticky="w"
        )

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
            text="Number of Matches:",
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

        self.result_scrollable_frame = customtkinter.CTkScrollableFrame(
            self.mainframe,
            label_text="Results:",
        )
        self.result_scrollable_frame.grid(
            row=self.rel + 4,
            column=0,
            columnspan=2,
            padx=20,
            pady=(10, 10),
            sticky="nsew",
        )
        self.result_scrollable_frame.grid_columnconfigure(0, weight=1)

        # self.playlist_textbox = customtkinter.CTkTextbox(
        #     self.result_scrollable_frame,
        #     wrap="none",
        #     font=customtkinter.CTkFont(size=16),
        # )
        # self.playlist_textbox.grid(
        #     row=0,
        #     column=0,
        #     # columnspan=2,
        #     # padx=20,
        #     pady=(0, 20),
        #     sticky="ew",
        # )

        self.result_tracks = []
        self.playlist = Playlist(
            self.result_scrollable_frame,
            self.result_tracks,
            stop_all_after=self.stop_all_after,
            cancel_current_running=self.cancel_current_running,
        )

        self.playlist.grid(
            row=0,
            column=0,
            padx=0,
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
            text="Analyze Library",
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
            if self.debug:
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
                self.set_result(self.playlist, result=result)
            if self.debug:
                print(result)

            self.save_playlist(result, platform="m3u")
            # messagebox.showinfo("Success", "Operation Completed Successfully")
            self.save_state()
        except ValueError:
            messagebox.showerror("Error", "Number of samples must be an integer.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            raise e

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

            yn = messagebox.askyesno(
                "Confirmation",
                f"Found {len(wav_files)} audio files. Do you want to proceed?",
            )
            if not yn:
                return

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

            messagebox.showinfo(
                "Success",
                f"Analysis completed. Embeddings saved to {full_emap_path}.",
            )
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
        self.init_size = load_variable("init_size")
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
            "init_size": self.init_size,
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
        res_playlist = pl.Playlist(result, savepath=playlist_path)
        res_playlist.write(
            platform,
            pathfunc=lambda x: x,
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

    def set_result(self, playlist_widget: Playlist, result):
        playlist_widget.stop_all()
        playlist_widget.tracks = result
        playlist_widget.redraw()

    def update_entries_number(self, entries: list, new_value):
        for entry in entries:
            entry.set(new_value)

    def hide_library_info(self):
        # hide the library sidebar frame
        self.library_visible.set(False)
        self.library_sidebar.grid_remove()

    def show_library_info(self):
        # show the library sidebar frame
        self.library_visible.set(True)
        self.library_sidebar.grid()

    def toggle_library_visibility(self):
        visible = self.library_visible.get()
        if visible:
            self.hide_library_info()
        else:
            self.show_library_info()

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

    def play_next(self, index=None):
        print("playing next track", index)
        if index is None:
            return
        if index < len(self.playlist.track_frames):
            self.playlist.track_frames[index].play()

    def stop_all_after(self, duration, index=None):
        if DEBUG:
            print("stopping all after", duration)

        def stop_all(after):
            if DEBUG:
                print("stopping all", after)
            self.playlist.stop_all()
            self.play_next(index + 1)

        self.running = self.after(round(duration) * 1000, lambda: stop_all(duration))

    def cancel_current_running(self):

        if self.running:
            if DEBUG:
                print("cancelling")
            self.after_cancel(self.running)

    def set_volume(self, volume):
        channel.set_volume(int(volume) / 100)


if __name__ == "__main__":

    # make UserLibrary directories
    startup()

    app = App()
    app.wm_iconbitmap(os.path.join(basepath, "assets", "logo.ico"))
    # tell user to analyse a library if they haven't done so yet
    if os.path.exists(LAST_STATE) and len(app.AnalysedLibraries.get()) > 0:
        app.hide_library_info()
        app.library_visible.set(False)
    else:
        # app.show_library_info()
        app.library_visible.set(True)

    app.mainloop()
