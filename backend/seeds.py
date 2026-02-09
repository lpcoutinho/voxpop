#!/usr/bin/env python
"""
Semente (Seeds) para popular o banco de dados do VoxPop.
Executar: python manage.py shell < seeds.py
Ou: docker exec voxpop_backend python manage.py shell < seeds.py
"""

import django
django.setup()

from django.db import transaction
from apps.tenants.models import Plan


def seed_plans():
    """Popula a tabela de planos."""

    plans_data = [
        {
            'name': 'Básico',
            'slug': 'basico',
            'description': 'Plano básico para pequenas campanhas',
            'max_supporters': 1000,
            'max_messages_month': 5000,
            'max_campaigns': 10,
            'max_whatsapp_sessions': 1,
            'price': 99.90,
            'features': {
                'support': 'email',
                'analytics': 'basic',
                'export': 'csv'
            },
            'is_active': True,
            'is_public': True,
        },
        {
            'name': 'Profissional',
            'slug': 'profissional',
            'description': 'Plano profissional para campanhas médias',
            'max_supporters': 10000,
            'max_messages_month': 50000,
            'max_campaigns': 50,
            'max_whatsapp_sessions': 3,
            'price': 299.90,
            'features': {
                'support': 'priority',
                'analytics': 'advanced',
                'export': 'csv,xlsx',
                'api_access': True
            },
            'is_active': True,
            'is_public': True,
        },
        {
            'name': 'Enterprise',
            'slug': 'enterprise',
            'description': 'Plano enterprise para grandes campanhas',
            'max_supporters': 100000,
            'max_messages_month': 500000,
            'max_campaigns': 200,
            'max_whatsapp_sessions': 10,
            'price': 999.90,
            'features': {
                'support': '24/7',
                'analytics': 'custom',
                'export': 'all',
                'api_access': True,
                'dedicated_server': True,
                'sla': '99.9'
            },
            'is_active': True,
            'is_public': True,
        },
    ]

    created_count = 0
    updated_count = 0

    for plan_data in plans_data:
        plan, created = Plan.objects.update_or_create(
            slug=plan_data['slug'],
            defaults=plan_data
        )
        if created:
            print(f"✓ Plano criado: {plan.name} (R$ {plan.price}/mês)")
            created_count += 1
        else:
            print(f"⊘ Plano já existe: {plan.name} - atualizado")
            updated_count += 1

    print(f"\nTotal: {created_count} novos, {updated_count} atualizados")
    return Plan.objects.count()


@transaction.atomic
def run_seeds():
    """Executa todos os seeds."""
    print("=" * 50)
    print("VoxPop - Populando banco de dados")
    print("=" * 50)
    print()

    # Limpar console
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

    print("📱 Criando planos...")
    total_plans = seed_plans()

    print()
    print("=" * 50)
    print(f"✓ Seeds concluídos! {total_plans} planos disponíveis")
    print("=" * 50)

    print("\nPlanos disponíveis:")
    for plan in Plan.objects.all().order_by('price'):
        print(f"  [{plan.id}] {plan.name} - R$ {plan.price}/mês")
        print(f"      - {plan.max_supporters} apoiadores")
        print(f"      - {plan.max_messages_month} mensagens/mês")
        print(f"      - {plan.max_campaigns} campanhas")
        print(f"      - {plan.max_whatsapp_sessions} sessões WhatsApp")


if __name__ == '__main__':
    run_seeds()
