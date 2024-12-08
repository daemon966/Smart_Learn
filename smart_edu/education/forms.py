# education/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True)
    age = forms.IntegerField(required=True)

    class Meta:
        model = User
        fields = ['username', 'full_name', 'age', 'password1', 'password2']


from django import forms

class RegisterForm(forms.Form):  # or forms.ModelForm
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    age = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))



from django import forms
from .models import QuizQuestion

class QuizForm(forms.Form):
    def __init__(self, *args, **kwargs):
        topic = kwargs.pop('topic', None)
        super(QuizForm, self).__init__(*args, **kwargs)
        if topic:
            questions = QuizQuestion.objects.filter(topic=topic)
            for index, question in enumerate(questions):
                self.fields[f'question_{index}'] = forms.ChoiceField(
                    choices=[(question.option_1, question.option_1),
                             (question.option_2, question.option_2),
                             (question.option_3, question.option_3),
                             (question.option_4, question.option_4)],
                    label=question.question,
                    widget=forms.RadioSelect
                )
