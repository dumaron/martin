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
		widget=forms.Select(attrs={'class': 'tom-select'}),
	)


class TaskForm(forms.ModelForm):
	class Meta:
		model = Task
		fields = ['description', 'project']
		widgets = {
			'description': forms.TextInput(attrs={'placeholder': 'Enter task description'}),
			'project': forms.Select(attrs={'class': 'tom-select'}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['project'].empty_label = 'No project (standalone task)'
		self.fields['project'].required = False


class InboxForm(forms.ModelForm):
	class Meta:
		model = Inbox
		fields = ['content']
		widgets = {'content': forms.Textarea(attrs={'rows': 4, 'placeholder': ''})}
