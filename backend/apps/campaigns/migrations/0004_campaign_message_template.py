from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('messaging', '0003_remove_message_template_signature'),
        ('campaigns', '0003_campaignitem_alter_campaignrecipient_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='message_template',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='campaigns',
                to='messaging.messagetemplate',
                verbose_name='Template de Mensagem',
            ),
        ),
    ]
