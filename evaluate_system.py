#!/usr/bin/env python3
import os, sqlite3, joblib, re
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# ================= KONFIGURASI =================
DB_PATH = "db.sqlite3"
MODELS_DIR = "models"
TABLE_NAME = "rekomendasi_place" 
COL_NAME = "name"
COL_DESC = "description"
COL_FACILITIES = "facilities"

# SKENARIO PENGUJIAN
# Format: "Query": ["kata_kunci_wajib"]
SCENARIOS = {
    "wisata alam sejuk": ["alam", "sejuk", "gunung", "bukit", "hutan", "air terjun", "danau", "sawah"],
    "pantai pasir putih": ["pantai", "laut", "pasir", "pesisir", "samudera", "gili"],
    "wisata sejarah candi": ["candi", "sejarah", "museum", "prasasti", "kuno", "budaya", "purbakala"],
    "tempat bermain anak": ["anak", "bermain", "keluarga", "taman", "kolam", "waterpark", "edukasi"],
    "air terjun indah": ["air terjun", "curug", "coban", "tumpak"]
}

# Ambang batas kemiripan (Sesuai request: yang penting tidak 0)
MIN_SCORE = 0.0 
# ===============================================

def clean_text(text):
    if text is None: return ""
    return str(text).lower()

def is_relevant(text_content, keywords):
    """Mengecek apakah text mengandung salah satu keyword target"""
    for k in keywords:
        if k in text_content:
            return True
    return False

def main():
    print("--- MEMULAI EVALUASI DINAMIS (SEMUA HASIL > 0) ---")
    
    # 1. Load Model
    try:
        vectorizer = joblib.load(os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib"))
        matrix = joblib.load(os.path.join(MODELS_DIR, "tfidf_matrix.joblib"))
        # Kita butuh place_ids untuk mapping yang akurat jika urutan DB beda
        # Tapi untuk simplifikasi evaluasi expert judgment, kita pakai text matching via DB dump
    except Exception as e:
        print(f"Error loading models: {e}")
        return

    # 2. Load Database (Ground Truth)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    try:
        # Ambil semua data
        query_sql = f"SELECT {COL_NAME}, {COL_DESC}, {COL_FACILITIES} FROM {TABLE_NAME}"
        cur.execute(query_sql)
        all_places = []
        for row in cur.fetchall():
            full_text = clean_text(row[COL_NAME]) + " " + \
                        clean_text(row[COL_DESC]) + " " + \
                        clean_text(row[COL_FACILITIES])
            all_places.append({
                "name": row[COL_NAME],
                "content": full_text
            })
        print(f"Total data di database: {len(all_places)} destinasi.")
            
    except Exception as e:
        print(f"Error database: {e}")
        return

    # 3. Proses Evaluasi
    evaluation_results = []

    for query, keywords in SCENARIOS.items():
        print(f"\nMenilai Skenario: '{query}'...")
        
        # A. Hitung TOTAL RELEVAN di DB (Ground Truth untuk Recall)
        total_relevant_db = 0
        for p in all_places:
            if is_relevant(p['content'], keywords):
                total_relevant_db += 1
        
        if total_relevant_db == 0:
            print(f"  -> Skip (Tidak ada data relevan di DB)")
            continue

        # B. Jalankan Sistem (Simulasi)
        q_clean = clean_text(query)
        q_vec = vectorizer.transform([q_clean])
        sims = cosine_similarity(q_vec, matrix).flatten()
        
        # C. Filter Hasil: Hanya ambil yang skor > 0
        # Dapatkan index yang skornya > 0
        valid_indices = np.where(sims > MIN_SCORE)[0]
        
        # Urutkan dari skor tertinggi ke terendah
        sorted_indices = valid_indices[np.argsort(sims[valid_indices])[::-1]]
        
        # N_Retrieved = Jumlah item yang ditampilkan sistem
        n_retrieved = len(sorted_indices)
        
        # D. Cek Relevansi Hasil (TP)
        tp_count = 0
        
        # Loop semua hasil yang muncul
        for idx in sorted_indices:
            if idx < len(all_places):
                place_data = all_places[idx]
                if is_relevant(place_data['content'], keywords):
                    tp_count += 1
        
        # E. Hitung Metrik
        # Precision = TP / Jumlah Yang Tampil
        if n_retrieved > 0:
            precision = (tp_count / n_retrieved) * 100
        else:
            precision = 0.0
        
        # Recall = TP / Total Relevan di DB
        recall = (tp_count / total_relevant_db) * 100
        if recall > 100: recall = 100.0
        
        # F1 Score
        if (precision + recall) > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0.0
            
        print(f"  -> Sistem Menampilkan: {n_retrieved} item (Skor > 0)")
        print(f"  -> Dari {n_retrieved} item, yang Relevan (TP): {tp_count}")
        print(f"  -> Metrics: P={precision:.1f}%, R={recall:.1f}%, F1={f1:.1f}%")

        evaluation_results.append({
            "Skenario Query": query,
            "Jml Tampil (N)": n_retrieved,
            "Relevan (TP)": tp_count,
            "Total Relevan di DB": total_relevant_db,
            "Precision (%)": round(precision, 1),
            "Recall (%)": round(recall, 1),
            "F1-Score (%)": round(f1, 1)
        })

    # 4. Simpan ke CSV
    df = pd.DataFrame(evaluation_results)
    
    avg_row = {
        "Skenario Query": "RATA-RATA",
        "Jml Tampil (N)": df["Jml Tampil (N)"].mean(),
        "Relevan (TP)": df["Relevan (TP)"].mean(),
        "Total Relevan di DB": "-",
        "Precision (%)": df["Precision (%)"].mean(),
        "Recall (%)": df["Recall (%)"].mean(),
        "F1-Score (%)": df["F1-Score (%)"].mean()
    }
    
    df = pd.concat([df, pd.DataFrame([avg_row])], ignore_index=True)
    
    output_file = "table6_dynamic_evaluation.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✅ Selesai! Cek file '{output_file}'")
    print(df)

if __name__ == "__main__":
    main()