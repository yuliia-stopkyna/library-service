# Generated by Django 4.1.7 on 2023-03-28 18:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("borrowing", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("Pending", "Pending"), ("Paid", "Paid")],
                        max_length=10,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[("Payment", "Payment"), ("Fine", "Fine")],
                        max_length=10,
                    ),
                ),
                ("session_url", models.URLField()),
                ("session_id", models.CharField(max_length=150)),
                ("money_to_pay", models.DecimalField(decimal_places=2, max_digits=8)),
                (
                    "borrowing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="borrowing.borrowing",
                    ),
                ),
            ],
        ),
    ]