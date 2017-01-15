from django import forms


class UploadFileForm(forms.Form):
    # title = forms.CharField(max_length=50)
    image = forms.ImageField()

class ImageUploadForm(forms.Form):
    """Image upload form."""
    title = forms.CharField(max_length=50)
    image = forms.ImageField()
    description = forms.CharField(widget=forms.Textarea)