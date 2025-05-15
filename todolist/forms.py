from django import forms
from .models import ToDoList

class AddTaskForm(forms.ModelForm):
    title = forms.CharField(),
    description = forms.CharField(),
    priority = forms.ChoiceField(widget=forms.Select(attrs={
            'class': 'form-select' # Опционально: inline-стили
        }), label="Статус сотрудника", choices=(
    ("Высокий", "Высокий"), ("Средний", "Средний"), ("Низкий", "Низкий")))

    category = forms.CharField(),
    class Meta:
        model = ToDoList
        fields = ['title', 'description', 'time', 'priority', 'category']
        labels = {'title': 'Название', 'description': 'Описание', 'time': 'Дэдлаен', 'priority': 'Приоретет', 'category': 'Категория'}

        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "time": forms.DateInput(attrs={"class": "form-control", "type":"date"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
        }