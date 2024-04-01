import argparse
import shutil
import json
from annoy import AnnoyIndex
from msclap import CLAP
import os

clap_model = CLAP(version = '2023', use_cuda=False)

def extract_embedding(audio_path, text=False):
    if text:
        embedding = clap_model.get_text_embeddings([audio_path])
    else:
        embedding = clap_model.get_audio_embeddings([audio_path])
    
    return embedding[0]

def load_embeddings_index(embedding_path_dir):
    """Load the embeddings index and path map from files."""
    index_path = os.path.join(embedding_path_dir, 'embeddings.ann')
    path_map_path = os.path.join(embedding_path_dir, 'path_map.json')
    t = AnnoyIndex(1024, 'angular')
    t.load(index_path)
    with open(path_map_path) as f:
        path_map = json.load(f)
    return t, path_map

def process_new_audio_sample(new_audio_path, embeddings_index, path_map, n_samples, destination_folder, text=False):
    """Process a new audio sample: Extract embedding, find closest samples, copy to destination."""
    new_embedding = extract_embedding(new_audio_path, text)
    nearest_ids = embeddings_index.get_nns_by_vector(new_embedding, n_samples)
    for nearest_id in nearest_ids:
        src_path = path_map[str(nearest_id)]
        shutil.copy(src_path, destination_folder)
        print(f"Copied {src_path} to {destination_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and copy closest audio samples.")
    parser.add_argument("new_audio_path", help="Path to the new audio sample")
    parser.add_argument("n_samples", type=int, help="Number of closest samples to find and copy")
    parser.add_argument("--text", type=bool, default=False, help="audio or text controll")
    parser.add_argument("--destination_folder", default="./found_samples/", help="Folder to copy closest samples to")
    parser.add_argument("--embedding_map_dir", default="junglefrenzy", help="Path to the folder with embeddings index and path map files")
    # parser.add_argument("--path_map_path", default="path_map.json", help="Path to the path map file")

    args = parser.parse_args()

    # Load embeddings index and path map
    embeddings_index, path_map = load_embeddings_index(args.embedding_map_dir)

    # Process the new audio sample
    process_new_audio_sample(args.new_audio_path, embeddings_index, path_map, args.n_samples, args.destination_folder, args.text)

# WRITE A SCRIPT FOR SLICING LONG SAMPLE CD FILES

