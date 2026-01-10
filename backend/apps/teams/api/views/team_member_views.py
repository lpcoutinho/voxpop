from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from core.permissions import IsTenantMember, IsTenantAdmin, CanEditTenant
from core.pagination import StandardPagination

from apps.teams.models import TeamMember
from apps.teams.api.serializers.team_member_serializers import (
    TeamMemberListSerializer,
    TeamMemberDetailSerializer, 
    TeamMemberCreateSerializer,
    TeamMemberUpdateSerializer
)


class TeamMemberViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de membros da equipe"""
    
    queryset = TeamMember.objects.select_related('user', 'created_by')
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    filterset_fields = ['role', 'department', 'is_active']
    ordering_fields = ['user__first_name', 'user__last_name', 'role', 'created_at']
    ordering = ['user__first_name', 'user__last_name']
    
    def get_serializer_class(self):
        """Seleciona serializer baseado na ação"""
        if self.action == 'list':
            return TeamMemberListSerializer
        elif self.action == 'create':
            return TeamMemberCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TeamMemberUpdateSerializer
        return TeamMemberDetailSerializer
    
    def get_permissions(self):
        """Define permissões baseado na ação"""
        if self.action in ['create', 'destroy', 'bulk_activate', 'bulk_deactivate']:
            return [permissions.IsAuthenticated(), IsTenantAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [permissions.IsAuthenticated(), CanEditTenant()]
        return [permissions.IsAuthenticated(), IsTenantMember()]
    
    def get_queryset(self):
        """Filtra membros por tenant ativo"""
        return self.queryset.filter(is_active=True)
    
    def perform_create(self, serializer):
        """Define criador do membro"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Ativa membro da equipe"""
        team_member = self.get_object()
        team_member.is_active = True
        team_member.save()
        
        return Response({
            'message': 'Membro ativado com sucesso',
            'data': TeamMemberDetailSerializer(team_member).data
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Desativa membro da equipe"""
        team_member = self.get_object()
        team_member.is_active = False
        team_member.save()
        
        return Response({
            'message': 'Membro desativado com sucesso',
            'data': TeamMemberDetailSerializer(team_member).data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_activate(self, request):
        """Ativa múltiplos membros"""
        member_ids = request.data.get('member_ids', [])
        updated = TeamMember.objects.filter(
            id__in=member_ids,
            is_active=False
        ).update(is_active=True)
        
        return Response({
            'message': f'{updated} membros ativados com sucesso',
            'updated_count': updated
        })
    
    @action(detail=False, methods=['post'])
    def bulk_deactivate(self, request):
        """Desativa múltiplos membros"""
        member_ids = request.data.get('member_ids', [])
        updated = TeamMember.objects.filter(
            id__in=member_ids,
            is_active=True
        ).update(is_active=False)
        
        return Response({
            'message': f'{updated} membros desativados com sucesso',
            'updated_count': updated
        })
    
    @action(detail=True, methods=['post'])
    def send_credentials(self, request, pk=None):
        """Reenvia credenciais por WhatsApp"""
        team_member = self.get_object()
        
        try:
            from apps.teams.services import TeamMemberService
            service = TeamMemberService()
            service.send_credentials_via_whatsapp(
                user=team_member.user,
                role=team_member.role
            )
            
            return Response({
                'message': 'Credenciais enviadas com sucesso via WhatsApp',
                'phone': team_member.user.phone
            })
        except Exception as e:
            return Response({
                'error': True,
                'message': f'Erro ao enviar credenciais: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def role_summary(self, request):
        """Retorna resumo de membros por função"""
        from django.db.models import Count
        
        summary = TeamMember.objects.filter(is_active=True).values(
            'role'
        ).annotate(
            count=Count('id')
        ).order_by('role')
        
        return Response({
            'data': list(summary),
            'total': TeamMember.objects.filter(is_active=True).count()
        })
    
    @action(detail=False, methods=['get'])
    def department_summary(self, request):
        """Retorna resumo de membros por departamento"""
        from django.db.models import Count
        
        summary = TeamMember.objects.filter(is_active=True).values(
            'department'
        ).annotate(
            count=Count('id')
        ).exclude(department='').order_by('-count')
        
        return Response({
            'data': list(summary),
            'total': TeamMember.objects.filter(is_active=True).count()
        })