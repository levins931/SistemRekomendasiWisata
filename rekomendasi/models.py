# rekomendasi/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

import uuid
from django.db import models

class Place(models.Model):
    place_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    rating = models.FloatField(null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0)
    facilities = models.TextField(blank=True)
    ticket_info = models.TextField(
        blank=True,
        help_text="Contoh: Weekday 10k, Weekend 20k, Parkir motor 2k, mobil 5k"
    )
    image = models.URLField(blank=True)
    coordinates = models.CharField(max_length=100, blank=True)
    opening_hours = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'place')
        verbose_name = "Favorit"
        verbose_name_plural = "Favorit"

    def __str__(self):
        return f"{self.user.username} ❤️ {self.place.name}"