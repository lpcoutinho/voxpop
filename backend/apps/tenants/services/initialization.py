"""
Service para inicialização de dados padrão de novos tenants.
"""
import logging

from django_tenants.utils import schema_context

logger = logging.getLogger(__name__)


def create_default_segments(created_by=None):
    """
    Cria segmentos padrão para o tenant.

    Args:
        created_by: Usuário que será registrado como criador dos segmentos
    """
    from apps.supporters.models import Segment

    segments = [
        {
            'name': 'Todos os Contatos',
            'description': 'Todos os contatos cadastrados',
            'filters': {},
        },
        {
            'name': 'Leads',
            'description': 'Contatos iniciais - ainda não são apoiadores',
            'filters': {'tags': ['lead']},
        },
        {
            'name': 'Apoiadores Ativos',
            'description': 'Contatos engajados - apoiadores confirmados',
            'filters': {'tags': ['apoiador']},
        },
    ]

    created_segments = []
    for seg_data in segments:
        segment, created = Segment.objects.get_or_create(
            name=seg_data['name'],
            defaults={
                'description': seg_data['description'],
                'filters': seg_data['filters'],
                'created_by': created_by,
            }
        )
        if created:
            created_segments.append(segment)
            logger.info(f"Created default segment: {segment.name}")

    return created_segments


def create_default_templates(created_by=None):
    """
    Cria templates padrão para o tenant.

    Args:
        created_by: Usuário que será registrado como criador dos templates
    """
    from apps.messaging.models import MessageTemplate

    template, created = MessageTemplate.objects.get_or_create(
        name='Boas-vindas',
        defaults={
            'description': 'Mensagem de boas-vindas para novos contatos',
            'message_type': 'text',
            'content': 'Olá {{name}}! Seja bem-vindo(a) à nossa campanha. Estamos felizes em ter você conosco!',
            'variables': ['name'],
            'is_active': True,
            'created_by': created_by,
        }
    )

    if created:
        logger.info(f"Created default template: {template.name}")
        return [template]

    return []


def initialize_tenant_data(tenant, admin_user=None):
    """
    Inicializa todos os dados padrão do tenant.

    Esta função deve ser chamada após a criação de um novo tenant para
    configurar os dados iniciais necessários.

    Args:
        tenant: Instância do Client (tenant) recém-criado
        admin_user: Usuário admin do tenant (opcional, usado como created_by)
    """
    if tenant.schema_name == 'public':
        logger.debug("Skipping initialization for public schema")
        return

    logger.info(f"Initializing default data for tenant: {tenant.name} ({tenant.schema_name})")

    with schema_context(tenant.schema_name):
        # 1. Criar tags de sistema
        from apps.supporters.models import Tag
        created_tags = Tag.create_system_tags()
        if created_tags:
            logger.info(f"Created {len(created_tags)} system tags")

        # 2. Criar segmentos padrão
        created_segments = create_default_segments(created_by=admin_user)
        if created_segments:
            logger.info(f"Created {len(created_segments)} default segments")

        # 3. Criar template padrão
        created_templates = create_default_templates(created_by=admin_user)
        if created_templates:
            logger.info(f"Created {len(created_templates)} default templates")

    logger.info(f"Tenant initialization completed for: {tenant.name}")
