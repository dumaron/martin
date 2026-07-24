from datetime import datetime

from django.contrib import admin

from core.models import (
	BankAccount,
	BankFileImport,
	BankTransaction,
	DailySuggestion,
	Document,
	Event,
	File,
	Flashcard,
	FlashcardReview,
	Inbox,
	Memory,
	Project,
	RecurrenceRule,
	RecurringSuggestion,
	Task,
	YnabAccount,
	YnabBudget,
	YnabCategory,
	YnabImport,
	YnabTransaction,
)


@admin.action(description='Snooze')
def snooze(modeladmin, request, queryset):
	queryset.update(snoozed_on=datetime.now())


class BankTransactionAdmin(admin.ModelAdmin):
	list_display = ['name', 'date', 'amount', 'snoozed_on', 'paired_on']
	search_fields = ['name', 'amount']
	list_filter = [
		('snoozed_on', admin.EmptyFieldListFilter),
		('paired_on', admin.EmptyFieldListFilter),
	]
	actions = [snooze]


class RecurrenceRuleInline(admin.TabularInline):
	model = RecurrenceRule
	extra = 1
	fields = ['type', 'day']


class RecurrenceRuleAdmin(admin.ModelAdmin):
	list_display = ['type', 'day', 'suggestion']
	list_filter = ['type', 'day', 'suggestion']


class RecurringSuggestionAdmin(admin.ModelAdmin):
	inlines = [RecurrenceRuleInline]
	list_display = ['content', 'created_at']
	search_fields = ['content']


class YnabTransactionAdmin(admin.ModelAdmin):
	list_display = ['date', 'amount', 'budget', 'memo', 'cleared', 'deleted']
	list_filter = ['date', 'cleared', 'deleted', 'budget']
	search_fields = ['memo']


class YnabImportAdmin(admin.ModelAdmin):
	list_display = ['budget', 'execution_datetime', 'server_knowledge']
	list_filter = ['budget']


class BankFileImportAdmin(admin.ModelAdmin):
	list_display = ['id', 'file_type', 'import_date']


class YnabAccountAdmin(admin.ModelAdmin):
	list_display = ['name', 'id', 'budget']
	list_filter = ['budget']


class BankAccountAdmin(admin.ModelAdmin):
	list_display = ['name', 'iban']


class MemoryAdmin(admin.ModelAdmin):
	list_display = ['id', 'date', 'description']
	search_fields = ['description']
	list_filter = ['date']


admin.site.register(Event)
admin.site.register(Inbox)
admin.site.register(BankFileImport, BankFileImportAdmin)
admin.site.register(BankTransaction, BankTransactionAdmin)
admin.site.register(YnabImport, YnabImportAdmin)
admin.site.register(YnabTransaction, YnabTransactionAdmin)
admin.site.register(YnabCategory)
admin.site.register(YnabBudget)
admin.site.register(YnabAccount, YnabAccountAdmin)
admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(Memory, MemoryAdmin)
admin.site.register(RecurringSuggestion, RecurringSuggestionAdmin)
admin.site.register(RecurrenceRule, RecurrenceRuleAdmin)


class ProjectAdmin(admin.ModelAdmin):
	list_display = ('title', 'parent', 'status', 'created_at')
	list_filter = ('status', 'parent')
	search_fields = ('title',)


admin.site.register(Project, ProjectAdmin)
admin.site.register(Document)
admin.site.register(File)
admin.site.register(DailySuggestion)
admin.site.register(Task)


class FlashcardAdmin(admin.ModelAdmin):
	list_display = ['id', 'question', 'state', 'due', 'last_review']
	search_fields = ['question', 'answer']
	list_filter = ['state']


class FlashcardReviewAdmin(admin.ModelAdmin):
	list_display = ['flashcard', 'rating', 'reviewed_at']
	list_filter = ['rating']


admin.site.register(Flashcard, FlashcardAdmin)
admin.site.register(FlashcardReview, FlashcardReviewAdmin)
