from django import forms
from .models import Letter, Message, Profile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from django import forms
from .models import Letter, LetterImage, Message, Profile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class LetterForm(forms.ModelForm):
    class Meta:
        model = Letter
        fields = ['letter_type', 'text_content', 'pdf']

    def __init__(self, *args, **kwargs):
        super(LetterForm, self).__init__(*args, **kwargs)
        self.fields['text_content'].widget = forms.Textarea(attrs={'rows': 4})
        self.fields['letter_type'].required = False  # optional when editing
        self.fields['pdf'].required = False           # optional on edit too

    def clean(self):
        cleaned_data = super().clean()

        # 🔥 Always fallback to the instance's letter_type if missing
        letter_type = cleaned_data.get('letter_type') or getattr(self.instance, 'letter_type', None)
        text_content = cleaned_data.get('text_content')
        pdf = cleaned_data.get('pdf')

        # 💡 Now validate reliably
        if letter_type == 'text' and not text_content:
            raise forms.ValidationError('You selected Text, but did not write anything.')

        if letter_type == 'pdf' and not pdf and not getattr(self.instance, 'pdf', None):
            raise forms.ValidationError('You selected PDF, but did not upload a file.')

        return cleaned_data

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 2}),
        }

class ProfileForm(forms.ModelForm):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Non-binary', 'Non-binary'),
        ('Trans', 'Trans'),
        ('Other', 'Other'),
        ('Prefer not to say', 'Prefer not to say'),
    ]

    PREFERRED_GENDER_CHOICES = [
        ('Any', 'Any'),
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Non-binary', 'Non-binary'),
        ('Trans', 'Trans'),
        ('Other', 'Other'),
    ]

    gender = forms.ChoiceField(choices=GENDER_CHOICES)
    preferred_gender = forms.ChoiceField(choices=PREFERRED_GENDER_CHOICES, required=False)

    class Meta:
        model = Profile
        fields = [
            'age',
            'gender',
            'profile_picture',
            'preferred_gender',
            'preferred_age_min',
            'preferred_age_max'
        ]
class LetterFilterForm(forms.Form):
    min_age = forms.IntegerField(required=False, label='Min Age')
    max_age = forms.IntegerField(required=False, label='Max Age')
    gender = forms.ChoiceField(
        required=False,
        choices=[('', 'Any'), ('Male', 'Male'), ('Female', 'Female')],
        label='Gender'
    )


class FullRegisterForm(UserCreationForm):
    name = forms.CharField(required=True, label="Name")
    email = forms.EmailField(required=True)
    age = forms.IntegerField(required=True)
    gender = forms.ChoiceField(
        choices=[
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Non-binary', 'Non-binary'),
            ('Trans', 'Trans'),
            ('Other', 'Other'),
            ('Prefer not to say', 'Prefer not to say'),
        ]
    )
    profile_picture = forms.ImageField(required=False)

    preferred_gender = forms.ChoiceField(
        choices=[
            ('Any', 'Any'),
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Non-binary', 'Non-binary'),
            ('Trans', 'Trans'),
            ('Other', 'Other'),
        ],
        required=False
    )

    preferred_age_min = forms.IntegerField(required=False, label="Preferred Minimum Age")
    preferred_age_max = forms.IntegerField(required=False, label="Preferred Maximum Age")

    # ✅ Optional letter fields
    letter_type = forms.ChoiceField(
        required=False,
        choices=[('text', 'Text'), ('image', 'Image'), ('pdf', 'PDF')],
        label="Letter Type (optional)"
    )
    text_content = forms.CharField(widget=forms.Textarea, required=False, label="Letter Text")
    pdf = forms.FileField(required=False)

    class Meta:
        model = User
        fields = [
            'name', 'email', 'password1', 'password2',
            'age', 'gender', 'profile_picture',
            'preferred_gender', 'preferred_age_min', 'preferred_age_max',
            'letter_type', 'text_content', 'pdf',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
class LetterImageForm(forms.ModelForm):
    class Meta:
        model = LetterImage
        fields = ['image']