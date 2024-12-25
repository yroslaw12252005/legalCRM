from django import forms
from .models import ToDoList

class AddTaskForm(forms.ModelForm):
    title = forms.CharField(),
    description = forms.CharField(),
    time = forms.DateField(label="Дэдлаен"),
    priority = forms.ChoiceField(label="Приоретет", choices=(("Высокий", "Высокий"), ("Средний", "Средний"), ("Низкий", "Низкий"))),
    category = forms.CharField(),
    class Meta:
        model = ToDoList
        fields = ['title', 'description', 'time', 'priority', 'category']
        labels = {'title': 'Название', 'description': 'Описание', 'time': 'Дэдлаен', 'priority': 'Приоретет', 'category': 'Категория'}