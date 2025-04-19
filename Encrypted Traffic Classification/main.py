import tkinter as tk
from tkinter import filedialog, messagebox
import pickle
import os
import sys
from process_pcaps import PcapProcessor
from app_agent import AppAgent
from cat_agent import CatAgent

current_dir = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.join(current_dir, '4-embeddings', 'combined_tls_md'))
# from FCE_combined_all_same import FeatureCombinationEncoder
sys.path.append(os.path.join(current_dir, '4-embeddings', 'seperated_tls_md'))
from FCE_seperate_same import FeatureCombinationEncoder

class FCEApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FCE Manager")
        self.model = None
        self.setup_gui()
    def setup_gui(self):
        tk.Label(self.root, text="Pcaps Directory:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.pcaps_entry = tk.Entry(self.root, width=40)
        self.pcaps_entry.grid(row=0, column=1, padx=10, pady=5)
        tk.Button(self.root, text="Browse", command=self.browse_pcaps).grid(row=0, column=2, padx=10, pady=5)

        tk.Label(self.root, text="Output Directory:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.output_entry = tk.Entry(self.root, width=40)
        self.output_entry.grid(row=2, column=1, padx=10, pady=5)
        tk.Button(self.root, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=10, pady=5)

        tk.Button(self.root, text="Process for FCE", command=self.process_data).grid(row=3, column=0, columnspan=1, pady=10)
        tk.Button(self.root, text="Train FCE", command=self.create_embedding).grid(row=3, column=1, columnspan=1, pady=10)
        tk.Button(self.root, text="Train Model", command=self.train_model).grid(row=3, column=2, columnspan=1, pady=10)
        tk.Button(self.root, text="Load FCE", command=self.load_fce).grid(row=4, column=0, columnspan=3, pady=10)
        tk.Button(self.root, text="Save FCE", command=self.save_fce).grid(row=5, column=0, columnspan=3, pady=10)

    def browse_pcaps(self):
        directory = filedialog.askdirectory()
        if directory:
            self.pcaps_entry.delete(0, tk.END)
            self.pcaps_entry.insert(0, directory)
    def browse_output(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)

    def train_model(self):
        if not all([self.output_entry.get()]):
            messagebox.showerror("Error", "Please fill in output directory.")
            return
        train_file = self.output_entry.get()+"/embeddings_combined_all_same.csv"
        # train_file = self.output_entry.get()+"/embeddings_seperate_changing.xlsx"
        test_file = self.output_entry.get()+"/embeddings_combined_all_same.csv"
        # test_file = self.output_entry.get()+"/embeddings_seperate_changing.xlsx"

        appAgent = AppAgent(train_file)
        appAgent.start_training()

        catAgent = CatAgent(train_file)
        catAgent.start_training()

        app_predictions = appAgent.predict_new_data(test_file)
        cat_predictions = catAgent.predict_new_data(test_file)
        print(app_predictions)
        print(cat_predictions)

    def create_embedding(self):
        if not all([self.output_entry.get()]):
            messagebox.showerror("Error", "Please fill in output directory.")
            return
        encoder = FeatureCombinationEncoder(self.output_entry.get())
        encoder.process_all_categories()
        self.model = encoder
        messagebox.showinfo("Success", "FCE training completed and features processed.")
    def process_data(self):
        if not all([self.pcaps_entry.get(), self.output_entry.get()]):
            messagebox.showerror("Error", "Please fill in all directories before training.")
            return
        processor = PcapProcessor(self.pcaps_entry.get(), self.output_entry.get())
        processor.split_and_extract()

    def load_fce(self):
        file_path = filedialog.askopenfilename(filetypes=[("Pickle Files", "*.pkl")])
        if file_path:
            with open(file_path, 'rb') as f:
                self.model = pickle.load(f)
            messagebox.showinfo("Success", "FCE model loaded successfully.")
    def save_fce(self):
        if self.model is None:
            messagebox.showerror("Error", "No trained FCE model to save.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".pkl", filetypes=[("Pickle Files", "*.pkl")])
        if file_path:
            with open(file_path, 'wb') as f:
                pickle.dump(self.model, f)
            messagebox.showinfo("Success", "FCE model saved successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = FCEApp(root)
    root.mainloop()
