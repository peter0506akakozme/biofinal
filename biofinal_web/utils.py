import numpy as np

def extract_aac_features(sequence):
    """計算 Amino Acid Composition (AAC) 特徵，共 20 維"""
    sequence = sequence.upper()
    amino_acids = 'ACDEFGHIKLMNPQRSTVWY'
    total = len(sequence)
    features = [sequence.count(aa) / total for aa in amino_acids]
    return np.array(features)