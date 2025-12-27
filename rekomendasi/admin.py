from django.contrib import admin
from django.utils.html import format_html
from .models import Place, Category, Favorite


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    # Kolom yang ditampilkan di daftar admin
    list_display = (
        "name",
        "category",
        "rating",
        "review_count",      # pastikan field ini ada di model
        "ticket_info_short", # ringkasan info tiket
        "show_image",
    )

    # Field yang tidak bisa diedit manual (cuma preview)
    readonly_fields = ("image_preview",)

    # Urutan dan isi form edit data
    fields = (
        "name",
        "category",
        "description",
        "address",
        "rating",
        "review_count",   # bisa diisi manual dari GMaps
        "facilities",
        "ticket_info",    # kolom baru pengganti weekday/weekend/parkir
        "image",          # URL gambar bisa diedit manual
        "image_preview",  # preview gambar otomatis
        "coordinates",
        "opening_hours",
    )

    # Pengaturan filter dan pencarian
    search_fields = ("name", "category__name", "address")
    list_filter = ("category",)
    list_per_page = 20

    # ✅ Tampilkan gambar di daftar (list)
    def show_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:70px; height:50px; object-fit:cover; '
                'border-radius:5px; box-shadow:0 2px 6px rgba(0,0,0,0.2);">',
                obj.image,
            )
        return "-"
    show_image.short_description = "Preview"

    # ✅ Preview gambar di halaman edit
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px; border-radius:8px; '
                'box-shadow:0 2px 10px rgba(0,0,0,0.15); margin-top:5px;">',
                obj.image,
            )
        return "Belum ada gambar."
    image_preview.short_description = "Preview Gambar"

    # ✅ Ringkas ticket_info di list (biar nggak kepanjangan)
    def ticket_info_short(self, obj):
        if obj.ticket_info:
            text = obj.ticket_info
            return text if len(text) <= 40 else text[:40] + "..."
        return "-"
    ticket_info_short.short_description = "Info Tiket"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "place", "created_at")
    search_fields = ("user__username", "place__name")
    list_filter = ("created_at",)
