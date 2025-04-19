import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import random

# Define models
class TimeSeriesModel(nn.Module):
    def __init__(self):
        super(TimeSeriesModel, self).__init__()
        self.network = nn.Sequential(
            nn.Conv1d(3, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten()
        )

    def forward(self, x):
        return self.network(x)

class TLSModel(nn.Module):
    def __init__(self):
        super(TLSModel, self).__init__()
        self.network = nn.Sequential(
            nn.Conv1d(1, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten()
        )

    def forward(self, x):
        return self.network(x)

class FeatureCombinationEncoder:
    def __init__(self, info_series_dir):
        self.info_series_dir = info_series_dir

        self.time_series_model = TimeSeriesModel()
        self.tls_model = TLSModel()

        self.all_embeddings = []
        self.all_categories = []
        self.all_protocols = []
        self.all_navigators = []
        self.all_opes = []

    def load_time_series(self, file_path):
        """Load time-series EXCEL as a numpy array."""
        df = pd.read_excel(file_path, sheet_name="MD")
        time_series = df[['Packet Size', 'Time Delta', 'Direction']].to_numpy()
        return time_series
    def load_tls_features(self, file_path):
        """Load TLS features EXCEL as a numpy array."""
        df = pd.read_excel(file_path, sheet_name="TLS")

        # Process `tls_content` to ensure valid hex values
        tls_features = []
        for content in df["tls_content"]:
            try:
                # Evaluate string representation of list and convert hex to integers
                hex_values = [int(byte, 16) for byte in eval(content)]
                # Ensure each packet is exactly 600 bytes
                padded_packet = np.pad(hex_values, (0, max(0, 600 - len(hex_values))), mode='constant')[:600]
                tls_features.append(padded_packet)
            except Exception as e:
                print(f"Error processing TLS content: {content}, error: {e}")
                continue

        tls_features = np.concatenate(tls_features[:3]) if tls_features else np.zeros(1800)
        return tls_features

    def process_directory(self, info_series_dir):
        """Process all files in a directory hierarchy and save combined features."""
        time_series_features_list = []
        tls_features_list = []
        for root, dirs, files in os.walk(info_series_dir):
            for file in files:
                if file.endswith(".xlsx"):
                    # Construct corresponding paths
                    relative_path = os.path.relpath(root, info_series_dir)
                    file = os.path.join(root, file)

                    if not os.path.exists(file):
                        print(f"TLS file missing for {file}, skipping...")
                        continue

                    # Combine features
                    cat_pro_nav_ope = relative_path.split('\\')
                    if len(cat_pro_nav_ope) == 4:
                        self.all_categories.append(cat_pro_nav_ope[0])
                        self.all_protocols.append(cat_pro_nav_ope[1])
                        self.all_navigators.append(cat_pro_nav_ope[2])
                        self.all_opes.append(cat_pro_nav_ope[3])

                        time_series_features_list.append(self.load_time_series(file))
                        tls_features_list.append(self.load_tls_features(file))

                        print(f"Processed features for {file}")

        time_series_tensor = torch.tensor(np.stack(time_series_features_list), dtype=torch.float32).permute(0, 2, 1)
        tls_tensor = torch.tensor(np.stack(tls_features_list), dtype=torch.float32).unsqueeze(1)

        # Process time series and TLS features in batch
        with torch.no_grad():
            processed_time_series = self.time_series_model(time_series_tensor)
            processed_tls = self.tls_model(tls_tensor)

        self.all_embeddings = torch.cat((processed_time_series, processed_tls), dim=1).numpy()


    def process_all_categories(self):
        """Process all categories in the input directories."""
        self.process_directory(self.info_series_dir)
        dataset = pd.DataFrame(self.all_embeddings, columns=[f'dim_{i}' for i in range(1,1+len(self.all_embeddings[0]))])
        dataset['Category'] = self.all_categories
        dataset['Protocol'] = self.all_protocols
        dataset['Navigator'] = self.all_navigators
        dataset['Operation'] = self.all_opes
        output_file = os.path.join(self.info_series_dir, "embeddings_combined_all_same.csv")
        dataset.to_csv(output_file, index=False, header=True)

# Example usage
# if __name__ == "__main__":
#     dir = os.path.abspath("../../main_output")
#
#     encoder = FeatureCombinationEncoder(dir)
#     encoder.process_all_categories()
