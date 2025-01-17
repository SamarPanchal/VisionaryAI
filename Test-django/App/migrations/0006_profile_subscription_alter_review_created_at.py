# Generated by Django 5.1.2 on 2024-11-05 13:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("App", "0005_profile_razorpay_order_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="subscription",
            field=models.TextField(default="free", max_length=10),
        ),
        migrations.AlterField(
            model_name="review",
            name="created_at",
            field=models.DateTimeField(default="2024-11-05 13:24:31"),
        ),
    ]
