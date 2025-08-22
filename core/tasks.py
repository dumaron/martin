from datetime import timedelta

from django.apps import apps
from django_tasks import task


@task()
def complete_time_box(time_box_id: int):
	"""Auto-complete a TimeBox when its duration expires.
	
	Args:
		time_box_id: The ID of the TimeBox to complete
		
	Returns:
		str: Status message about the completion
	"""

	# I need to import the Timebox model this way because since I also import these tasks in the model definition,
	# we would get a circular import.
	TimeBox = apps.get_model('core', 'TimeBox')

	try:
		time_box = TimeBox.objects.get(id=time_box_id, ended_on__isnull=True)

		# If it is already marked as ended, it has probably been interrupted. Given that I cannot a task from django-tasks
		# (at least I think), I will simply ignore it.
		if time_box.ended_on is not None:
			return f"TimeBox {time_box_id} already marked as interrupted"

		
		# Set ended_on to the exact expected completion time, not current time
		# This ensures consistency regardless of when the task actually runs
		expected_end_time = time_box.started_on + timedelta(minutes=time_box.max_duration_minutes)
		
		time_box.ended_on = expected_end_time
		time_box.has_been_interrupted = False
		time_box.save()
		
		return f"TimeBox {time_box_id} auto-completed successfully at {expected_end_time}"
		
	except TimeBox.DoesNotExist:
		return f"TimeBox {time_box_id} not found or already completed"
	except Exception as e:
		return f"Error completing TimeBox {time_box_id}: {str(e)}"
