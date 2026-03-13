from django.db import models
from accounts.models import User
from company.models import Companys


class Category(models.Model):
    name = models.CharField(max_length=120)
    companys = models.ForeignKey(Companys, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("name", "companys")
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self) -> str:
        return self.name


class Material(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    document = models.FileField(upload_to="education_docs/", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="materials")
    companys = models.ForeignKey(Companys, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"

    def __str__(self) -> str:
        return self.title
