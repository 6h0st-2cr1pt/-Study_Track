from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import GradeEntry, StudentProfile, Subject


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class GradeEntryForm(forms.Form):
    subject_name = forms.CharField(label='Subject', max_length=120)
    grading_period = forms.ChoiceField(choices=GradeEntry.PERIOD_CHOICES)
    grade = forms.DecimalField(min_value=0, max_value=100, decimal_places=2, max_digits=5)
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    def clean_subject_name(self):
        value = self.cleaned_data['subject_name']
        return ' '.join(value.strip().split())


class GoalForm(forms.Form):
    subject = forms.ModelChoiceField(label='Subject', queryset=Subject.objects.none(), empty_label='Select a subject')
    target_grade = forms.DecimalField(min_value=0, max_value=100, decimal_places=2, max_digits=5)
    active = forms.BooleanField(required=False, initial=True)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['subject'].queryset = Subject.objects.filter(user=user).order_by('name')


class ProfileManagementForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    institution = forms.CharField(max_length=150, required=False)
    program = forms.CharField(max_length=150, required=False)
    year_level = forms.CharField(max_length=50, required=False)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['institution'].initial = profile.institution
            self.fields['program'].initial = profile.program
            self.fields['year_level'].initial = profile.year_level

    def save(self):
        profile, _ = StudentProfile.objects.get_or_create(user=self.user)
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        self.user.save(update_fields=['first_name', 'last_name', 'email'])

        profile.institution = self.cleaned_data['institution']
        profile.program = self.cleaned_data['program']
        profile.year_level = self.cleaned_data['year_level']
        profile.save(update_fields=['institution', 'program', 'year_level', 'updated_at'])
        return self.user, profile



