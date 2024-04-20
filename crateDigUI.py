import sys
import json
import tkinter as tk
from tkinter import DoubleVar, StringVar, IntVar, HORIZONTAL, END, Frame, Variable
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

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(
    "theme.json"
)  # Themes: "blue" (standard), "green", "dark-blue"

UserLibraryPath = __file__.replace("crateDigUI.py", "UserLibrary")
LAST_STATE = os.path.join(UserLibraryPath, "state", "state.json")
UINAME = "CrateDigAI"
AUDIO_FORMATS = (".wav", ".flac", ".mp3")


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


DEFAULTS = {
    "AnalysedLibraries": [],
    "LastUsedLibrary": "",
    "UserLibraryPath": UserLibraryPath,
    "PlaylistExportPath": os.path.join(UserLibraryPath, "playlists"),
    "EmbeddingsExportPath": os.path.join(UserLibraryPath, "embeddings"),
    "ExportFilesToPath": "",
}


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.load_state()

        def get_library_path():
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

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text=UINAME,
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_1 = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Show Library Info",
            command=self.toggle_library_visibility,
        )
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)

        self.scaling_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="UI Scaling:", anchor="w"
        )
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling_event,
        )
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        self.search_button = customtkinter.CTkButton(
            master=self,
            text="Search",
            command=lambda: print(get_library_path()),
        )
        self.search_button.grid(
            row=3, column=1, padx=(20, 20), pady=(0, 20), sticky="nsew"
        )

        # create tabview
        tabnames = ["Playlists", "Sample Finder", "Analyse New Library"]
        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(
            row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew", rowspan=3
        )
        self.tabview.add(tabnames[0])
        self.tabview.add(tabnames[1])
        # self.tabview.add("Analyse New Library")

        self.tabview.tab("Playlists").grid_columnconfigure(
            0, weight=1
        )  # configure grid of individual tabs
        self.tabview.tab("Sample Finder").grid_columnconfigure(0, weight=1)

        # self.optionmenu_1 = customtkinter.CTkOptionMenu(
        #     self.tabview.tab(tabnames[0]),
        #     dynamic_resizing=False,
        #     values=["Value 1", "Value 2", "Value Long Long Long"],
        # )
        # self.optionmenu_1.grid(row=0, column=0, padx=20, pady=(20, 10))
        # self.combobox_1 = customtkinter.CTkComboBox(
        #     self.tabview.tab(tabnames[0]),
        #     values=["Value 1", "Value 2", "Value Long....."],
        # )
        # self.combobox_1.grid(row=1, column=0, padx=20, pady=(10, 10))
        # self.string_input_button = customtkinter.CTkButton(
        #     self.tabview.tab("CTkTabview"),
        #     text="Open CTkInputDialog",
        #     command=self.open_input_dialog_event,
        # )
        # self.string_input_button.grid(row=2, column=0, padx=20, pady=(10, 10))
        # self.label_tab_2 = customtkinter.CTkLabel(
        #     self.tabview.tab("Tab 2"), text="CTkLabel on Tab 2"
        # )
        # self.label_tab_2.grid(row=0, column=0, padx=20, pady=20)

        # # create radiobutton frame
        # self.radiobutton_frame = customtkinter.CTkFrame(self)
        # self.radiobutton_frame.grid(
        #     row=0, column=3, padx=(20, 20), pady=(20, 0), sticky="nsew"
        # )
        # self.radio_var = tkinter.IntVar(value=0)
        # self.label_radio_group = customtkinter.CTkLabel(
        #     master=self.radiobutton_frame, text="CTkRadioButton Group:"
        # )
        # self.label_radio_group.grid(
        #     row=0, column=2, columnspan=1, padx=10, pady=10, sticky=""
        # )
        # self.radio_button_1 = customtkinter.CTkRadioButton(
        #     master=self.radiobutton_frame, variable=self.radio_var, value=0
        # )
        # self.radio_button_1.grid(row=1, column=2, pady=10, padx=20, sticky="n")
        # self.radio_button_2 = customtkinter.CTkRadioButton(
        #     master=self.radiobutton_frame, variable=self.radio_var, value=1
        # )
        # self.radio_button_2.grid(row=2, column=2, pady=10, padx=20, sticky="n")
        # self.radio_button_3 = customtkinter.CTkRadioButton(
        #     master=self.radiobutton_frame, variable=self.radio_var, value=2
        # )
        # self.radio_button_3.grid(row=3, column=2, pady=10, padx=20, sticky="n")

        # # create slider and progressbar frame
        # self.slider_progressbar_frame = customtkinter.CTkFrame(
        #     self, fg_color="transparent"
        # )
        # self.slider_progressbar_frame.grid(
        #     row=1, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew"
        # )
        # self.slider_progressbar_frame.grid_columnconfigure(0, weight=1)
        # self.slider_progressbar_frame.grid_rowconfigure(4, weight=1)
        # self.seg_button_1 = customtkinter.CTkSegmentedButton(
        #     self.slider_progressbar_frame
        # )
        # self.seg_button_1.grid(
        #     row=0, column=0, padx=(20, 10), pady=(10, 10), sticky="ew"
        # )
        # self.progressbar_1 = customtkinter.CTkProgressBar(self.slider_progressbar_frame)
        # self.progressbar_1.grid(
        #     row=1, column=0, padx=(20, 10), pady=(10, 10), sticky="ew"
        # )
        # self.progressbar_2 = customtkinter.CTkProgressBar(self.slider_progressbar_frame)
        # self.progressbar_2.grid(
        #     row=2, column=0, padx=(20, 10), pady=(10, 10), sticky="ew"
        # )
        # self.slider_1 = customtkinter.CTkSlider(
        #     self.slider_progressbar_frame, from_=0, to=1, number_of_steps=4
        # )
        # self.slider_1.grid(row=3, column=0, padx=(20, 10), pady=(10, 10), sticky="ew")
        # self.slider_2 = customtkinter.CTkSlider(
        #     self.slider_progressbar_frame, orientation="vertical"
        # )
        # self.slider_2.grid(
        #     row=0, column=1, rowspan=5, padx=(10, 10), pady=(10, 10), sticky="ns"
        # )
        # self.progressbar_3 = customtkinter.CTkProgressBar(
        #     self.slider_progressbar_frame, orientation="vertical"
        # )
        # self.progressbar_3.grid(
        #     row=0, column=2, rowspan=5, padx=(10, 20), pady=(10, 10), sticky="ns"
        # )

        # create scrollable frame
        # self.scrollable_frame = customtkinter.CTkScrollableFrame(
        #     self, label_text="CTkScrollableFrame"
        # )
        # self.scrollable_frame.grid(
        #     row=1, column=2, padx=(20, 0), pady=(20, 0), sticky="nsew"
        # )
        # self.scrollable_frame.grid_columnconfigure(0, weight=1)
        # self.scrollable_frame_switches = []
        # for i in range(100):
        #     switch = customtkinter.CTkSwitch(
        #         master=self.scrollable_frame, text=f"CTkSwitch {i}"
        #     )
        #     switch.grid(row=i, column=0, padx=10, pady=(0, 20))
        #     self.scrollable_frame_switches.append(switch)

        # # create checkbox and switch frame
        # self.checkbox_slider_frame = customtkinter.CTkFrame(self)
        # self.checkbox_slider_frame.grid(
        #     row=1, column=3, padx=(20, 20), pady=(20, 0), sticky="nsew"
        # )
        # self.checkbox_1 = customtkinter.CTkCheckBox(master=self.checkbox_slider_frame)
        # self.checkbox_1.grid(row=1, column=0, pady=(20, 0), padx=20, sticky="n")
        # self.checkbox_2 = customtkinter.CTkCheckBox(master=self.checkbox_slider_frame)
        # self.checkbox_2.grid(row=2, column=0, pady=(20, 0), padx=20, sticky="n")
        # self.checkbox_3 = customtkinter.CTkCheckBox(master=self.checkbox_slider_frame)
        # self.checkbox_3.grid(row=3, column=0, pady=20, padx=20, sticky="n")

        # # set default values
        # self.sidebar_button_3.configure(state="disabled", text="Disabled CTkButton")
        # self.checkbox_3.configure(state="disabled")
        # self.checkbox_1.select()
        # self.scrollable_frame_switches[0].select()
        # self.scrollable_frame_switches[4].select()
        # self.radio_button_3.configure(state="disabled")
        # self.appearance_mode_optionemenu.set("Dark")
        # self.scaling_optionemenu.set("100%")
        # self.optionmenu_1.set("CTkOptionmenu")
        # self.combobox_1.set("CTkComboBox")
        # self.slider_1.configure(command=self.progressbar_2.set)
        # self.slider_2.configure(command=self.progressbar_3.set)
        # self.progressbar_1.configure(mode="indeterminnate")
        # self.progressbar_1.start()
        # self.textbox.insert(
        #     "0.0",
        #     "CTkTextbox\n\n"
        #     + "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.\n\n"
        #     * 20,
        # )
        # self.seg_button_1.configure(values=["CTkSegmentedButton", "Value 2", "Value 3"])
        # self.seg_button_1.set("Value 2")

        # Library Right Sidebar

        self.library_sidebar = customtkinter.CTkFrame(self, width=500)
        self.library_sidebar.grid(
            row=0,
            rowspan=4,
            column=3,
            columnspan=2,
            padx=(0, 20),
            pady=(38, 20),
            sticky="nsew",
        )

        self.library_sidebar_label = customtkinter.CTkLabel(
            self.library_sidebar,
            text="Library",
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
            command=lambda x: print(x, get_library_path()),
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
            text="browse",
            width=80,
            command=lambda: self.browse_folder(self.library_path_entry),
        )
        self.browse_button.grid(row=7, column=1, padx=(10, 20), pady=(10, 10))

        self.libinfo_button = customtkinter.CTkButton(
            self.library_sidebar,
            text="Analyze and Save Collection",
            command=self.analyze_audio_collection,
            width=290,
            
        )
        self.libinfo_button.grid(
            row=8, column=0, padx=20, pady=(10, 20), columnspan=2, 
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
        entry.delete(0, END)
        entry.insert(0, file_selected)

    def validate_and_run(self, input_type):
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
                messagebox.showerror("Error", "Number of samples must be an integer.")
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
            print(result)
            # self.playlist_textbox_audio.delete("1.0", END)
            # self.playlist_textbox_text.delete("1.0", END)
            # self.playlist_textbox_audio.insert(
            #     "1.0",
            #     "\n".join(
            #         f"{index+1}. {path}" for index, path in enumerate(result)
            #     ),
            # )
            # self.playlist_textbox_text.insert(
            #     "1.0",
            #     "\n".join(
            #         f"{index+1}. {path}" for index, path in enumerate(result)
            #     ),
            # )

            messagebox.showinfo("Success", "Operation Completed Successfully")
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
        if new_library_name in [libname for libname, libpath in self.AnalysedLibraries.get()]:
            messagebox.showwarning(
                "Warning", "Library with this name already exists. Please choose a different name."
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

        self.AnalysedLibraries = Variable(value=last_state.get("AnalysedLibraries", {}))
        self.LastUsedLibrary = Variable(value=load_variable("LastUsedLibrary"))
        self.UserLibraryPath = Variable(value=load_variable("UserLibraryPath"))
        self.PlaylistExportPath = Variable(value=load_variable("PlaylistExportPath"))
        self.EmbeddingsExportPath = Variable(value=load_variable("EmbeddingsExportPath"))
        self.ExportFilesToPath = Variable(value=load_variable("ExportFilesToPath"))
        self.NewLibraryPath = StringVar(value="")

    def save_state(self, state_path=LAST_STATE):

        # list[tuple[str,str]]
        AnalysedLibraries = self.AnalysedLibraries.get()
        # path str
        LastUsedLibrary = self.LastUsedLibrary.get()
        UserLibraryPath = self.UserLibraryPath.get()
        PlaylistExportPath = self.PlaylistExportPath.get()
        EmbeddingsExportPath = self.EmbeddingsExportPath.get()
        ExportFilesToPath = self.ExportFilesToPath.get()

        with open(state_path, "w") as f:
            json.dump(
                {
                    "AnalysedLibraries": AnalysedLibraries,
                    "LastUsedLibrary": LastUsedLibrary,
                    "UserLibraryPath": UserLibraryPath,
                    "PlaylistExportPath": PlaylistExportPath,
                    "EmbeddingsExportPath": EmbeddingsExportPath,
                    "ExportFilesToPath": ExportFilesToPath,
                },
                f,
                indent=4,
            )

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

    def get_last_used_library_path(self):
        return os.path.join(self.EmbeddingsExportPath.get(), self.LastUsedLibrary.get())

    def update_entries_number(self, entries, new_value):
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


if __name__ == "__main__":
    if not os.path.exists(UserLibraryPath):
        os.makedirs(UserLibraryPath, exist_ok=True)
        os.makedirs(os.path.join(UserLibraryPath, "state"), exist_ok=True)
        os.makedirs(os.path.join(UserLibraryPath, "playlists"), exist_ok=True)
        os.makedirs(os.path.join(UserLibraryPath, "embeddings"), exist_ok=True)
        os.makedirs(os.path.join(UserLibraryPath, "models"), exist_ok=True)
    print(DEFAULTS)

    app = App()
    app.hide_library_info()
    app.mainloop()
