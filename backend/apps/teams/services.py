from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from celery import shared_task
import logging

from ..models import TeamMember


User = get_user_model()
logger = logging.getLogger(__name__)


class TeamMemberService:
    """Serviço para gerenciamento de membros da equipe"""
    
    def create_member(self, data: dict, created_by: User) -> TeamMember:
        """Cria novo membro da equipe com credenciais WhatsApp"""
        try:
            # Extrair dados do usuário
            user_data = {
                'email': data['email'],
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'phone': data.get('phone', ''),
            }
            send_whatsapp = data.get('send_whatsapp_credentials', True)
            
            # Criar ou obter usuário
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults=user_data
            )
            
            # Se usuário novo, criar senha temporária
            temp_password = None
            if created:
                temp_password = User.objects.make_random_password(length=8)
                user.set_password(temp_password)
                user.save()
                logger.info(f"Novo usuário criado: {user.email}")
            
            # Criar TeamMember
            team_member = TeamMember.objects.create(
                user=user,
                role=data['role'],
                department=data.get('department', ''),
                notes=data.get('notes', ''),
                created_by=created_by
            )
            
            # Enviar credenciais por WhatsApp se solicitado
            if send_whatsapp and user.phone:
                self.send_credentials_via_whatsapp(
                    user=user,
                    temp_password=temp_password,
                    role=team_member.role
                )
            
            logger.info(f"Membro da equipe criado: {team_member}")
            return team_member
            
        except Exception as e:
            logger.error(f"Erro ao criar membro da equipe: {str(e)}")
            raise
    
    def send_credentials_via_whatsapp(self, user: User, temp_password: str = None, role: str = 'volunteer'):
        """Envia credenciais de acesso via WhatsApp"""
        try:
            from apps.campaigns.services import CampaignService
            from apps.messaging.tasks import send_message_task
            
            # Template para novo membro
            role_display = dict(TeamMember.ROLE_CHOICES).get(role, role.title())
            
            message = f"""🎉 Bem-vindo(a) à equipe, {user.first_name}!

📧 **Acesso ao Sistema:**
• Email: {user.email}
• Senha{' Temporária' if temp_password else ''}: {temp_password or 'Use sua senha atual'}

👤 **Seus Dados:**
• Função: {role_display}
• Status: Ativo

📱 **Próximos Passos:**
1️⃣ Acesse: http://localhost:5173/login
2️⃣ Use suas credenciais acima
3️⃣ Altere sua senha no primeiro acesso

🔗 **Acesso Rápido:** http://localhost:5173/login

⚠️ **Importante:** Altere sua senha após primeiro acesso!
Para ajuda, contate o administrador da equipe.

Equipe VoxPop 🚀"""
            
            # Obter primeira sessão WhatsApp ativa do tenant
            from apps.whatsapp.models import WhatsAppSession
            whatsapp_sessions = WhatsAppSession.objects.filter(status='connected', is_healthy=True)
            
            if whatsapp_sessions:
                # Enviar usando primeira sessão disponível
                send_message_task.delay(
                    phone=user.phone,
                    content=message.strip(),
                    session_id=whatsapp_sessions[0].id,
                    template_name='team_welcome'
                )
                logger.info(f"Credenciais enviadas via WhatsApp para {user.email}")
            else:
                logger.warning(f"Sem sessão WhatsApp disponível para enviar credenciais para {user.email}")
                # Enviar por email como fallback
                self._send_email_credentials(user, temp_password, role_display)
                
        except Exception as e:
            logger.error(f"Erro ao enviar credenciais WhatsApp para {user.email}: {str(e)}")
            raise
    
    def _send_email_credentials(self, user: User, temp_password: str, role_display: str):
        """Envia credenciais por email (fallback)"""
        try:
            subject = f"Bem-vindo à equipe VoxPop - {user.get_full_name()}"
            
            message = f"""Olá {user.first_name},

Seja bem-vindo(a) à equipe VoxPop!

Seus dados de acesso:
Email: {user.email}
Senha{' Temporária' if temp_password else ''}: {temp_password or 'Use sua senha atual'}
Função: {role_display}

Acesse o sistema em: http://localhost:5173/login

Importante: Altere sua senha após o primeiro acesso.

Atenciosamente,
Equipe VoxPop"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email='noreply@voxpop.com',
                recipient_list=[user.email],
                fail_silently=False
            )
            logger.info(f"Credenciais enviadas por email para {user.email}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar email de credenciais para {user.email}: {str(e)}")
            raise
    
    def bulk_update_roles(self, member_ids: list[int], new_role: str, updated_by: User):
        """Atualiza role de múltiplos membros"""
        try:
            updated_count = TeamMember.objects.filter(
                id__in=member_ids
            ).update(role=new_role)
            
            logger.info(f"{updated_count} membros atualizados para role {new_role} por {updated_by.email}")
            return updated_count
            
        except Exception as e:
            logger.error(f"Erro em atualização bulk de roles: {str(e)}")
            raise
    
    def get_team_statistics(self):
        """Retorna estatísticas da equipe"""
        from django.db.models import Count, Q
        
        stats = {}
        
        # Total por role
        role_stats = TeamMember.objects.filter(is_active=True).values('role').annotate(
            count=Count('id')
        )
        stats['by_role'] = {item['role']: item['count'] for item in role_stats}
        
        # Total por departamento
        dept_stats = TeamMember.objects.filter(is_active=True).exclude(
            department=''
        ).values('department').annotate(
            count=Count('id')
        )
        stats['by_department'] = {item['department']: item['count'] for item in dept_stats}
        
        # Totais gerais
        stats['total_active'] = TeamMember.objects.filter(is_active=True).count()
        stats['total_inactive'] = TeamMember.objects.filter(is_active=False).count()
        stats['total_members'] = TeamMember.objects.count()
        
        # Crescimento recentes (últimos 30 dias)
        from django.utils import timezone
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        stats['recent_members'] = TeamMember.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        return stats


@shared_task(bind=True, max_retries=3)
def send_welcome_message_task(user_id: int, temp_password: str = None):
    """Task assíncrona para enviar mensagem de boas-vindas"""
    try:
        user = User.objects.get(id=user_id)
        team_member = user.team_memberships.filter(is_active=True).first()
        
        if team_member and user.phone:
            service = TeamMemberService()
            service.send_credentials_via_whatsapp(
                user=user,
                temp_password=temp_password,
                role=team_member.role
            )
        else:
            logger.warning(f"Não foi possível enviar WhatsApp: usuário {user_id} sem telefone ou equipe")
            
    except Exception as exc:
        logger.error(f"Erro em send_welcome_message_task: {str(exc)}")
        raise send_welcome_message_task.retry(exc=exc, countdown=60)