from django.db.models import Q, QuerySet
from django.utils import timezone

from borrowing.models import Borrowing
from borrowing.notifications import send_telegram_notification


def get_borrowing_info(borrowing: Borrowing) -> str:
    return (
        f"id: {borrowing.id}\n"
        f"Borrow date: {borrowing.borrow_date}\n"
        f"Expected return date: {borrowing.expected_return_date}\n"
        f"Book: {borrowing.book.title}\n"
        f"User full name: {borrowing.user.get_full_name()}\n"
        f"User id: {borrowing.user.id}"
    )


def check_overdue_borrowings() -> QuerySet:
    queryset = Borrowing.objects.select_related("book", "user").filter(
        Q(actual_return_date__isnull=True)
        & Q(
            expected_return_date__lte=timezone.now().date() + timezone.timedelta(days=1)
        )
    )

    return queryset


def borrowings_overdue_send_message(queryset) -> None:
    if not queryset:
        return send_telegram_notification("No borrowings overdue today!")

    for borrowing in queryset:
        send_telegram_notification(
            "Borrowing overdue:\n" + get_borrowing_info(borrowing)
        )


def daily_borrowings_overdue_notification() -> None:
    borrowings_overdue_send_message(check_overdue_borrowings())
