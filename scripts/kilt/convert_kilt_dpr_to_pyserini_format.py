import argparse
import pickle
import csv
from tqdm import tqdm
import glob

import faiss
from dpr.indexer.faiss_indexers import DenseFlatIndexer


# All files required for this script can be found at:
# https://github.com/facebookresearch/KILT/tree/master/kilt/retrievers#download-models-1
# Note: Use this script
# https://github.com/huggingface/transformers/blob/053efc5d2d2e87833e9b7290a0dd83fa77cd6ae8/src/transformers/models/dpr/convert_dpr_original_checkpoint_to_pytorch.py
# to convert KILT's dpr_multi_set_f_bert.0 model into a PyTorch checkpoint

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert KILT-dpr corpus into the index & docid file read by pyserini')
    parser.add_argument('--input_dir', required=True, help='Path to the input dir. Must contain the files: '
                                                           'kilt_w100_title.tsv,'
                                                           'mapping_KILT_title.p,'
                                                           'kilt_passages_2048_0.pkl')
    parser.add_argument('--output_dir', required=True, help='Path of the output dir')

    args = parser.parse_args()

    print('Loading KILT mapping...')
    with open(f'{args.input_dir}/mapping_KILT_title.p', "rb") as f:
        KILT_mapping = pickle.load(f)

    print('Creating docid file...')
    not_found = set()
    with open(f'{args.input_dir}/kilt_w100_title.tsv', 'r') as f, \
            open(f'{args.output_dir}/docid', 'w') as outp:
        tsv = csv.reader(f, delimiter='\t')
        next(tsv)  # skip headers
        for row in tqdm(tsv, mininterval=10.0, maxinterval=20.0):
            title = row[2]
            if title not in KILT_mapping:
                not_found.add(title)
                _ = outp.write('N/A\n')
            else:
                _ = outp.write(f'{KILT_mapping[title]}\n')

    print("Done writing docid file!")
    print(f'Some documents did not have a docid in the mapping: {not_found}')

    print('Creating index file...')
    ctx_files_pattern = f'{args.input_dir}/kilt_passages_2048_0.pkl'
    input_paths = glob.glob(ctx_files_pattern)

    vector_size = 768
    index = DenseFlatIndexer(vector_size)
    index.index_data(input_paths)
    faiss.write_index(index, f'{args.output_dir}/index')
    print('Done writing index file!')