from django.utils import timezone
from django_q.tasks import schedule


schedule(
    "borrowing.utils.daily_borrowings_overdue_notification",
    schedule_type="D",
    repeats=-1,
    next_run=timezone.now() + timezone.timedelta(minutes=1),
)
