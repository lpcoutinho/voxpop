from django.db import migrations, models


def backfill_first_last_name(apps, schema_editor):
    Supporter = apps.get_model('supporters', 'Supporter')
    for supporter in Supporter.objects.all():
        if supporter.name:
            parts = supporter.name.strip().split(maxsplit=1)
            supporter.first_name = parts[0]
            supporter.last_name = parts[1] if len(parts) > 1 else ''
            supporter.save(update_fields=['first_name', 'last_name'])


class Migration(migrations.Migration):

    dependencies = [
        ('supporters', '0003_create_system_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='supporter',
            name='first_name',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Nome',
            ),
        ),
        migrations.AddField(
            model_name='supporter',
            name='last_name',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Sobrenome',
            ),
        ),
        migrations.RunPython(
            backfill_first_last_name,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
