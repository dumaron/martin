import django_tables2 as tables
from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from core.models import Document, File


class MultipleFileInput(forms.ClearableFileInput):
	allow_multiple_selected = True


class MultipleFileField(forms.FileField):
	def __init__(self, *args, **kwargs):
		kwargs.setdefault("widget", MultipleFileInput())
		super().__init__(*args, **kwargs)

	def clean(self, data, initial=None):
		single_file_clean = super().clean
		if isinstance(data, (list, tuple)):
			result = [single_file_clean(d, initial) for d in data]
		else:
			result = single_file_clean(data, initial)
		return result


class DocumentForm(forms.ModelForm):
	files = MultipleFileField(
		required=False,
		help_text='Select one or more files to upload'
	)

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


class FileTable(tables.Table):
	id = tables.Column(verbose_name='ID')
	file = tables.Column(verbose_name='File Path')
	uploaded_at = tables.DateTimeColumn(verbose_name='Uploaded At', format='Y-m-d H:i')

	class Meta:
		model = File
		template_name = 'django_tables2/table.html'
		fields = ('id', 'file', 'uploaded_at')


class DocumentTable(tables.Table):
	id = tables.LinkColumn('document_detail', args=[tables.A('pk')], verbose_name='ID')
	name = tables.Column(verbose_name='Name')
	description = tables.Column(verbose_name='Description')
	location = tables.Column(verbose_name='Location')
	tags = tables.Column(empty_values=(), verbose_name='Tags', orderable=False)
	created_at = tables.DateTimeColumn(verbose_name='Created At', format='Y-m-d H:i')
	file_count = tables.Column(empty_values=(), verbose_name='Files')

	def render_tags(self, record):
		return ', '.join([tag.name for tag in record.tags.all()])

	class Meta:
		model = Document
		template_name = 'django_tables2/table.html'
		fields = ('id', 'name', 'description', 'location', 'tags', 'created_at', 'file_count')


@login_required
@require_GET
def document_detail(request, document_id):
	document = get_object_or_404(Document, pk=document_id)
	files = File.objects.filter(document=document).order_by('-uploaded_at')

	files_table = FileTable(files)
	tables.RequestConfig(request, paginate=False).configure(files_table)
	return render(
		request,
		'document_detail.html',
		{
			'document': document,
			'files': files,
			'files_table': files_table,
		},
	)


@login_required
@require_GET
def document_list(request):
	table = DocumentTable(
		Document.objects.annotate(file_count=Count('file')).order_by('-created_at')
	)
	tables.RequestConfig(request).configure(table)
	return render(request, 'document_list.html', {'table': table})


@login_required
@require_GET
def document_create_page(request):
	form = DocumentForm()
	return render(request, 'document_create.html', {'form': form})


@login_required
@require_POST
def document_create(request):
	form = DocumentForm(request.POST, request.FILES)
	if form.is_valid():
		document = form.save()

		# Handle multiple file uploads
		files = request.FILES.getlist('files')
		for uploaded_file in files:
			File.objects.create(file=uploaded_file, document=document)

		return redirect('document_detail', document_id=document.id)
	else:
		return render(request, 'document_create.html', {'form': form})
