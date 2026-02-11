from django import forms
from django.shortcuts import redirect, render

from apps.website.pages.page import Page
from core.models import Document, File


class MultipleFileInput(forms.ClearableFileInput):
	allow_multiple_selected = True


class MultipleFileField(forms.FileField):
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('widget', MultipleFileInput())
		super().__init__(*args, **kwargs)

	def clean(self, data, initial=None):
		single_file_clean = super().clean
		if isinstance(data, (list, tuple)):
			result = [single_file_clean(d, initial) for d in data]
		else:
			result = single_file_clean(data, initial)
		return result


class DocumentForm(forms.ModelForm):
	files = MultipleFileField(required=False, help_text='Select one or more files to upload')

	class Meta:
		model = Document
		fields = ['name', 'description', 'location', 'tags']
		widgets = {
			'name': forms.TextInput(attrs={'placeholder': 'Document name'}),
			'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional description'}),
			'location': forms.TextInput(attrs={'placeholder': 'Optional physical location'}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['tags'].required = False


page = Page(name='document_create_page', base_route='models/document')


@page.main('create')
def main_render(request):
	form = DocumentForm()
	return render(request, 'document_create/document_create.html', {'form': form})


@page.action('create-action')
def create_document(request):
	form = DocumentForm(request.POST, request.FILES)
	if form.is_valid():
		document = form.save()

		# Handle multiple file uploads
		files = request.FILES.getlist('files')
		for uploaded_file in files:
			File.objects.create(file=uploaded_file, document=document)

		return redirect('document_detail_page.main_render', document_id=document.id)
	else:
		return render(request, 'document_create/document_create.html', {'form': form})
