import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from sample_finder_SA_inter import (
    load_embeddings_index,
    process_new_audio_sample,
    find_wav_files,
    build_embeddings_index,
    save_embeddings_index,
)
import os
import argparse
import customtkinter as ctk


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


def run_sample_finder_gui():
    def browse_folder(entry):
        folder_selected = filedialog.askdirectory()
        entry.delete(0, tk.END)
        entry.insert(0, folder_selected)

    def browse_file(entry):
        file_selected = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav *.flac")]
        )
        entry.delete(0, tk.END)
        entry.insert(0, file_selected)

    def validate_and_run():
        try:
            input_type = input_type_var.get()
            input_value = (
                text_prompt_entry.get()
                if input_type == "Text"
                else audio_file_entry.get()
            )
            n_samples = int(n_samples_entry.get())
            destination_folder = destination_folder_entry.get()
            embedding_map_dir = embedding_map_dir_entry.get()

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
        audio_collection_dir = audio_collection_entry.get()
        file_type = file_type_var.get()
        emap_name = emap_name_entry.get()
        save_emap_location = save_emap_location_entry.get()

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

    def toggle_input_type():
        if input_type_var.get() == "Text":
            audio_file_entry.pack_forget()
            audio_file_label.pack_forget()
            browse_button.pack_forget()
            text_prompt_label.pack(**p)
            text_prompt_entry.pack(**p)
        else:  # 'Audio'
            text_prompt_entry.pack_forget()
            text_prompt_label.pack_forget()
            audio_file_label.pack(**p)
            audio_file_entry.pack(**p)
            browse_button.pack(**p)

    root = ctk.CTk()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root.title("Sample Finder")
    root.geometry("1000x800")  # Making the GUI wider
    theme = {
        "light": {"bg": "light grey", "fg": "black"},
        "dark": {
            "bg_color": "#333333",
        },
    }
    m = theme["dark"]
    p = {
        "padx": 10,
        "pady": 5,
    }
    # root.configure(bg="#1f1f1f")
    # mb = {"bg": m["bg"]}
    # mf = {"fg": m["fg"]}

    initial_analysis_frame = ctk.CTkFrame(root, **m)
    initial_analysis_frame.place(relx=0.02, rely=0.02, relwidth=0.45, relheight=0.96)

    inference_frame = ctk.CTkFrame(root, **m)
    inference_frame.place(relx=0.52, rely=0.02, relwidth=0.45, relheight=0.96)

    # Section 1: Initial analysis
    ctk.CTkLabel(initial_analysis_frame, text="Build Database").pack(**p)

    ctk.CTkLabel(initial_analysis_frame, text="Audio Collection Folder:", **p).pack(**p)
    audio_collection_entry = ctk.CTkEntry(initial_analysis_frame)
    audio_collection_entry.pack(**p)
    ctk.CTkButton(
        initial_analysis_frame,
        text="Browse...",
        command=lambda: browse_folder(audio_collection_entry),
    ).pack(**p)

    ctk.CTkLabel(initial_analysis_frame, text="File Type:").pack(**p)
    file_type_var = tk.StringVar(value=".wav")  # Default file type
    file_type_entry = ctk.CTkEntry(initial_analysis_frame, textvariable=file_type_var)
    file_type_entry.pack(**p)

    ctk.CTkLabel(initial_analysis_frame, text="Embedding Map Name:").pack(**p)
    emap_name_entry = ctk.CTkEntry(initial_analysis_frame)
    emap_name_entry.pack(**p)

    ctk.CTkLabel(initial_analysis_frame, text="Save Embedding Map Location:").pack(**p)
    save_emap_location_entry = ctk.CTkEntry(initial_analysis_frame)
    save_emap_location_entry.pack(**p)
    ctk.CTkButton(
        initial_analysis_frame,
        text="Browse...",
        command=lambda: browse_folder(save_emap_location_entry),
    ).pack(**p)

    ctk.CTkButton(
        initial_analysis_frame,
        text="Analyze and Save Collection",
        command=analyze_audio_collection,
    ).pack(**p)



    # Section 2: Running inference with SampleFinder

    ctk.CTkLabel(inference_frame, text="Search for Samples").pack(**p)
    input_type_var = tk.StringVar(value="Text")
    ctk.CTkRadioButton(
        inference_frame,
        text="Text",
        variable=input_type_var,
        value="Text",
        command=toggle_input_type,
    ).pack(**p)
    ctk.CTkRadioButton(
        inference_frame,
        text="Audio",
        variable=input_type_var,
        value="Audio",
        command=toggle_input_type,
    ).pack(**p)

    text_prompt_label = ctk.CTkLabel(inference_frame, text="Text Prompt:")
    audio_file_label = ctk.CTkLabel(inference_frame, text="Audio File:")
    text_prompt_entry = ctk.CTkEntry(inference_frame)
    audio_file_entry = ctk.CTkEntry(inference_frame)
    browse_button = ctk.CTkButton(
        inference_frame, text="Browse...", command=lambda: browse_file(audio_file_entry)
    )

    # Initial toggle to configure initial view
    toggle_input_type()

    ctk.CTkLabel(inference_frame, text="Number of Samples:").pack(**p)
    n_samples_entry = ctk.CTkEntry(inference_frame)
    n_samples_entry.pack(**p)

    ctk.CTkLabel(inference_frame, text="Destination Folder:").pack(**p)
    destination_folder_entry = ctk.CTkEntry(inference_frame)
    destination_folder_entry.pack(**p)
    ctk.CTkButton(
        inference_frame,
        text="Browse...",
        command=lambda: browse_folder(destination_folder_entry),
    ).pack(**p)

    ctk.CTkLabel(inference_frame, text="Embeddings Folder:").pack(**p)
    embedding_map_dir_entry = ctk.CTkEntry(inference_frame)
    embedding_map_dir_entry.pack(**p)
    ctk.CTkButton(
        inference_frame,
        text="Browse...",
        command=lambda: browse_folder(embedding_map_dir_entry),
    ).pack(**p)

    run_button = ctk.CTkButton(
        inference_frame, text="Run Sample Finder", command=validate_and_run
    )
    run_button.pack(**p)

    root.mainloop()


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
        run_sample_finder_gui()
