import argparse
import shutil
import json
from annoy import AnnoyIndex

# from msclap import CLAP
import os
import torch
from transformers import AutoTokenizer
import sys

# import tkinter as tk
# from tkinter import filedialog, messagebox
import torchaudio
import collections.abc
import random
import re
import numpy as np
import torchaudio.transforms as T
import gc
from tqdm import tqdm

# import subprocess


################# AUDIO COLLECTION ANALYSIS #################


def find_wav_files(root_dir, file_types):
    """Recursively find all audio files of specified types in the directory."""
    audio_files = []
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(tuple(file_types)):
                audio_files.append(os.path.join(subdir, file))
    return audio_files


def build_embeddings_index(wav_files, embeddings_list_path, progressbar, refresh):
    """Build an index of embeddings for the given files and return embeddings."""
    f = 1024  # embedding size is 1024
    t = AnnoyIndex(f, "angular")  # Using Annoy for nearest neighbor search
    shape = (len(wav_files), f)
    embeddings_path_map = {}
    # embeddings_list = []
    embeddings_list = np.memmap(
        embeddings_list_path, dtype="float32", mode="w+", shape=shape
    )
    done = 0
    progressbar.set(0)
    progressbar.start()

    for i, file_path in tqdm(
        enumerate(wav_files),
        desc="Building embeddings index",
        total=len(wav_files),
        unit="files",
    ):
        embedding = extract_embedding(file_path, False)
        embedding_np = embedding.detach().cpu().numpy()
        t.add_item(i, embedding_np)
        embeddings_path_map[i] = file_path
        embeddings_list[i] = embedding_np
        done += 1
        progressbar.set(done / len(wav_files))
        refresh()
        # embeddings_list.append(embedding)  # Add embedding to list
        del embedding  # Explicitly delete if it's no longer needed
        gc.collect()  # Force garbage collection

    progressbar.stop()
    t.build(10)  # 10 trees
    return t, embeddings_path_map  # Return embeddings_list


def save_embeddings_index(embeddings_index, path_map, index_path, path_map_path):
    """Save the embeddings index, path map, and embeddings list to files."""
    embeddings_index.save(index_path)
    with open(path_map_path, "w", encoding="utf-8") as f:
        json.dump(path_map, f)
    # np.save(embeddings_list_path, embeddings_list)  # Save embeddings list as .npy file


# # def analyse_and_save(args):
# def analyse_and_save(audio_collection_dir, save_emap_full_path):
#     # os.makedirs(args.save_emap, exist_ok=False)
#     wav_files = find_audio_files(audio_collection_dir)
#     embeddings_index, path_map, embeddings_list = build_embeddings_index(wav_files)
#     save_embeddings_index(embeddings_index, path_map, embeddings_list,
#                             os.path.join(save_emap_full_path, 'embeddings.ann'),
#                             os.path.join(save_emap_full_path, 'path_map.json'),
#                             os.path.join(save_emap_full_path, 'embeddings_list.npy')
#                             )


################# AUDIO PROCESSING #################


def read_audio(audio_path, sampling_rate, resample=True):
    r"""Loads audio file or array and returns a torch tensor"""
    # Load audio file
    audio_time_series, sample_rate = torchaudio.load(audio_path)

    # Resample if necessary
    if resample and sampling_rate != sample_rate:
        resampler = T.Resample(sample_rate, sampling_rate)
        audio_time_series = resampler(audio_time_series)
    return audio_time_series, sampling_rate


def load_audio_into_tensor(
    audio_path, audio_duration, sampling_rate, resample=False
) -> torch.Tensor:
    r"""Loads audio file and returns raw audio."""
    # Read and resample audio
    audio_time_series, sample_rate = read_audio(
        audio_path, sampling_rate, resample=resample
    )
    audio_time_series = audio_time_series.reshape(-1)

    # Extend or trim the audio_time_series to match the desired audio duration
    if audio_duration * sample_rate >= audio_time_series.shape[0]:
        repeat_factor = int(
            np.ceil((audio_duration * sample_rate) / audio_time_series.shape[0])
        )
        audio_time_series = audio_time_series.repeat(repeat_factor)[
            : audio_duration * sample_rate
        ]
    else:
        start_index = random.randrange(
            audio_time_series.shape[0] - audio_duration * sample_rate
        )
        audio_time_series = audio_time_series[
            start_index : start_index + audio_duration * sample_rate
        ]

    return torch.FloatTensor(audio_time_series)


def default_collate(batch: list[torch.Tensor]):
    r"""Puts each data field into a tensor with outer dimension batch size"""
    elem = batch[0]
    elem_type = type(elem)
    np_str_obj_array_pattern = re.compile(r"[SaUO]")
    if isinstance(elem, torch.Tensor):
        out = None
        if torch.utils.data.get_worker_info() is not None:
            # If we're in a background process, concatenate directly into a
            # shared memory tensor to avoid an extra copy
            numel = sum(x.numel() for x in batch)
            storage = elem.storage()._new_shared(numel)
            out = elem.new(storage)
        return torch.stack(batch, 0, out=out)
    elif (
        elem_type.__module__ == "numpy"
        and elem_type.__name__ != "str_"
        and elem_type.__name__ != "string_"
    ):
        if elem_type.__name__ == "ndarray" or elem_type.__name__ == "memmap":
            # array of string classes and object
            if np_str_obj_array_pattern.search(elem.dtype.str) is not None:
                raise TypeError("batch must not contain strings or objects")
            return default_collate([torch.as_tensor(b) for b in batch])
        elif elem.shape == ():  # scalars
            return torch.as_tensor(batch)
    elif isinstance(elem, float):
        return torch.tensor(batch, dtype=torch.float64)
    elif isinstance(elem, int):
        return torch.tensor(batch)
    elif isinstance(elem, str):
        return batch
    elif isinstance(elem, collections.abc.Mapping):
        return {key: default_collate([d[key] for d in batch]) for key in elem}
    elif isinstance(elem, tuple) and hasattr(elem, "_fields"):  # namedtuple
        return elem_type(*(default_collate(samples) for samples in zip(*batch)))
    elif isinstance(elem, collections.abc.Sequence):
        it = iter(batch)
        elem_size = len(next(it))
        if not all(len(elem) == elem_size for elem in it):
            raise RuntimeError("each element in list of batch should be of equal size")
        transposed = zip(*batch)
        return [default_collate(samples) for samples in transposed]
    raise TypeError("Unsupported batch data type")


def preprocess_audio(
    audio_files, audio_duration=7, sampling_rate=44100, use_cuda=False, resample=True
):
    r"""Load list of audio files and return raw audio"""
    audio_tensors = []
    for audio_file in audio_files:
        audio_tensor = load_audio_into_tensor(
            audio_file, audio_duration, sampling_rate, resample
        )
        if use_cuda and torch.cuda.is_available():
            audio_tensor = audio_tensor.reshape(1, -1).cuda()
        else:
            audio_tensor = audio_tensor.reshape(1, -1)
        audio_tensors.append(audio_tensor)
    preprocessed_audio = default_collate(audio_tensors)
    preprocessed_audio = preprocessed_audio.reshape(
        preprocessed_audio.shape[0], preprocessed_audio.shape[2]
    )
    return preprocessed_audio


################# TEXT PROCESSING #################


def preprocess_text(text_queries, text_model="gpt2", text_len=77, use_cuda=False):
    """
    Tokenize a list of text queries using a specified model tokenizer.

    Parameters:
    - text_queries: A list of strings (text queries) to tokenize.
    - text_model: The model ID for the tokenizer (default: 'gpt2').
    - text_len: Maximum length of the tokenized output (default: 512).
    - use_cuda: Whether to move tensors to CUDA if available (default: False).

    Returns:
    - A tensor containing the tokenized and collated text queries.
    """
    # tokenizer = AutoTokenizer.from_pretrained(text_model)

    # Set the padding token if not already defined
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    tokenized_texts = []
    for ttext in text_queries:
        ttext = ttext + " " if "gpt" in text_model else ttext

        tok = tokenizer.encode_plus(
            text=ttext,
            add_special_tokens=True,
            max_length=text_len,
            padding="max_length",
            return_tensors="pt",
            truncation=True,
        )

        if use_cuda and torch.cuda.is_available():
            tok = {k: v.cuda() for k, v in tok.items()}
        tokenized_texts.append(tok)

    input_ids = torch.stack([t["input_ids"].squeeze() for t in tokenized_texts])
    attention_mask = torch.stack(
        [t["attention_mask"].squeeze() for t in tokenized_texts]
    )

    return {"input_ids": input_ids, "attention_mask": attention_mask}


################# EMBEDDING EXTRACTION AND LOADING #################


def extract_embedding(audio_path, is_text) -> torch.Tensor:
    if is_text:
        # embedding = clap_model.get_text_embeddings([audio_path])
        text_input = preprocess_text([audio_path])
        embedding = text_encoder_model(text_input)
    else:
        audio_input = preprocess_audio([audio_path])
        embedding = audio_encoder_model(audio_input)[0]

    return embedding[0]


def load_embeddings_index(embedding_path_dir) -> tuple[AnnoyIndex, dict]:
    """Load the embeddings index and path map from files."""
    index_path = os.path.join(embedding_path_dir, "embeddings.ann")
    path_map_path = os.path.join(embedding_path_dir, "path_map.json")
    t = AnnoyIndex(1024, "angular")
    t.load(index_path)
    with open(path_map_path, "r", encoding="utf-8") as f:
        path_map = json.load(f)
    return t, path_map


################# PROCESS INPUT #################
def process_path(mode, **kwargs):
    """Process a path based on the mode: 'list' or 'copy'."""
    if mode == "copy":
        shutil.copy(kwargs["src_path"], kwargs["dest_path"])
        print(f"Copied {kwargs['src_path']} to {kwargs['dest_path']}")
        return kwargs["dest_path"]
    return kwargs["src_path"]


def process_new_audio_sample(
    input_value,
    embeddings_index: AnnoyIndex,
    path_map: dict,
    n_samples,
    destination_folder,
    is_text,
    mode="list",
):
    # def process_new_audio_sample(new_audio_path, embeddings_index, path_map, n_samples, destination_folder, text=False):
    """Process a new audio sample: Extract embedding, find closest samples, copy to destination."""
    new_embedding = extract_embedding(input_value, is_text)
    nearest_ids = embeddings_index.get_nns_by_vector(new_embedding, n_samples)
    result = []
    for nearest_id in nearest_ids:
        src_path = path_map[str(nearest_id)]
        result.append(
            process_path(mode, src_path=src_path, destination_folder=destination_folder)
        )

    return result


################# PLAYLIST GENERATION #################


def process_iterative_samples(
    input_value,
    embeddings_index: AnnoyIndex,
    path_map: dict,
    n_samples,
    destination_folder,
    is_text,
    rename=False,
):
    """
    Process an input to iteratively find the closest samples, creating a chain of related samples without repetition.
    Files are optionally renamed in sequential order starting from 0 based on the 'rename' parameter.
    """
    current_embedding = extract_embedding(input_value, is_text)
    used_ids = set()
    file_counter = 0  # Initialize a counter to name files sequentially if renaming

    for _ in range(n_samples):
        nearest_ids = embeddings_index.get_nns_by_vector(
            current_embedding, n_samples + len(used_ids)
        )
        # Find the first unused sample
        next_sample_id = next((nid for nid in nearest_ids if nid not in used_ids), None)

        if next_sample_id is None:
            print("No new unique samples available.")
            break

        # Mark this sample as used
        used_ids.add(next_sample_id)

        # Update current embedding to the last found sample's embedding
        src_path = path_map[str(next_sample_id)]
        current_embedding = extract_embedding(src_path, is_text)

        # Construct the destination path based on the rename argument
        if rename:
            file_extension = os.path.splitext(src_path)[
                1
            ]  # Get the file extension from the source path
            dest_path = os.path.join(
                destination_folder, f"{file_counter}{file_extension}"
            )
        else:
            dest_path = os.path.join(destination_folder, os.path.basename(src_path))

        # Copy the file to the destination folder with the new or original name
        shutil.copy(src_path, dest_path)
        print(f"Copied {src_path} to {dest_path}")

        # Increment the file counter for the next file name if renaming
        file_counter += 1


################# LOADING MODELS AND CHECKPOINTS #################

# Check if running as a PyInstaller bundle
if getattr(sys, "frozen", False):
    application_path = sys._MEIPASS
else:
    application_path = "."

tokenizer_path = os.path.join(application_path, "gpt2_tokenizer")
tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

text_encoder_model = torch.jit.load(
    os.path.join(
        application_path, "UserLibrary", "models", "traced_text_encoder_model.pt"
    )
)
audio_encoder_model = torch.jit.load(
    os.path.join(
        application_path, "UserLibrary", "models", "traced_audio_encoder_model.pt"
    )
)
