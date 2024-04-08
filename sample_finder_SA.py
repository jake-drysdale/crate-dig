import argparse
import shutil
import json
from annoy import AnnoyIndex
from msclap import CLAP
import os
import torch
from transformers import AutoTokenizer
import sys



def preprocess_text(text_queries, text_model='gpt2', text_len=77, use_cuda=False):
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
        ttext = ttext + ' ' if 'gpt' in text_model else ttext
        
        tok = tokenizer.encode_plus(
            text=ttext,
            add_special_tokens=True,
            max_length=text_len,
            padding='max_length',
            return_tensors="pt",
            truncation=True
        )
        
        if use_cuda and torch.cuda.is_available():
            tok = {k: v.cuda() for k, v in tok.items()}
        tokenized_texts.append(tok)

    input_ids = torch.stack([t["input_ids"].squeeze() for t in tokenized_texts])
    attention_mask = torch.stack([t["attention_mask"].squeeze() for t in tokenized_texts])

    return {"input_ids": input_ids, "attention_mask": attention_mask}

def extract_embedding(audio_path, text=False):
    if text:
        # embedding = clap_model.get_text_embeddings([audio_path])
        text_input = preprocess_text([audio_path])
        embedding = text_encoder_model(text_input)
    else:
        None
        # embedding = clap_model.get_audio_embeddings([audio_path])
    
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


# Check if running as a PyInstaller bundle
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = '.'

tokenizer_path = os.path.join(application_path, 'gpt2_tokenizer')
tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

# clap_model = CLAP(version = '2023', use_cuda=False)

text_encoder_model = torch.jit.load(os.path.join(application_path,"traced_text_encoder_model.pt"))
audio_encoder_model = torch.jit.load(os.path.join(application_path, "traced_audio_encoder_model.pt"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and copy closest audio samples.")
    parser.add_argument("new_audio_path", help="Path to the new audio sample")
    parser.add_argument("n_samples", type=int, help="Number of closest samples to find and copy")
    parser.add_argument("--text", type=bool, default=True, help="audio or text controll")
    parser.add_argument("--destination_folder", default="/found_samples/", help="Folder to copy closest samples to")
    parser.add_argument("--embedding_map_dir", default=os.path.join(application_path,"embeddings"), help="Path to the folder with embeddings index and path map files")
    # parser.add_argument("--path_map_path", default="path_map.json", help="Path to the path map file")

    args = parser.parse_args()

    # Load embeddings index and path map
    embeddings_index, path_map = load_embeddings_index(args.embedding_map_dir)

    # Process the new audio sample
    process_new_audio_sample(args.new_audio_path, embeddings_index, path_map, args.n_samples, args.destination_folder, args.text)

# WRITE A SCRIPT FOR SLICING LONG SAMPLE CD FILES

