# rekomendasi/management/commands/evaluate_offline.py
import numpy as np
from django.core.management.base import BaseCommand
from rekomendasi.models import Place
from rekomendasi.ml_utils import clean_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.model_selection import train_test_split

def eval_with_category_proxy(docs, cats, ids, test_size=0.2, random_state=42, top_k=5):
    # Stratified split berdasarkan kategori
    X_train_idx, X_test_idx = train_test_split(
        range(len(docs)),
        test_size=test_size,
        random_state=random_state,
        stratify=cats
    )

    docs_train = [docs[i] for i in X_train_idx]
    docs_test = [docs[i] for i in X_test_idx]
    cats_train = [cats[i] for i in X_train_idx]
    cats_test = [cats[i] for i in X_test_idx]

    # TF-IDF fit hanya pada training
    vectorizer = TfidfVectorizer(ngram_range=(1,2), min_df=1)
    tfidf_train = vectorizer.fit_transform(docs_train)
    tfidf_test = vectorizer.transform(docs_test)

    # KNN fit pada training set
    knn = NearestNeighbors(n_neighbors=top_k, metric="cosine")
    knn.fit(tfidf_train)

    dists, neighbors = knn.kneighbors(tfidf_test, n_neighbors=top_k)

    precisions, recalls, f1s = [], [], []
    for i in range(len(docs_test)):
        rec_idxs = neighbors[i]
        # relevan (= kategori sama)
        relevant = sum(1 for idx in rec_idxs if cats_train[idx] == cats_test[i])
        total_relevant = sum(1 for c in cats_train if c == cats_test[i])

        prec = relevant / top_k
        rec = relevant / total_relevant if total_relevant > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0

        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    return {
        "precision": float(np.mean(precisions)),
        "recall": float(np.mean(recalls)),
        "f1": float(np.mean(f1s)),
        "n_test": len(docs_test)
    }

class Command(BaseCommand):
    help = "Offline evaluation dengan train/test split (TF-IDF + KNN)"

    def add_arguments(self, parser):
        parser.add_argument("--runs", type=int, default=5)
        parser.add_argument("--top_k", type=int, default=5)
        parser.add_argument("--test_size", type=float, default=0.2)

    def handle(self, *args, **options):
        qs = Place.objects.select_related("category").all()

        docs = []
        cats = []
        ids = []

        # Buat data text final
        for p in qs:
            text = " ".join(filter(None, [
                p.category.name if p.category else "",
                p.description or "",
                p.facilities or ""
            ]))
            docs.append(clean_text(text))
            cats.append(p.category.name if p.category else "")
            ids.append(str(p.place_id))

        all_results = []

        for i in range(options["runs"]):
            res = eval_with_category_proxy(
                docs, cats, ids,
                test_size=options["test_size"],
                top_k=options["top_k"],
                random_state=42 + i
            )
            all_results.append(res)
            self.stdout.write(f"Run {i+1}: {res}")

        avg_result = {
            "precision_avg": float(np.mean([r["precision"] for r in all_results])),
            "recall_avg": float(np.mean([r["recall"] for r in all_results])),
            "f1_avg": float(np.mean([r["f1"] for r in all_results]))
        }

        self.stdout.write(self.style.SUCCESS(f"Average results: {avg_result}"))
