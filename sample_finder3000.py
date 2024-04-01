import os
import numpy as np
import json
from sklearn.preprocessing import normalize
# You might choose a different library for extracting embeddings
from annoy import AnnoyIndex
import argparse

from msclap import CLAP
import os
import json

# Load model (Choose between versions '2022' or '2023')
# The model weight will be downloaded automatically if `model_fp` is not specified
clap_model = CLAP(version = '2023', use_cuda=False)

def extract_embedding(audio_path):
    embedding = clap_model.get_audio_embeddings([audio_path])
    return embedding[0]

def find_wav_files(root_dir):
    """Recursively find all .wav files in the directory."""
    wav_files = []
    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".wav"):
                wav_files.append(os.path.join(subdir, file))
    return wav_files

def build_embeddings_index(wav_files):
    """Build an index of embeddings for the given files."""
    f = 1024  # embedding size is 1024
    t = AnnoyIndex(f, 'angular')  # Using Annoy for nearest neighbor search
    embeddings_path_map = {}

    for i, file_path in enumerate(wav_files):
        embedding = extract_embedding(file_path)
        t.add_item(i, embedding)
        embeddings_path_map[i] = file_path

    t.build(10)  # 10 trees
    return t, embeddings_path_map

def save_embeddings_index(embeddings_index, path_map, index_path, path_map_path):
    """Save the embeddings index and path map to files."""
    embeddings_index.save(index_path)
    with open(path_map_path, 'w') as f:
        json.dump(path_map, f)

def load_embeddings_index(index_path, path_map_path):
    """Load the embeddings index and path map from files."""
    t = AnnoyIndex(1024, 'angular')  # embedding size is 1024
    t.load(index_path)
    with open(path_map_path) as f:
        path_map = json.load(f)
    return t, path_map

def find_closest_embedding(embedding, embeddings_index, path_map, n=1):
    """Find the closest embedding in the index and return the corresponding file path."""
    nearest_ids = embeddings_index.get_nns_by_vector(embedding, n)
    return [path_map[str(nearest_id)] for nearest_id in nearest_ids]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create dataset embeddings and path map")
    parser.add_argument("audio_collection", help="Path to directory containing audio samples")
    parser.add_argument("save_emap", help="directory to save embeddings and path map")
    args = parser.parse_args()


    # root_dir = '/Users/jake/Documents/code/trip/clap/sample_test_data/Zero-G Jungle Warfare Complete/Zero-G Jungle Warfare 1, 2 & 3/VOL 1/'
    os.makedirs(args.save_emap, exist_ok=False)
    wav_files = find_wav_files(args.audio_collection)
    embeddings_index, path_map = build_embeddings_index(wav_files)
    save_embeddings_index(embeddings_index, path_map,
                          os.path.join(args.save_emap, 'embeddings.ann'),
                          os.path.join(args.save_emap, 'path_map.json')
                          )



# make it okay to use not just wav files, so mp3 aif etc. just an if in list

print("debug")