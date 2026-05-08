from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import GradeEntry, StudentProfile, Subject


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    institution = forms.CharField(max_length=150, required=False)
    program = forms.CharField(max_length=150, required=False)
    year_level = forms.CharField(max_length=50, required=False)
    grading_structure = forms.ChoiceField(
        choices=StudentProfile.GRADING_STRUCTURE_CHOICES,
        initial=StudentProfile.SEMESTER,
        label='School Academic Calendar',
        help_text='Select your school\'s academic calendar structure (Semester or Trimester)'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'grading_structure', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            # Update the student profile with grading structure
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            profile.grading_structure = self.cleaned_data.get('grading_structure')
            # Save additional profile fields provided during registration
            profile.institution = self.cleaned_data.get('institution', '')
            profile.program = self.cleaned_data.get('program', '')
            profile.year_level = self.cleaned_data.get('year_level', '')
            profile.save(update_fields=['grading_structure', 'institution', 'program', 'year_level'])
        return user


class GradeEntryForm(forms.Form):
	subject = forms.ModelChoiceField(label='Subject', queryset=Subject.objects.none(), empty_label='Select a subject')
	grading_period = forms.ChoiceField(label='Grading Period')
	grade = forms.DecimalField(min_value=0, max_value=100, decimal_places=2, max_digits=5, label='Grade (0-100)')
	notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

	def __init__(self, *args, user=None, **kwargs):
		super().__init__(*args, **kwargs)
		if user is not None:
			self.fields['subject'].queryset = Subject.objects.filter(user=user).order_by('name')
			
			# Get user's profile to determine grading structure
			profile, _ = StudentProfile.objects.get_or_create(user=user)
			if profile.grading_structure == StudentProfile.TRIMESTER:
				# Trimester: Prelim, Midterm, Endterm
				self.fields['grading_period'].choices = GradeEntry.TRIMESTER_PERIOD_CHOICES
			else:
				# Semester: Midterm, Endterm
				self.fields['grading_period'].choices = GradeEntry.SEMESTER_PERIOD_CHOICES


class GoalForm(forms.Form):
    subject_name = forms.CharField(label='Subject', max_length=120)
    target_grade = forms.DecimalField(min_value=0, max_value=100, decimal_places=2, max_digits=5)
    active = forms.BooleanField(required=False, initial=True)

    def clean_subject_name(self):
        value = self.cleaned_data['subject_name']
        return ' '.join(value.strip().split())


class ProfileManagementForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    institution = forms.CharField(max_length=150, required=False)
    program = forms.CharField(max_length=150, required=False)
    year_level = forms.CharField(max_length=50, required=False)
    grading_structure = forms.ChoiceField(
        choices=StudentProfile.GRADING_STRUCTURE_CHOICES,
        label='School Academic Calendar'
    )

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
            self.fields['grading_structure'].initial = profile.grading_structure

    def save(self):
        profile, _ = StudentProfile.objects.get_or_create(user=self.user)
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        self.user.save(update_fields=['first_name', 'last_name', 'email'])

        profile.institution = self.cleaned_data['institution']
        profile.program = self.cleaned_data['program']
        profile.year_level = self.cleaned_data['year_level']
        profile.grading_structure = self.cleaned_data['grading_structure']
        profile.save(update_fields=['institution', 'program', 'year_level', 'grading_structure', 'updated_at'])
        return self.user, profile
