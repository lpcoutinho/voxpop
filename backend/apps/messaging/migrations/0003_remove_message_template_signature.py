from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('messaging', '0002_message_template_signature'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='messagetemplate',
            name='signature',
        ),
    ]
