import numpy as np
import tensorflow as tf


def prepare_sequences(df, features, max_seq_length=6):
    sequences = []
    targets = []
    
    # Group by game and at_bat to get sequences
    for (game_id, at_bat), group in df.groupby(['game_date', 'at_bat_number']):
        # Sort by pitch number within at_bat
        group = group.sort('pitch_number')
        
        # Extract features for this sequence
        seq = group.select(features).to_numpy()
        
        # Only keep complete sequences
        if not np.any(np.isnan(seq)):
            sequences.append(seq)
            # Sum of run values for the sequence
            targets.append(group['delta_run_exp'].sum())
    
    # Pad sequences
    if sequences:
        X = tf.keras.preprocessing.sequence.pad_sequences(
            sequences,
            maxlen=max_seq_length,
            padding='post',
            dtype='float32',
            value=0.0
        )
        return np.array(X), np.array(targets)
    return np.array([]), np.array([])
