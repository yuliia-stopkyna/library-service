import stripe
from django.conf import settings
from rest_framework.request import Request
from rest_framework.reverse import reverse

from borrowing.models import Borrowing
from payment.models import Payment

stripe.api_key = settings.STRIPE_API_KEY
FINE_MULTIPLIER = 2


def create_payment(
    borrowing: Borrowing, session: stripe.checkout.Session, payment_type: str
) -> None:
    Payment.objects.create(
        status="Pending",
        type=payment_type,
        borrowing=borrowing,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=session.amount_total / 100,
    )


def create_stripe_session(
    borrowing: Borrowing, request: Request, payment_type: str, overdue_days: int = None
) -> stripe.checkout.Session:
    book = borrowing.book
    if overdue_days is None:
        borrowing_period = (borrowing.expected_return_date - borrowing.borrow_date).days
        amount = int(book.daily_fee * borrowing_period * 100)
        product_name = f"Payment for borrowing of {book.title}"
    else:
        amount = int(book.daily_fee * overdue_days * 100) * FINE_MULTIPLIER
        product_name = f"Fine payment for {book.title}: {overdue_days} days overdue"
    success_url = reverse("payment:payment-success", request=request)
    cancel_url = reverse("payment:payment-cancel", request=request)

    session = stripe.checkout.Session.create(
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": product_name,
                    },
                    "unit_amount": amount,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url + "?session_id={CHECKOUT_SESSION_ID}",
    )
    create_payment(borrowing, session, payment_type)
    return session
