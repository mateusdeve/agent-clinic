# Requirements: MedIA

**Defined:** 2026-03-29
**Core Value:** O paciente consegue agendar, remarcar e tirar duvidas pelo WhatsApp 24h sem intervencao humana, e a equipe da clinica tem visibilidade total das conversas e agendamentos em tempo real.

## v1 Requirements

### Landing Page

- [x] **LAND-01**: Visitante ve hero section com proposta de valor e CTA que redireciona para WhatsApp
- [x] **LAND-02**: Visitante ve secoes de features, como funciona e depoimento (baseado no site.html)
- [x] **LAND-03**: Landing page e responsiva e funcional em dispositivos moveis
- [x] **LAND-04**: Landing page segue identidade visual do site.html (paleta verde, DM Serif/DM Sans)

### Authentication

- [x] **AUTH-01**: Usuario pode fazer login com email e senha
- [x] **AUTH-02**: Usuario pode fazer logout de qualquer pagina
- [x] **AUTH-03**: Sessao do usuario persiste entre recarregamentos do browser (JWT + refresh token)
- [x] **AUTH-04**: Sistema suporta tres roles: Admin, Recepcionista, Medico
- [x] **AUTH-05**: Rotas protegidas redirecionam usuario nao autenticado para login
- [x] **AUTH-06**: Funcionalidades sao restritas por role (RBAC)

### Multi-Tenancy

- [x] **TENANT-01**: Cada clinica tem dados completamente isolados (tenant_id em todas as tabelas)
- [x] **TENANT-02**: Nenhum endpoint retorna dados de outra clinica
- [x] **TENANT-03**: tenant_id e extraido do JWT automaticamente, nunca passado como parametro

### Dashboard

- [x] **DASH-01**: Admin/Recepcionista ve KPIs: consultas hoje, taxa de ocupacao, no-shows, confirmacoes pendentes
- [x] **DASH-02**: Admin/Recepcionista ve lista das proximas consultas do dia
- [x] **DASH-03**: Admin/Recepcionista ve contador de conversas WhatsApp ativas
- [x] **DASH-04**: Admin ve graficos de tendencias semanais, funil de conversao e receita por especialidade

### Appointment Management (Agenda)

- [x] **AGENDA-01**: Recepcionista ve calendario visual (dia/semana/mes) com filtro por medico
- [x] **AGENDA-02**: Recepcionista pode criar agendamento manualmente (paciente, medico, data, hora, especialidade)
- [x] **AGENDA-03**: Recepcionista pode editar/remarcar agendamento existente
- [x] **AGENDA-04**: Recepcionista pode cancelar agendamento com motivo opcional
- [x] **AGENDA-05**: Agendamentos tem status tracking: Agendado > Confirmado > Realizado > Cancelado
- [x] **AGENDA-06**: Admin pode bloquear horarios (ferias, almoco, indisponibilidade)
- [x] **AGENDA-07**: Medico ve apenas sua propria agenda

### Patient Management

- [x] **PAT-01**: Recepcionista ve lista de pacientes com busca por nome/telefone
- [x] **PAT-02**: Recepcionista pode criar paciente manualmente (nome, telefone, data nascimento, notas)
- [x] **PAT-03**: Recepcionista pode editar dados de paciente
- [x] **PAT-04**: Pagina de perfil do paciente mostra historico de consultas
- [x] **PAT-05**: Pagina de perfil do paciente mostra historico de conversas WhatsApp

### WhatsApp Panel — Inbox

- [x] **WPP-01**: Recepcionista ve lista de conversas em tempo real via WebSocket
- [x] **WPP-02**: Recepcionista pode abrir conversa e ler historico completo de mensagens
- [x] **WPP-03**: Conversas mostram indicador de status: IA ativa / takeover humano / resolvida
- [x] **WPP-04**: Novas mensagens aparecem em tempo real sem recarregar a pagina
- [x] **WPP-05**: Recepcionista pode buscar conversas por nome/telefone do paciente
- [x] **WPP-06**: Painel lateral mostra info do paciente junto com a conversa

### WhatsApp Panel — Takeover

- [x] **WPP-07**: Recepcionista pode clicar "Assumir" para desativar IA naquela conversa
- [x] **WPP-08**: Recepcionista pode enviar mensagens como humano pelo painel
- [x] **WPP-09**: Recepcionista pode clicar "Devolver para IA" para reativar o bot
- [x] **WPP-10**: IA nao responde enquanto conversa esta em modo takeover
- [x] **WPP-11**: Indicador visual mostra que conversa esta em modo humano para todos os usuarios conectados

### WhatsApp Panel — Templates & Campaigns

- [x] **WPP-12**: Admin pode criar/editar templates de mensagem com variaveis (nome, data)
- [x] **WPP-13**: Recepcionista pode usar template para enviar mensagem rapida a um paciente
- [x] **WPP-14**: Admin pode criar campanha selecionando segmento de pacientes e template
- [x] **WPP-15**: Sistema envia campanha respeitando rate limits do WhatsApp
- [x] **WPP-16**: Admin ve status da campanha (enviado/entregue/lido/falha)

### Doctor Management

- [x] **DOC-01**: Admin ve lista de medicos com especialidade
- [x] **DOC-02**: Admin pode criar/editar perfil de medico (nome, especialidade, CRM, horarios)
- [x] **DOC-03**: Admin pode definir grade de disponibilidade por medico (dia x horarios)

### User Management

- [x] **USER-01**: Admin ve lista de usuarios do sistema com role
- [x] **USER-02**: Admin pode criar usuario com atribuicao de role
- [x] **USER-03**: Admin pode editar role de usuario existente
- [x] **USER-04**: Admin pode desativar/reativar usuario
- [x] **USER-05**: Usuario pode redefinir senha

### Backend API

- [x] **API-01**: FastAPI expoe endpoints REST para todas as entidades (patients, appointments, doctors, users, conversations)
- [x] **API-02**: FastAPI implementa autenticacao JWT com refresh token
- [x] **API-03**: FastAPI implementa middleware de multi-tenancy com filtro automatico por tenant_id
- [x] **API-04**: FastAPI integra Socket.IO para streaming de mensagens WhatsApp em tempo real

## v2 Requirements

### Dashboard Intelligence

- **DASH-V2-01**: Funil de conversao WhatsApp → agendamento → comparecimento
- **DASH-V2-02**: Performance do agente Sofia (tempo de resposta, resolucoes)
- **DASH-V2-03**: Receita por especialidade (requer tagging de valores)

### Advanced WhatsApp

- **WPP-V2-01**: Notas internas em conversas (contexto para troca de turno)
- **WPP-V2-02**: Atribuicao de conversa a funcionario especifico
- **WPP-V2-03**: Tags/categorizacao de conversas (urgencia, reclamacao)
- **WPP-V2-04**: Resumo automatico de conversa por IA

### Patient CRM

- **PAT-V2-01**: Segmentacao de pacientes (ativo, inativo, em risco)
- **PAT-V2-02**: Resumo de conversa WhatsApp no card do paciente

### Automation

- **AUTO-V2-01**: Waitlist management (notificar paciente quando vaga abre)
- **AUTO-V2-02**: Confirmacao automatica 24h antes via WhatsApp (controle no UI)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Prontuario Eletronico (PEP) | Complexidade CFM/TISS, meses de trabalho, sem diferencial WhatsApp |
| Portal do paciente (login paciente) | Dobra complexidade auth, compete com canal WhatsApp |
| Pagamento online / billing | PCI compliance, gateway, seguro — v2+ |
| App mobile nativo | Web responsivo resolve v1, PWA como ponte |
| Video consulta / telemedicina | Categoria de produto diferente (WebRTC) |
| Multi-idioma | pt-BR unico mercado v1, i18n sem valor agora |
| Integracao TISS/ANS | Cada plano tem regras diferentes, escopo proprio |
| SEO avancado na landing | SEO basico sim, blog/conteudo nao |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| LAND-01 | Phase 1 | Complete |
| LAND-02 | Phase 1 | Complete |
| LAND-03 | Phase 1 | Complete |
| LAND-04 | Phase 1 | Complete |
| AUTH-01 | Phase 2 | Complete |
| AUTH-02 | Phase 2 | Complete |
| AUTH-03 | Phase 2 | Complete |
| AUTH-04 | Phase 2 | Complete |
| AUTH-05 | Phase 2 | Complete |
| AUTH-06 | Phase 2 | Complete |
| TENANT-01 | Phase 2 | Complete |
| TENANT-02 | Phase 2 | Complete |
| TENANT-03 | Phase 2 | Complete |
| API-02 | Phase 2 | Complete |
| API-03 | Phase 2 | Complete |
| AGENDA-01 | Phase 3 | Complete |
| AGENDA-02 | Phase 3 | Complete |
| AGENDA-03 | Phase 3 | Complete |
| AGENDA-04 | Phase 3 | Complete |
| AGENDA-05 | Phase 3 | Complete |
| AGENDA-06 | Phase 3 | Complete |
| AGENDA-07 | Phase 3 | Complete |
| PAT-01 | Phase 3 | Complete |
| PAT-02 | Phase 3 | Complete |
| PAT-03 | Phase 3 | Complete |
| PAT-04 | Phase 3 | Complete |
| PAT-05 | Phase 3 | Complete |
| DOC-01 | Phase 3 | Complete |
| DOC-02 | Phase 3 | Complete |
| DOC-03 | Phase 3 | Complete |
| USER-01 | Phase 3 | Complete |
| USER-02 | Phase 3 | Complete |
| USER-03 | Phase 3 | Complete |
| USER-04 | Phase 3 | Complete |
| USER-05 | Phase 3 | Complete |
| API-01 | Phase 3 | Complete |
| WPP-01 | Phase 4 | Complete |
| WPP-02 | Phase 4 | Complete |
| WPP-03 | Phase 4 | Complete |
| WPP-04 | Phase 4 | Complete |
| WPP-05 | Phase 4 | Complete |
| WPP-06 | Phase 4 | Complete |
| WPP-07 | Phase 4 | Complete |
| WPP-08 | Phase 4 | Complete |
| WPP-09 | Phase 4 | Complete |
| WPP-10 | Phase 4 | Complete |
| WPP-11 | Phase 4 | Complete |
| API-04 | Phase 4 | Complete |
| DASH-01 | Phase 5 | Complete |
| DASH-02 | Phase 5 | Complete |
| DASH-03 | Phase 5 | Complete |
| DASH-04 | Phase 5 | Complete |
| WPP-12 | Phase 5 | Complete |
| WPP-13 | Phase 5 | Complete |
| WPP-14 | Phase 5 | Complete |
| WPP-15 | Phase 5 | Complete |
| WPP-16 | Phase 5 | Complete |

**Coverage:**
- v1 requirements: 57 total
- Mapped to phases: 57
- Unmapped: 0

---
*Requirements defined: 2026-03-29*
*Last updated: 2026-03-29 — traceability mapped after roadmap creation*
