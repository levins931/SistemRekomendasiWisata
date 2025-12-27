function pilihKategori(kategori) {
    // Otomatis kirim form dengan kategori terpilih
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/search_ml/";
  
    const csrf = document.querySelector("input[name='csrfmiddlewaretoken']").cloneNode();
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "preferensi";
    input.value = kategori;
  
    form.appendChild(csrf);
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
  }
