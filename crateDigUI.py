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

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(
    "blue"
)  # Themes: "blue" (standard), "green", "dark-blue"

UserLibrary = "UserLibrary"

LAST_STATE_FILE_SF = f"{UserLibrary}/state/last_state_samplefinder.json"
LAST_STATE_FILE_ANL = f"{UserLibrary}/state/last_state_analyse_new_library.json"


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


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
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

        # configure window
        self.title("CrateDig")
        self.geometry(f"{1100}x{580}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # # create sidebar frame with widgets
        # self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        # self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        # self.sidebar_frame.grid_rowconfigure(4, weight=1)
        # self.logo_label = customtkinter.CTkLabel(
        #     self.sidebar_frame,
        #     text="CustomTkinter",
        #     font=customtkinter.CTkFont(size=20, weight="bold"),
        # )
        # self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        # self.sidebar_button_1 = customtkinter.CTkButton(
        #     self.sidebar_frame, command=self.sidebar_button_event
        # )
        # self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        # self.sidebar_button_2 = customtkinter.CTkButton(
        #     self.sidebar_frame, command=self.sidebar_button_event
        # )
        # self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        # self.sidebar_button_3 = customtkinter.CTkButton(
        #     self.sidebar_frame, command=self.sidebar_button_event
        # )
        # self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)
        # self.appearance_mode_label = customtkinter.CTkLabel(
        #     self.sidebar_frame, text="Appearance Mode:", anchor="w"
        # )
        # self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        # self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
        #     self.sidebar_frame,
        #     values=["Light", "Dark", "System"],
        #     command=self.change_appearance_mode_event,
        # )
        # self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        # self.scaling_label = customtkinter.CTkLabel(
        #     self.sidebar_frame, text="UI Scaling:", anchor="w"
        # )
        # self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        # self.scaling_optionemenu = customtkinter.CTkOptionMenu(
        #     self.sidebar_frame,
        #     values=["80%", "90%", "100%", "110%", "120%"],
        #     command=self.change_scaling_event,
        # )
        # self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # create main entry and button
        # self.entry = customtkinter.CTkEntry(self, placeholder_text="CTkEntry")
        # self.entry.grid(
        #     row=3, column=1, columnspan=2, padx=(20, 20), pady=(20, 20), sticky="nsew"
        # )

        self.main_button_1 = customtkinter.CTkButton(
            master=self,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "#DCE4EE"),
        )
        self.main_button_1.grid(
            row=3, column=3, padx=(20, 20), pady=(20, 20), sticky="nsew"
        )

        # # create textbox
        # self.textbox = customtkinter.CTkTextbox(self, width=250)
        # self.textbox.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")

        # create tabview
        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.tabview.add("Playlists")
        self.tabview.add("Sample Finder")
        # self.tabview.add("Analyse New Library")

        self.tabview.tab("Playlists").grid_columnconfigure(
            0, weight=1
        )  # configure grid of individual tabs
        self.tabview.tab("Sample Finder").grid_columnconfigure(0, weight=1)

        self.optionmenu_1 = customtkinter.CTkOptionMenu(
            self.tabview.tab("Playlists"),
            dynamic_resizing=False,
            values=["Value 1", "Value 2", "Value Long Long Long"],
        )
        self.optionmenu_1.grid(row=0, column=0, padx=20, pady=(20, 10))
        # self.combobox_1 = customtkinter.CTkComboBox(
        #     self.tabview.tab("CTkTabview"),
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

        # # create scrollable frame
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

    def browse_folder(self, entry):
            """
            Browse for a folder and insert the path into the entry.
            """
            folder_selected = filedialog.askdirectory()
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

    def analyze_audio_collection(self, ):
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
    
    def update_entries_number(self, entries, new_value):
        for entry in entries:
            entry.set(new_value)
    
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

    def sidebar_button_event(self):
        print("sidebar_button click")


if __name__ == "__main__":
    app = App()
    app.mainloop()
