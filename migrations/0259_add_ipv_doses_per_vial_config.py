from django.db import migrations


CONFIG_SLUG = "vaccine_doses_per_vial"
VACCINE = "IPV"
PRESENTATIONS = [1, 5]


def add_ipv_presentations(apps, schema_editor):
    Config = apps.get_model("iaso", "Config")

    for config in Config.objects.filter(slug=CONFIG_SLUG):
        content = config.content or {}
        if VACCINE in content:
            continue
        content[VACCINE] = list(PRESENTATIONS)
        config.content = content
        config.save()


class Migration(migrations.Migration):
    dependencies = [
        ("iaso", "0261_config"),
        ("polio", "0258_alter_campaignscope_vaccine_and_more"),
    ]

    operations = [
        migrations.RunPython(add_ipv_presentations, migrations.RunPython.noop),
    ]
