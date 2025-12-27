# rekomendasi/views.py
import os
import joblib
from typing import Optional, Tuple, List

from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors

from .models import Place, Favorite, Category
from .ml_utils import clean_text

# ---------------------------
# Konfigurasi path model
# ---------------------------
# Folder models di root project (settings.BASE_DIR / "models")
MODEL_DIR = os.path.join(settings.BASE_DIR, "models")
TFIDF_VEC_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.joblib")
TFIDF_MATRIX_PATH = os.path.join(MODEL_DIR, "tfidf_matrix.joblib")
KNN_MODEL_PATH = os.path.join(MODEL_DIR, "knn_model.joblib")
PLACE_IDS_PATH = os.path.join(MODEL_DIR, "place_ids.joblib")

# Ambang batas kemiripan untuk menampilkan hasil
SIMILARITY_THRESHOLD = 0.05

# ---------------------------
# Fungsi loading model (module-scope caching)
# ---------------------------
def load_models() -> Tuple[Optional[object], Optional[object], Optional[object], Optional[List[str]]]:
    """
    Coba load model dari disk. Jika gagal, kembalikan None.
    Dipanggil sekali saat module diimport.
    """
    try:
        vec = joblib.load(TFIDF_VEC_PATH)
        mat = joblib.load(TFIDF_MATRIX_PATH)
        knn = joblib.load(KNN_MODEL_PATH)
        ids = joblib.load(PLACE_IDS_PATH)
        ids = [str(i) for i in ids]
        return vec, mat, knn, ids
    except Exception as e:
        # Print untuk debugging di console; views akan menampilkan pesan ramah ke user/admin.
        print("Warning: gagal load models:", e)
        return None, None, None, None

TFIDF_VECTOR, TFIDF_MATRIX, KNN_MODEL, PLACE_IDS = load_models()


def ensure_models_available(request):
    """
    Jika model belum tersedia, render halaman error yang memberitahu admin untuk
    menjalankan command build_models. Dipakai oleh views yang butuh model.
    """
    if TFIDF_VECTOR is None or TFIDF_MATRIX is None:
        return render(request, "error.html", {
            "message": "Model rekomendasi belum dibangun. Jalankan: python manage.py build_models"
        })
    return None


# ---------------------------
# Helper untuk mengambil Place dari DB
# ---------------------------
def get_place_obj(place_id):
    try:
        return Place.objects.select_related('category').get(place_id=place_id)
    except Place.DoesNotExist:
        return None


# ---------------------------
# Home
# ---------------------------
@login_required(login_url='login')
def home(request):
    wisata_list = (
        Place.objects
        .select_related('category')
        .exclude(image="")
        .order_by('?')[:6]
    )

    return render(request, "home.html", {
        "wisata_list": wisata_list
    })

# ---------------------------
# Search TF-IDF (Content-Based Filtering)
# ---------------------------
@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def search_tfidf(request):
    """
    Pencarian berbasis TF-IDF:
    - Ambil query dari POST['preferensi'] atau GET['q']
    - Transform dan hitung cosine similarity terhadap TFIDF_MATRIX
    - Tampilkan hasil yang memiliki skor >= SIMILARITY_THRESHOLD
    """
    # cek model tersedia
    err = ensure_models_available(request)
    if err:
        return err

    query = ""
    results = []
    sort = request.GET.get("sort", "")

    # Ambil query dari form atau param
    if request.method == "POST" and request.POST.get("preferensi"):
        query = request.POST.get("preferensi", "").strip()
    elif request.GET.get("q"):
        query = request.GET.get("q", "").strip()

    if query:
        q_clean = clean_text(query)
        try:
            q_vec = TFIDF_VECTOR.transform([q_clean])
            sims = cosine_similarity(q_vec, TFIDF_MATRIX).flatten()
        except Exception as e:
            # Jika ada masalah transform / similarity, tampilkan pesan sederhana
            print("TF-IDF / similarity error:", e)
            return render(request, "error.html", {"message": "Terjadi kesalahan pada pemrosesan query."})

        # Ambil top candidate (batasi 30)
        idxs = sims.argsort()[::-1][:30]

        for i in idxs:
            score = float(sims[i])
            if score >= SIMILARITY_THRESHOLD:
                try:
                    place_id = PLACE_IDS[i]
                except Exception:
                    continue
                p = get_place_obj(place_id)
                if not p:
                    continue
                results.append({
                    "place_id": place_id,
                    "name": p.name,
                    "category": p.category.name if p.category else "",
                    "description": (p.description or "")[:150] + ("..." if (p.description and len(p.description) > 150) else ""),
                    "score": round(score, 3),
                    "rating": p.rating or 0,
                    "review_count": getattr(p, "review_count", 0),
                    "image": p.image or ""
                })

    # Sorting: rating atau 'harga' (di kode asli 'harga' dipetakan ke skor)
    if sort and results:
        if sort == "rating":
            results = sorted(results, key=lambda x: x.get("rating", 0), reverse=True)
        elif sort == "harga":
            results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)

    return render(request, "search_tfidf.html", {
        "results": results,
        "query": query,
        "sort": sort
    })


# ---------------------------
# Detail Wisata + rekomendasi mirip (KNN)
# ---------------------------
def detail_wisata(request, place_id):
    """
    Tampilkan detail tempat dan rekomendasi mirip berdasarkan KNN.
    KNN dan TF-IDF di-load dari disk (production model).
    """
    place = get_place_obj(place_id)
    if not place:
        return render(request, "404.html", {"message": "Place not found"})

    item_detail = {
        "Place_Id": str(place.place_id),
        "Place_Name": place.name,
        "Category": place.category.name if place.category else "",
        "Description": place.description,
        "Facilities": place.facilities,
        "Ticket_Info": getattr(place, "ticket_info", ""),
        "Rating": place.rating,
        "Review_Count": getattr(place, "review_count", 0),
        "Image": place.image,
        "Coordinates": place.coordinates,
    }


    # jika model tidak ada, tampilkan detail saja dengan peringatan
    if TFIDF_MATRIX is None or KNN_MODEL is None or PLACE_IDS is None:
        return render(request, "detail.html", {
            "item": item_detail,
            "rekomendasi_mirip": [],
            "warning": "Model rekomendasi belum tersedia. Jalankan: python manage.py build_models"
        })

    # cari index di PLACE_IDS
    try:
        idx = PLACE_IDS.index(str(place_id))
    except ValueError:
        idx = None

    rekomendasi_mirip = []
    if idx is not None:
        try:
            # TFIDF_MATRIX[idx] memberikan 1xN vector (sparse matrix row)
            distances, indices = KNN_MODEL.kneighbors(TFIDF_MATRIX[idx], n_neighbors=6)
            for i, dist in zip(indices[0][1:], distances[0][1:]):  # skip self
                sim = 1 - float(dist)
                if sim >= SIMILARITY_THRESHOLD:
                    pid = PLACE_IDS[i]
                    p = get_place_obj(pid)
                    if not p:
                        continue
                    rekomendasi_mirip.append({
                        "place_id": pid,
                        "name": p.name,
                        "category": p.category.name if p.category else "",
                        "description": (p.description or "")[:120] + ("..." if (p.description and len(p.description) > 120) else ""),
                        "image": p.image or "",
                        "similarity": round(sim, 3)
                    })
        except Exception as e:
            # log error di console, tapi UI tetap stabil (tanpa rekomendasi mirip)
            print("KNN error:", e)
            rekomendasi_mirip = []

    return render(request, "detail.html", {
        "item": item_detail,
        "rekomendasi_mirip": rekomendasi_mirip
    })


# ---------------------------
# Auth: register, login, logout
# ---------------------------
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        if password != password2:
            messages.error(request, "Password tidak sama!")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username sudah dipakai.")
            return redirect("register")

        User.objects.create_user(username=username, password=password)
        messages.success(request, "Registrasi berhasil. Silakan login!")
        return redirect("login")

    return render(request, "auth/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Login berhasil!")
            return redirect("home")
        else:
            messages.error(request, "Username atau password salah.")
            return redirect("login")
    return render(request, "auth/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Anda berhasil logout.")
    return redirect("login")


# ---------------------------
# Favorites: toggle + list
# ---------------------------
@login_required(login_url='login')
def toggle_favorite(request, place_id):
    """
    Tambah / hapus tempat dari favorit user.
    Mengembalikan JSON {success, favorited}
    """
    place = Place.objects.filter(place_id=place_id).first()
    if not place:
        return JsonResponse({"success": False, "message": "Tempat tidak ditemukan."})

    favorite, created = Favorite.objects.get_or_create(user=request.user, place=place)
    if not created:
        favorite.delete()
        return JsonResponse({"success": True, "favorited": False})
    return JsonResponse({"success": True, "favorited": True})


@login_required(login_url='login')
def list_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('place')
    return render(request, "favorites.html", {"favorites": favorites})
