from datetime import datetime

from django.contrib import admin

from core.models import (
	BankAccount,
	BankFileImport,
	BankTransaction,
	Event,
	Inbox,
	Memory,
	TimeBox,
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
	list_display = ['name', 'date', 'amount', 'snoozed_on', 'paired_on', 'file_type']
	search_fields = ['name', 'amount']
	list_filter = [
		'file_import__file_type',
		('snoozed_on', admin.EmptyFieldListFilter),
		('paired_on', admin.EmptyFieldListFilter),
	]
	actions = [snooze]

	def file_type(self, obj):
		return obj.file_import.file_type

	def imported_on(self, obj):
		return obj.file_import.import_date


class YnabTransactionAdmin(admin.ModelAdmin):
	list_display = ['date', 'amount', 'budget', 'memo', 'cleared', 'deleted']
	list_filter = ['date', 'cleared', 'deleted', 'budget']
	search_fields = ['memo']


class YnabImportAdmin(admin.ModelAdmin):
	list_display = ['budget', 'execution_datetime', 'server_knowledge']
	list_filter = ['budget']


class BankFileImportAdmin(admin.ModelAdmin):
	list_display = ['id', 'file_name', 'file_type', 'import_date']


class YnabAccountAdmin(admin.ModelAdmin):
	list_display = ['name', 'id', 'budget']
	list_filter = ['budget']


class BankAccountAdmin(admin.ModelAdmin):
	list_display = ['name', 'iban']


class MemoryAdmin(admin.ModelAdmin):
	list_display = ['id', 'date', 'description']
	search_fields = ['description']
	list_filter = ['date']


class TimeBoxAdmin(admin.ModelAdmin):
	list_display = ['id', 'started_on', 'ended_on', 'duration_display', 'max_duration_minutes', 'status_display', 'has_been_interrupted']
	list_filter = [
		('ended_on', admin.EmptyFieldListFilter),
		'has_been_interrupted',
		'started_on',
		'max_duration_minutes',
	]
	search_fields = []
	readonly_fields = ['duration_display', 'status_display', 'elapsed_time']
	ordering = ['-started_on']
	
	def get_readonly_fields(self, request, obj=None):
		"""Show readonly fields only in change form, not add form."""
		if obj:  # Editing existing object
			return self.readonly_fields
		else:  # Adding new object
			return []
	
	def duration_display(self, obj):
		"""Display the actual duration of the time box."""
		if obj.ended_on:
			duration = obj.ended_on - obj.started_on
			minutes = int(duration.total_seconds() // 60)
			seconds = int(duration.total_seconds() % 60)
			return f"{minutes}m {seconds}s"
		else:
			from django.utils import timezone
			duration = timezone.now() - obj.started_on
			minutes = int(duration.total_seconds() // 60)
			seconds = int(duration.total_seconds() % 60)
			return f"{minutes}m {seconds}s (ongoing)"
	duration_display.short_description = "Actual Duration"
	
	def status_display(self, obj):
		"""Display the status of the time box."""
		if not obj.ended_on:
			return "🟢 Active"
		elif obj.has_been_interrupted:
			return "🟡 Interrupted"
		else:
			# Check if it completed the full duration
			from django.utils import timezone
			duration = obj.ended_on - obj.started_on
			max_duration_seconds = obj.max_duration_minutes * 60
			if duration.total_seconds() >= max_duration_seconds - 5:  # Allow 5 second tolerance
				return "✅ Completed"
			else:
				return "🟡 Ended Early"
	status_display.short_description = "Status"
	
	def elapsed_time(self, obj):
		"""Show elapsed time for read-only display."""
		from django.utils import timezone
		if obj.ended_on:
			elapsed = obj.ended_on - obj.started_on
		else:
			elapsed = timezone.now() - obj.started_on
		
		total_seconds = int(elapsed.total_seconds())
		hours = total_seconds // 3600
		minutes = (total_seconds % 3600) // 60
		seconds = total_seconds % 60
		
		if hours > 0:
			return f"{hours}h {minutes}m {seconds}s"
		else:
			return f"{minutes}m {seconds}s"
	elapsed_time.short_description = "Elapsed Time"


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
admin.site.register(TimeBox, TimeBoxAdmin)
