from django import forms
from record import models


# Upload files
class UploadFormFile(forms.ModelForm):
    class Meta:
        model = models.Upload
        fields = ('title', 'file')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control form-control-user'})
        self.fields['file'].widget.attrs.update({'class': 'form-control form-control-user'})
