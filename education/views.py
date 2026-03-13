from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoryForm, MaterialForm
from .models import Category, Material


STATUS_ADMIN = "Администратор"


@login_required
def material_list(request):
    categories = Category.objects.filter(companys=request.user.companys).order_by("name")
    materials = Material.objects.filter(companys=request.user.companys).select_related("category")

    query = (request.GET.get("q") or "").strip()
    category_id = (request.GET.get("category") or "").strip()

    if query:
        materials = materials.filter(
            Q(title__icontains=query) | Q(body__icontains=query) | Q(document__icontains=query)
        )
    if category_id:
        materials = materials.filter(category_id=category_id)

    materials = materials.order_by("-created_at")

    return render(
        request,
        "education/material_list.html",
        {
            "materials": materials,
            "categories": categories,
            "query": query,
            "selected_category": category_id,
        },
    )


@login_required
def material_detail(request, pk):
    material = get_object_or_404(Material, id=pk, companys=request.user.companys)
    return render(request, "education/material_detail.html", {"material": material})


@login_required
def material_create(request):
    if request.user.status != STATUS_ADMIN:
        messages.warning(request, "Нет прав для добавления материала")
        return redirect("education_list")

    form = MaterialForm(request.POST or None, request.FILES or None)
    form.fields["category"].queryset = Category.objects.filter(companys=request.user.companys).order_by("name")
    if request.method == "POST" and form.is_valid():
        material = form.save(commit=False)
        material.companys = request.user.companys
        material.created_by = request.user
        material.save()
        messages.success(request, "Материал успешно добавлен")
        return redirect("education_detail", pk=material.id)

    return render(request, "education/material_form.html", {"form": form})


@login_required
def material_edit(request, pk):
    if request.user.status != STATUS_ADMIN:
        messages.warning(request, "Нет прав для редактирования материала")
        return redirect("education_list")

    material = get_object_or_404(Material, id=pk, companys=request.user.companys)
    form = MaterialForm(request.POST or None, request.FILES or None, instance=material)
    form.fields["category"].queryset = Category.objects.filter(companys=request.user.companys).order_by("name")

    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        updated.companys = request.user.companys
        if updated.created_by is None:
            updated.created_by = request.user
        updated.save()
        messages.success(request, "Материал успешно обновлен")
        return redirect("education_detail", pk=material.id)

    return render(request, "education/material_form.html", {"form": form, "material": material})


@login_required
def material_delete(request, pk):
    if request.user.status != STATUS_ADMIN:
        messages.warning(request, "Нет прав для удаления материала")
        return redirect("education_list")

    material = get_object_or_404(Material, id=pk, companys=request.user.companys)
    if request.method == "POST":
        material.delete()
        messages.success(request, "Материал удален")
        return redirect("education_list")

    return render(request, "education/material_delete.html", {"material": material})


@login_required
def category_create(request):
    if request.user.status != STATUS_ADMIN:
        messages.warning(request, "Нет прав для добавления категории")
        return redirect("education_list")

    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        name = form.cleaned_data["name"].strip()
        if Category.objects.filter(companys=request.user.companys, name__iexact=name).exists():
            messages.warning(request, "Такая категория уже существует")
        else:
            category = form.save(commit=False)
            category.name = name
            category.companys = request.user.companys
            category.save()
            messages.success(request, "Категория успешно добавлена")
            return redirect("education_list")

    return render(request, "education/category_form.html", {"form": form})
