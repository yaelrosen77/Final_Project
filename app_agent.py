import os
import subprocess
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import scikit-learn.model_selection import train_test_split
from scikit-learn.preprocessing import LabelEncoder
from torch.utils.data import Dataset, DataLoader

# 2. שליפת הנתונים

def load_preprocessed_data(data_path, max_packets=3, packet_size=600):
    flows = []
    labels = []
    for root, dirs, files in os.walk(data_path):
        for file in files:
            if file.endswith(".csv"):
                csv_path = os.path.join(root, file)
                df = pd.read_csv(csv_path)

                # הפקת TLS Content
                tls_content = df["tls_content"].apply(
                    lambda x: list(map(lambda h: int(h, 16), str(x).strip("[]").replace("'", "").split(",")))
                ).tolist()

                # שילוב חבילות לזרם
                flow = combine_tls_packets(tls_content, max_packets=max_packets, packet_size=packet_size)
                flows.append(flow)

                # שמירת תווית הזרם
                if "app_protocol" in df.columns and not df["app_protocol"].empty:
                    labels.append(df["app_protocol"].iloc[0])
                else:
                    print(f"Missing app_protocol in {csv_path}. Skipping file.")
    return np.array(flows), np.array(labels)

# פונקציה לשילוב חבילות
def combine_tls_packets(packets, max_packets=3, packet_size=600):
    combined = np.zeros((max_packets, packet_size))
    for i, packet in enumerate(packets[:max_packets]):
        combined[i, :len(packet)] = packet
    return combined.flatten()

# 3. בניית Dataset

class TLSFeatureDataset(Dataset):
    def __init__(self, data, labels):
        self.data = torch.tensor(data, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]

# 4. המודל

class TLSFeatureExtractor(nn.Module):
    def __init__(self):
        super(TLSFeatureExtractor, self).__init__()
        self.network = nn.Sequential(
            nn.Conv1d(3, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),
            nn.Conv1d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),
            nn.Flatten(),
            nn.Linear(256 * 150, 128)
        )

    def forward(self, x):
        return self.network(x)

class MatchingNetwork(nn.Module):
    def __init__(self, embedding_model):
        super(MatchingNetwork, self).__init__()
        self.embedding_model = embedding_model

    def forward(self, support, query):
        support_embeddings = self.embedding_model(support)
        query_embeddings = self.embedding_model(query)
        similarity = torch.matmul(query_embeddings, support_embeddings.T) / (
            torch.norm(query_embeddings, dim=1, keepdim=True) *
            torch.norm(support_embeddings, dim=1, keepdim=True).T
        )
        return similarity

# 5. אימון המודל

def train_matching_network(model, train_loader, optimizer, criterion, epochs=10):
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0
        for batch in train_loader:
            data, labels = batch
            optimizer.zero_grad()
            similarity = model(data, data)
            loss = criterion(similarity, labels)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        print(f"Epoch {epoch+1}/{epochs}, Loss: {epoch_loss / len(train_loader):.4f}")

# 6. בדיקת המודל

def evaluate_matching_network(model, test_loader):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for batch in test_loader:
            data, labels = batch
            similarity = model(data, data)
            predictions = torch.argmax(similarity, dim=1)
            correct += (predictions == labels).sum().item()
            total += labels.size(0)
    print(f"Accuracy: {100 * correct / total:.2f}%")

# הגדרת קלט
output_dir = "C:\\Users\\Adam\\Desktop\\Project\\csv_datasets\\mldit"
data, labels = load_preprocessed_data(output_dir)

# המרת תוויות למספרים
label_encoder = LabelEncoder()
labels = label_encoder.fit_transform(labels)

# פיצול הנתונים
train_data, test_data, train_labels, test_labels = train_test_split(data, labels, test_size=0.2, stratify=labels)
train_dataset = TLSFeatureDataset(train_data, train_labels)
test_dataset = TLSFeatureDataset(test_data, test_labels)

# הכנת DataLoader
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# בניית המודל
embedding_model = TLSFeatureExtractor()
matching_network = MatchingNetwork(embedding_model)
optimizer = torch.optim.Adam(matching_network.parameters(), lr=0.001)
criterion = torch.nn.CrossEntropyLoss()

# אימון
train_matching_network(matching_network, train_loader, optimizer, criterion)

# הערכה
evaluate_matching_network(matching_network, test_loader)
