# rekomendasi/ml_utils.py
import re
import pandas as pd

# Daftar stopword sederhana bahasa Indonesia (bisa ditambah manual atau pakai library Sastrawi)
STOPWORDS = set([
    "dan", "yang", "di", "ke", "dari", "ini", "itu", "untuk", "pada", "adalah", 
    "sebagai", "dengan", "juga", "karena", "sehingga", "namun", "tetapi", 
    "atau", "oleh", "sudah", "akan", "bisa", "dapat", "kami", "kita", 
    "saya", "anda", "mereka", "ada", "dalam", "luar", "atas", "bawah"
])

def clean_text(text):
    """
    Membersihkan teks: lowercase, hapus angka/simbol, dan hapus stopwords.
    """
    if pd.isna(text) or not text:
        return ""
    
    # 1. Ubah ke lowercase
    text = str(text).lower()
    
    # 2. Hapus karakter selain huruf (angka dan tanda baca hilang)
    text = re.sub(r'[^a-z\s]', ' ', text)
    
    # 3. Tokenisasi (pecah jadi kata-kata)
    tokens = text.split()
    
    # 4. Stopword removal (Hapus kata umum yang tidak bermakna unik)
    tokens = [word for word in tokens if word not in STOPWORDS and len(word) > 2]
    
    # 5. Gabung kembali
    return " ".join(tokens)