// static/js/main.js
// small helper: get geolocation and set hidden fields so server can compute distance
function getLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(function(pos){
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      const latInput = document.getElementById('lat');
      const lonInput = document.getElementById('lon');
      if (latInput) latInput.value = lat;
      if (lonInput) lonInput.value = lon;
    }, function(err){
      console.warn('geo error', err);
    });
  }
  
  document.addEventListener('DOMContentLoaded', function(){
    // try to fill location
    getLocation();
  });

  window.addEventListener("scroll", function () {
    const navbar = document.querySelector(".navbar");
    if (window.scrollY > 30) {
      navbar.classList.add("scrolled");
    } else {
      navbar.classList.remove("scrolled");
    }
  });
  
  document.addEventListener("DOMContentLoaded", function () {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
  
    document.querySelectorAll(".btn-favorite").forEach((favBtn) => {
      favBtn.addEventListener("click", async () => {
        const url = favBtn.dataset.url;
        if (!url) return;
  
        try {
          const response = await fetch(url, {
            method: "POST",
            headers: {
              "X-CSRFToken": csrfToken,
            },
          });
          const data = await response.json();
  
          if (data.success) {
            favBtn.textContent = data.favorited
              ? "💔 Hapus dari Favorit"
              : "❤️ Tambah ke Favorit";
          } else {
            alert("Gagal memperbarui favorit.");
          }
        } catch (error) {
          console.error("Error toggle favorite:", error);
        }
      });
    });
  });

  // Efek klik & hapus favorit
  document.querySelectorAll('.btn-remove-fav').forEach(btn => {
    btn.addEventListener('click', async () => {
      const url = btn.dataset.url;
      const card = btn.closest('.favorite-card');

      // Tambahkan animasi klik
      btn.classList.add('active');

      try {
        const res = await fetch(url);
        if (res.ok) {
          // Getar sedikit biar seperti “unsave”
          btn.querySelector('.icon-save').style.animation = 'saveShake 0.3s';
          // Hilangkan card setelah delay kecil
          setTimeout(() => {
            card.style.transition = 'all 0.4s ease';
            card.style.transform = 'scale(0.9)';
            card.style.opacity = '0';
            setTimeout(() => card.remove(), 400);
          }, 300);
        }
      } catch (e) {
        console.error("Gagal menghapus favorit:", e);
      }

      // Hapus animasi setelah selesai biar bisa diklik lagi
      setTimeout(() => btn.classList.remove('active'), 600);
    });
  });

  document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("userMenuBtn");
    const dropdown = document.getElementById("userDropdown");
  
    if (!btn || !dropdown) return;
  
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdown.classList.toggle("open");
    });
  
    // Klik di luar menutup dropdown
    document.addEventListener("click", () => {
      dropdown.classList.remove("open");
    });
  });
  

  