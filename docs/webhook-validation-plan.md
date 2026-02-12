# Plano de Implementação: Validar Mensagens Recebidas via Webhooks

## Contexto e Problema

O sistema atual envia mensagens via WhatsApp (Evolution API), mas não valida se as mensagens foram realmente recebidas pelos destinatários. Para isso, precisamos:

1. **Configurar webhooks** na Evolution API para cada instância de WhatsApp
2. **Receber eventos** de mensagens recebidas/enviadas
3. **Validar** mensagens recebidas contra o registro de destinatários
4. **Rastrear** status de entrega e validação

## Visão Geral da Solução

```
Evolution API ──► Webhook (público) ──► Backend Django
                                                       │
                                                       ▼
                                                   └──► Database
```

## Arquitetura Proposta

### Componentes Principais

1. **WebhookController** (Novo)
   - Recebe webhooks da Evolution API
   - Valida autenticação (se implementado)
   - Verifica integridade do payload
   - Desoforta eventos para handlers específicos

2. **WebhookEventHandlers** (Novo)
   - `MessageReceivedHandler`: Processa `messages.upsert`
   - `MessageStatusHandler`: Processa `messages.update`
   - `ConnectionUpdateHandler`: Processa `connection.update`
   - Responsável por extrair e validar dados da mensagem

3. **MessageValidationService** (Novo)
   - Valida mensagens recebidas
   - Compara com registros de destinatários
   - Busca apoiadores (`Supporter`) por telefone
   - Valida:
     - Número de telefone registrado
     - Status do destinatário (apoiador, lead, blacklist)
     - Conteúdo da mensagem

4. **WebhookSecurityService** (Novo)
   - Gerencia segredos de webhooks
   - Valida assinaturas (HMAC-SHA256)
   - Verifica rate limiting
   - Protege contra ataques de replay

5. **MessageTracking** (Extensão ao modelo existente)
   - Adiciona campos ao `Message`: `validation_status`, `webhook_received_at`, `webhook_payload`
   - Adiciona campos ao `CampaignItem`: `delivery_status`, `webhook_received_at`
   - Adiciona campos ao `Supporter`: `last_message_from`, `last_message_at`, `validation_status`

6. **WebhookConfigurationService** (Novo)
   - Gerencia URLs de webhooks por instância
   - Sincroniza configurações com Evolution API
   - Gerencia secrets/tokens de webhook

## Fases de Implementação

### Fase 1: Fundamentos e Segurança (2-3 dias)

**Objetivos:**
- Autenticação de webhooks
- Segurança de secrets
- Infraestrura básica de validação

**Tarefas:**
1. ✅ Criar modelo `WebhookSecret` para armazenar secrets de webhook por instância
2. ✅ Criar `WebhookSecurityService` com métodos de validação
3. ✅ Adicionar campos de rastreamento ao `WebhookLog`
4. ✅ Modificar `WhatsAppSession` para incluir `webhook_secret`
5. ✅ Atualizar serializadores para incluir novos campos
6. ✅ Configurar variáveis de ambiente para segurança de webhook
7. ✅ Criar middleware de autenticação de webhook

**Arquivos a modificar/criar:**
- `backend/apps/whatsapp/models/webhook_log.py` - Adicionar campos de validação
- `backend/apps/whatsapp/models/session.py` - Adicionar webhook_secret
- `backend/apps/whatsapp/models/message.py` - Adicionar campos de validação
- `backend/apps/campaigns/models/campaign_item.py` - Adicionar campos de validação
- `backend/apps/supporters/models/supporter.py` - Adicionar campos de validação
- `backend/apps/whatsapp/api/serializers/webhook_serializers.py` - Criar serializadores para webhook
- `backend/apps/whatsapp/services/webhook_security_service.py` - Serviço de segurança
- `backend/apps/whatsapp/services/webhook_validation_service.py` - Serviço de validação
- `backend/apps/whatsapp/api/views/webhook_views.py` - Atualizar views
- `backend/apps/whatsapp/tasks/webhook_tasks.py` - Tasks de processamento
- `backend/core/middleware.py` - Middleware de autenticação
- `backend/config/settings/base.py` - Configurações de webhook

### Fase 2: Infraestrutura de Webhooks (3-4 dias)

**Objetivos:**
- Controlador centralizado de webhooks
- Sistema de roteamento para handlers específicos
- Processamento assíncrono de eventos

**Tarefas:**
1. ✅ Criar `WebhookController` para gerenciar webhooks recebidos
2. ✅ Criar classes `WebhookEventHandler` base para cada tipo de evento
3. ✅ Implementar handlers específicos:
   - `MessageReceivedHandler` - Processa `messages.upsert`
   - `MessageStatusHandler` - Processa `messages.update`
   - `ConnectionUpdateHandler` - Processa `connection.update`
4. ✅ Criar `WebhookEventProcessor` para orquestrar eventos
5. ✅ Criar `WebhookIncomingService` para receber requisições de webhook
6. ✅ Modificar views para usar novo sistema

**Arquivos a criar:**
- `backend/apps/whatsapp/controllers/webhook_controller.py` - Controlador principal
- `backend/apps/whatsapp/handlers/message_received_handler.py`
- `backend/apps/whatsapp/handlers/message_status_handler.py`
- `backend/apps/whatsapp/handlers/connection_update_handler.py`
- `backend/apps/whatsapp/processors/webhook_event_processor.py`
- `backend/apps/whatsapp/services/webhook_incoming_service.py`
- `backend/apps/whatsapp/api/views/webhook_public_views.py` - Views públicas

### Fase 3: Validação de Mensagens (4-5 dias)

**Objetivos:**
- Serviço robusto de validação
- Consulta a registros existentes
- Validação multi-campos (telefone, destinatário, conteúdo)
- Rastreamento de status de validação

**Tarefas:**
1. ✅ Criar `MessageValidationService`
2. ✅ Criar `SupporterRepository` para consultas otimizadas
3. ✅ Implementar validadores:
   - `PhoneValidator` - Valida formato e código de área
   - `SupporterStatusValidator` - Valida status do destinatário
   - `MessageContentValidator` - Valida conteúdo e variáveis
   - `AntiSpamValidator` - Detecta padrões suspeitos
4. ✅ Criar `WebhookValidationTask` para processamento assíncrono
5. ✅ Adicionar testes unitários para validadores
6. ✅ Implementar cache para consultas frequentes

**Arquivos a criar:**
- `backend/apps/whatsapp/validators/__init__.py`
- `backend/apps/whatsapp/validators/phone_validator.py`
- `backend/apps/whatsapp/validators/status_validator.py`
- `backend/apps/whatsapp/validators/content_validator.py`
- `backend/apps/whatsapp/validators/anti_spam_validator.py`
- `backend/apps/whatsapp/services/message_validation_service.py`
- `backend/apps/whatsapp/services/supporter_repository.py`
- `backend/apps/whatsapp/tasks/webhook_validation_tasks.py`

### Fase 4: Integração com Evolution API (3-4 dias)

**Objetivos:**
- Configuração automática de webhooks
- Sincronização com Evolution API
- Gerenciamento de instâncias

**Tarefas:**
1. ✅ Criar `EvolutionWebhookService`
2. ✅ Implementar `set_webhook()` para configurar webhooks
3. ✅ Implementar `create_instance()` com configuração de webhook
4. ✅ Modificar `whatsapp_service` para integrar com webhook service
5. ✅ Criar `EvolutionWebhookConfiguration` para gerenciar webhooks por instância
6. ✅ Criar comandos de gerenciamento:
   - Configurar webhook em todas as instâncias
   - Listar webhooks configurados
   - Testar webhooks
   - Reenviar webhook se necessário

**Arquivos a criar:**
- `backend/apps/whatsapp/services/evolution_webhook_service.py`
- `backend/apps/whatsapp/services/evolution_webhook_configuration.py`
- `backend/apps/whatsapp/api/views/webhook_management_views.py`
- `backend/apps/whatsapp/management/commands/set_webhook.py`
- `backend/apps/whatsapp/management/commands/test_webhook.py`
- `backend/apps/whatsapp/management/commands/list_webhooks.py`

### Fase 5: Dashboard e Relatórios (2-3 dias)

**Objetivos:**
- Visualizar status de validação
- Relatórios de mensagens validadas/rejeitadas
- Métricas de webhook (sucesso, falhas, tempo médio)

**Tarefas:**
1. ✅ Adicionar endpoints ao dashboard para métricas de validação
2. ✅ Criar `WebhookMetricsService` para cálculo de estatísticas
3. ✅ Criar `ValidationReport` para relatórios detalhados
4. ✅ Adicionar cards de status ao dashboard
5. ✅ Criar views para relatórios de validação
6. ✅ Implementar caching de métricas

**Arquivos a criar:**
- `backend/apps/dashboard/api/views/validation_views.py`
- `backend/apps/dashboard/api/serializers/validation_serializers.py`
- `backend/apps/dashboard/services/webhook_metrics_service.py`
- `backend/apps/dashboard/models/webhook_metrics.py`

### Fase 6: Frontend - Visualização de Validações (2-3 dias)

**Objetivos:**
- Interface para visualizar mensagens recebidas
- Filtros por status, data, destinatário
- Ações manuais de validação (aprovar, rejeitar)
- Dashboard com métricas em tempo real

**Tarefas:**
1. ✅ Criar página `/validation/messages` - Lista de mensagens recebidas
2. ✅ Criar página `/validation/reports` - Relatórios de validação
3. ✅ Criar serviço `validationService` no frontend
4. ✅ Criar componentes para visualizar status de validação
5. ✅ Implementar filtros e paginação
6. ✅ Adicionar notificações em tempo real

**Arquivos a criar:**
- `frontend/src/pages/validation/ValidationMessagesPage.tsx`
- `frontend/src/pages/validation/ValidationReportsPage.tsx`
- `frontend/src/services/validationService.ts`
- `frontend/src/components/validation/ValidationStatusBadge.tsx`
- `frontend/src/components/validation/ValidationFilters.tsx`

### Fase 7: Testes e Documentação (2-3 dias)

**Objetivos:**
- Testes unitários de validadores
- Testes de integração com Evolution API
- Testes de carga para webhooks
- Documentação completa do sistema

**Tarefas:**
1. ✅ Criar testes para validadores
2. ✅ Criar mocks da Evolution API
3. ✅ Criar testes de integração end-to-end
4. ✅ Criar testes de carga (load testing)
5. ✅ Documentar arquitetura e fluxos
6. ✅ Criar guias de configuração e uso

**Arquivos a criar:**
- `backend/apps/whatsapp/tests/test_validators.py`
- `backend/apps/whatsapp/tests/test_evolution_integration.py`
- `backend/apps/whatsapp/tests/test_webhook_controller.py`
- `backend/apps/whatsapp/tests/load_tests.py`
- `docs/webhook-system.md` - Documentação completa
- `docs/validation-guide.md` - Guia de uso
- `docs/webhook-configuration.md` - Guia de configuração

## Estrutura de Dados Proposta

### Novos Modelos

1. **WebhookSecret**
   ```python
   class WebhookSecret(SafeModel):
       instance = models.ForeignKey(WhatsAppSession, on_delete=models.CASCADE)
       secret_token = models.CharField(max_length=64)  # HMAC secret
       webhook_url = models.URLField(max_length=500)  # URL configurada
       is_active = models.BooleanField(default=True)
       created_at = models.DateTimeField(auto_now_add=True)
   ```

2. **Message** (campos adicionais)
   ```python
   # Adicionar a Message:
       validation_status = models.CharField(choices=[...])  # pending, validated, rejected, approved
       webhook_received_at = models.DateTimeField()
       webhook_payload = models.JSONField()
       delivery_attempts = models.IntegerField(default=0)
       last_validation_error = models.TextField(blank=True)
   ```

3. **ValidationLog**
   ```python
   class ValidationLog(SafeModel):
       message = models.ForeignKey(Message, on_delete=models.CASCADE)
       validation_type = models.CharField(choices=[...])  # phone, supporter, content, spam, duplicate
       result = models.CharField(choices=[...])  # valid, invalid, approved
       details = models.JSONField()
       validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
       created_at = models.DateTimeField(auto_now_add=True)
   ```

## Detalhes de Implementação

### Segurança de Webhooks

1. **Autenticação**
   - Cada instância tem um `webhook_secret` único
   - Secret compartilhado entre Evolution e Django via variável de ambiente
   - WebhookController valida assinatura HMAC-SHA256 do webhook

2. **Eventos Suportados**
   - `messages.upsert` - Nova mensagem recebida
   - `messages.update` - Status atualizado (delivered, read, failed)
   - `send.message` - Confirmação de envio

### Lógica de Validação

1. **Validação de Telefone**
   - Verifica formato brasileiro: +55 (11) 9XXXX-XXXX
   - Verifica se o número está cadastrado para o destinatário
   - Verifica DDD (se aplicável)
   - Normaliza para E.164 format

2. **Validação de Destinatário**
   - Busca apoiador por telefone
   - Verifica se apoiador está ativo
   - Verifica status (lead, apoiador, blacklist)
   - Valida contra blacklist

3. **Validação de Conteúdo**
   - Verifica palavras-chave suspeitas
   - Valida tamanho da mensagem
   - Verifica se contém links suspeitos
   - Valida variáveis usadas ({{name}}, etc.)

4. **Validação de Integridade**
   - Detecta mensagens duplicadas (possível ataque)
   - Valida timestamp (replay attack detection)
   - Verifica sequência de mensagens

## Cronograma de Implementação

- **Semana 1-2**: Fundamentos e Segurança
- **Semana 3-4**: Infraestrutura de Webhooks
- **Semana 4-5**: Validação de Mensagens
- **Semana 5-6**: Integração com Evolution API e Testes
- **Semana 6-7**: Frontend e Documentação
- **Semana 8**: Refinamentos e Otimizações

## Tecnologias e Dependências

### Novas Dependências
- `py-evolve` (validação de assinaturas)
- `redis` (cache de validação)
- `celery` (processamento assíncrono)

### Pontos de Atenção

1. **Performance**: Webhooks podem receber muitos eventos simultâneos - usar filas do Celery
2. **Segurança**: Webhooks são endpoints públicos - usar secrets fortes e rate limiting
3. **Commutação**: Sincronização entre webhook configuration e processamento
4. **Escalabilidade**: Sistema deve suportar múltiplas instâncias de WhatsApp
5. **Compatibilidade**: Garantir compatibilidade com Evolution API v2

## Testes e Validação

### Testes Unitários
- Validadores de telefone, status, conteúdo
- WebhookSecurityService
- WebhookController e handlers

### Testes de Integração
- Comunicação com Evolution API
- Configuração de webhooks
- Retentativas e fallbacks

### Testes de Carga
- Mil requisições por segundo
- Performance sob carga

## Próximos Passos

1. Revisar plano com equipe
2. Priorizar Fase 1 (Fundamentos e Segurança)
3. Criar migrações iniciais para novos modelos
4. Implementar código inicial
5. Testar com instância de desenvolvimento

## Verificação

Este plano aborda todos os aspectos solicitados:
- ✅ Configuração de webhooks na Evolution API
- ✅ Recepção e processamento de eventos
- ✅ Validação robusta de mensagens
- ✅ Segurança com autenticação e secrets
- ✅ Rastreamento e métricas
- ✅ Frontend para visualização
- ✅ Testes abrangentes

Aguardando aprovação para iniciar a implementação em fases sequenciais.
