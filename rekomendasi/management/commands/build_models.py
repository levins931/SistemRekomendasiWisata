# rekomendasi/management/commands/build_models.py
import os
import joblib
from django.core.management.base import BaseCommand
from rekomendasi.models import Place
from rekomendasi.ml_utils import clean_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# Gunakan path absolut agar aman saat deploy/run server
from django.conf import settings
MODEL_DIR = os.path.join(settings.BASE_DIR, "models")

class Command(BaseCommand):
    help = "Build TF-IDF and KNN models from Place data and save to disk."

    def handle(self, *args, **options):
        # Buat folder jika belum ada
        os.makedirs(MODEL_DIR, exist_ok=True)

        # Ambil semua data wisata
        qs = Place.objects.select_related("category").all()
        
        docs = []
        ids = []
        
        print(f"Memproses {qs.count()} data wisata...")

        for p in qs:
            # Gabungkan Kategori + Deskripsi + Fasilitas
            # Ini penting agar pencarian 'toilet' atau 'parkir' juga bisa terdeteksi
            text_content = [
                p.category.name if p.category else "",
                p.name, # Nama wisata juga penting dimasukkan ke fitur
                p.description or "",
                p.facilities or ""
            ]
            
            # Gabung jadi satu string
            raw_text = " ".join(filter(None, text_content))
            
            # Bersihkan teks
            cleaned = clean_text(raw_text)
            
            docs.append(cleaned)
            ids.append(str(p.place_id))

        # --- TF-IDF (Content Based Filtering) ---
        # ngram_range=(1,2) artinya mendeteksi kata tunggal dan frasa 2 kata (misal: "air terjun")
        vectorizer = TfidfVectorizer(ngram_range=(1,2), min_df=1)
        tfidf_matrix = vectorizer.fit_transform(docs)

        # --- KNN (Item Similarity) ---
        knn = NearestNeighbors(n_neighbors=6, metric="cosine")
        knn.fit(tfidf_matrix)

        # Simpan Model
        joblib.dump(vectorizer, os.path.join(MODEL_DIR, "tfidf_vectorizer.joblib"))
        joblib.dump(tfidf_matrix, os.path.join(MODEL_DIR, "tfidf_matrix.joblib"))
        joblib.dump(knn, os.path.join(MODEL_DIR, "knn_model.joblib"))
        joblib.dump(ids, os.path.join(MODEL_DIR, "place_ids.joblib"))

        self.stdout.write(self.style.SUCCESS(f"Sukses! Model disimpan di {MODEL_DIR}/"))