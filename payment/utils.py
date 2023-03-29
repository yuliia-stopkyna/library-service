import stripe
from django.conf import settings
from rest_framework.request import Request
from rest_framework.reverse import reverse

from borrowing.models import Borrowing
from payment.models import Payment

stripe.api_key = settings.STRIPE_API_KEY


def create_payment(borrowing: Borrowing, session: stripe.checkout.Session) -> None:
    Payment.objects.create(
        status="Pending",
        type="Payment",
        borrowing=borrowing,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=session.amount_total / 100,
    )


def create_stripe_session(borrowing: Borrowing, request: Request) -> None:
    book = borrowing.book
    borrowing_period = (borrowing.expected_return_date - borrowing.borrow_date).days
    amount = int(book.daily_fee * borrowing_period * 100)
    success_url = reverse("payment:payment-success", request=request)

    session = stripe.checkout.Session.create(
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Borrowing of {book.title}",
                    },
                    "unit_amount": amount,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:4242/cancel",
    )
    create_payment(borrowing, session)
