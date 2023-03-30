import stripe
from django.conf import settings

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


def create_stripe_session(borrowing: Borrowing) -> None:
    book = borrowing.book
    borrowing_period = (borrowing.expected_return_date - borrowing.borrow_date).days
    amount = int(book.daily_fee * borrowing_period * 100)
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
        success_url="http://localhost:4242/success",
        cancel_url="http://localhost:4242/cancel",
    )
    create_payment(borrowing, session)
