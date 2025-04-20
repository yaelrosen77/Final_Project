import pandas as pd
import os

def load_links_from_excel(sheet_name: str, excel_path="App_direct_links.xlsx"):
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file '{excel_path}' not found")

    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
    urls = df[1].dropna().tolist()
    class_names = df[0].fillna("").tolist()

    results = []
    for i in range(len(urls)):
        url = urls[i]
        extra = class_names[i] if i < len(class_names) else ""
        if isinstance(url, str) and url.startswith("http"):
            results.append((url, extra))
    return results
