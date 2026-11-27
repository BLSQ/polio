from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("polio", "0259_add_ipv_doses_per_vial_config"),
    ]

    operations = [
        migrations.AlterField(
            model_name="countryplan",
            name="vaccine",
            field=models.CharField(
                choices=[
                    ("mOPV2", "mOPV2"),
                    ("nOPV2", "nOPV2"),
                    ("bOPV", "bOPV"),
                    ("nOPV2 & bOPV", "nOPV2 & bOPV"),
                    ("IPV", "IPV"),
                    ("fIPV", "fIPV"),
                    ("IPV & bOPV", "IPV & bOPV"),
                    ("fIPV & bOPV", "fIPV & bOPV"),
                    ("IPV & nOPV2", "IPV & nOPV2"),
                    ("fIPV & nOPV2", "fIPV & nOPV2"),
                    ("IPV & nOPV2 & bOPV", "IPV & nOPV2 & bOPV"),
                    ("fIPV & nOPV2 & bOPV", "fIPV & nOPV2 & bOPV"),
                ],
                max_length=30,
            ),
        ),
    ]
