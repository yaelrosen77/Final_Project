import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from collections import Counter

class CombinedDataset(Dataset):
    def __init__(self, embeddings, labels):
        self.embeddings = embeddings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return (
            torch.tensor(self.embeddings[idx], dtype=torch.float32),
            torch.tensor(self.labels[idx], dtype=torch.long)
        )

class FullyConnectedClassifier(nn.Module):
    def __init__(self, input_dim, num_classes):
        super(FullyConnectedClassifier, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.fc(x)

def train_model(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    for data, labels in dataloader:
        data, labels = data.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(data)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(dataloader)

def evaluate_model(model, dataloader, device):
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for data, labels in dataloader:
            data, labels = data.to(device), labels.to(device)
            outputs = model(data)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    return correct / total

def predict_labels(model, csv_path, device, label_encoder):
    """
    קרא CSV חדש, עבד את ה-embeddings שבו, והחזר את הלייבלים החזויים.
    """
    # קרא את ה-CSV החדש
    new_data = pd.read_csv(csv_path)
    embeddings = new_data.to_numpy()  # כל השורות הן embeddings

    # המרת הנתונים לטנסורים
    embeddings_tensor = torch.tensor(embeddings, dtype=torch.float32).to(device)

    # הפעל את המודל במצב חיזוי
    model.eval()
    with torch.no_grad():
        outputs = model(embeddings_tensor)
        _, predicted = torch.max(outputs, 1)  # תחזית המחלקה
        predicted_labels = label_encoder.inverse_transform(predicted.cpu().numpy())

    return predicted_labels

class AppAgent:
    def __init__(self, embedding_dir):
        self.embedding_dir = embedding_dir

    def start_training(self):
        # labeled_dataset = pd.read_excel(self.embedding_dir, sheet_name="TLS")
        # labeled_dataset = pd.read_excel(self.embedding_dir, sheet_name="MD")
        labeled_dataset = pd.read_csv(self.embedding_dir)
        label_cat = labeled_dataset['Category']
        label_pro = labeled_dataset['Protocol']
        label_nav = labeled_dataset['Navigator']
        label_ope = labeled_dataset['Operation']

        # labels = [f"{label_cat[i]}_{label_pro[i]}_{label_nav[i]}_{label_ope[i]}" for i in range(len(label_cat))]
        labels = [f"{label_cat[i]}_{label_pro[i]}" for i in range(len(label_cat))]
        # labels = [f"{label_cat[i]}" for i in range(len(label_cat))]
        # print(Counter(labels1))
        # print(Counter(labels2))
        # print(Counter(labels3))

        dataset = labeled_dataset.drop(columns=["Category", "Protocol", "Navigator", "Operation"])
        embeddings = dataset.to_numpy()

        # Encode labels
        self.label_encoder = LabelEncoder()
        labels = self.label_encoder.fit_transform(labels)

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            embeddings, labels, test_size=0.2, random_state=42
        )

        # Prepare datasets and dataloaders
        train_dataset = CombinedDataset(X_train, y_train)
        test_dataset = CombinedDataset(X_test, y_test)
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
        test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

        # Define model
        input_dim = embeddings.shape[1]  # Dimension of the combined embeddings
        num_classes = len(self.label_encoder.classes_)
        self.model = FullyConnectedClassifier(input_dim, num_classes)

        # Training setup
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(device)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.CrossEntropyLoss()

        # Training loop
        epochs = 10
        for epoch in range(epochs):
            train_loss = train_model(self.model, train_loader, optimizer, criterion, device)
            accuracy = evaluate_model(self.model, test_loader, device)
            print(f"Epoch {epoch + 1}/{epochs}, Loss: {train_loss:.4f}, Accuracy: {accuracy:.4f}")

        # Final evaluation
        final_accuracy = evaluate_model(self.model, test_loader, device)
        print(f"Final Test Accuracy: {final_accuracy:.4f}")

    def predict_new_data(self, csv_path):
        """
        בצע חיזוי על קובץ CSV חדש באמצעות המודל המאומן.
        """
        if self.model is None or self.label_encoder is None:
            raise ValueError("The model must be trained before predictions can be made.")

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        predicted_labels = predict_labels(self.model, csv_path, device, self.label_encoder)
        return predicted_labels

# if __name__ == "__main__":
#     dir_embeddings_type = "4-embeddings/combined_tls_md"
#     dir_embeddings_type = "4-embeddings/seperated_tls_md"
#     csv_embedding_process = "embeddings_seperate_changing.csv"
#     csv_embedding_process = "embeddings_seperate_same.csv"
#     csv_embedding_process = "embeddings_combined.csv"
#     csv_embedding_process = "embeddings_combined.csv"
#
#     dir = f"{dir_embeddings_type}/{csv_embedding_process}"
#     agent = AppAgent(dir)
    # labeled_dataset = pd.read_csv("embeddings_seperate_same.csv")
