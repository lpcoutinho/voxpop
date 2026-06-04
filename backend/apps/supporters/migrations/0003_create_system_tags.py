from django.db import migrations

SYSTEM_TAGS = {
    'lead': {
        'name': 'Lead',
        'color': '#3B82F6',
        'description': 'Contato inicial - ainda nao e apoiador',
        'slug': 'lead',
    },
    'apoiador': {
        'name': 'Apoiador',
        'color': '#22C55E',
        'description': 'Contato engajado - apoiador confirmado',
        'slug': 'apoiador',
    },
    'blacklist': {
        'name': 'Blacklist',
        'color': '#EF4444',
        'description': 'Nao contatar - excluido de campanhas',
        'slug': 'blacklist',
    },
}


def create_system_tags(apps, schema_editor):
    Tag = apps.get_model('supporters', 'Tag')
    for slug, data in SYSTEM_TAGS.items():
        Tag.objects.get_or_create(
            slug=slug,
            defaults={
                'name': data['name'],
                'color': data['color'],
                'description': data['description'],
                'is_system': True,
            }
        )


def reverse_system_tags(apps, schema_editor):
    Tag = apps.get_model('supporters', 'Tag')
    Tag.objects.filter(slug__in=SYSTEM_TAGS.keys(), is_system=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('supporters', '0002_add_system_tags_fields'),
    ]

    operations = [
        migrations.RunPython(create_system_tags, reverse_system_tags),
    ]
