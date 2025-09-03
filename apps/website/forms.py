from django import forms

from core.models import BankFileImport, Inbox, Project, Task, YnabCategory


class BankFileImportForm(forms.ModelForm):
	class Meta:
		model = BankFileImport
		fields = ['bank_file', 'file_type']


class YnabTransactionCreationForm(forms.Form):
	memo = forms.CharField()
	bank_transaction_id = forms.IntegerField(widget=forms.HiddenInput)
	ynab_category = forms.ModelChoiceField(
		queryset=YnabCategory.objects.none(), widget=forms.Select(attrs={'class': 'tom-select'})
	)

	def __init__(self, *args, budget_id, **kwargs):
		super().__init__(*args, **kwargs)

		# update the category field now that we have the budget_id available
		filtered_queryset = YnabCategory.objects.filter(budget_id=budget_id, hidden=False)
		self.fields['ynab_category'].queryset = filtered_queryset


# GTD Forms

class ProjectForm(forms.ModelForm):
	class Meta:
		model = Project
		fields = ['title', 'description']
		widgets = {
			'title': forms.TextInput(attrs={'placeholder': 'Enter project title'}),
			'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional project description'}),
		}


class ProjectStatusForm(forms.Form):
	status = forms.ChoiceField(
		choices=[('', 'Choose status...')] + Project.STATUS_CHOICES,
		widget=forms.Select(attrs={'class': 'tom-select'})
	)


class TaskForm(forms.ModelForm):
	class Meta:
		model = Task
		fields = ['description']
		widgets = {
			'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional task description'}),
		}


class InboxForm(forms.ModelForm):
	class Meta:
		model = Inbox
		fields = ['content']
		widgets = {
			'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What\'s on your mind? Ideas, tasks, thoughts...'}),
		}


class InboxProcessingForm(forms.Form):
	ACTION_CHOICES = [
		('create_project', 'Create New Project'),
		('create_task', 'Add Task to Project'),
		('mark_done', 'Mark as Processed'),
	]
	
	action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.RadioSelect)
	
	# Project creation fields
	project_title = forms.CharField(
		required=False,
		widget=forms.TextInput(attrs={'placeholder': 'Enter project title'})
	)
	project_description = forms.CharField(
		required=False,
		widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional project description'})
	)
	
	# Task creation fields
	project_id = forms.ModelChoiceField(
		queryset=Project.objects.filter(status='active'),
		required=False,
		empty_label="Choose a project...",
		widget=forms.Select(attrs={'class': 'tom-select'})
	)
	task_title = forms.CharField(
		required=False,
		widget=forms.TextInput(attrs={'placeholder': 'Enter task title'})
	)
	task_description = forms.CharField(
		required=False,
		widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional task description'})
	)
