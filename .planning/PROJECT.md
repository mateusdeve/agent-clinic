# MedIA — Sistema de Gestao de Clinicas com IA

## What This Is

Plataforma SaaS multi-tenant de gestao de clinicas medicas com atendente de IA no WhatsApp. Combina agente conversacional inteligente (agendamento, follow-up, FAQ, lembretes) com painel web completo para administradores, recepcionistas e medicos. Inclui landing page de captura, dashboard operacional com KPIs, gestao de agenda/pacientes/medicos/usuarios, inbox WhatsApp em tempo real com takeover humano, templates de mensagem e campanhas em massa.

## Core Value

O paciente consegue agendar, remarcar e tirar duvidas pelo WhatsApp 24h por dia sem intervencao humana, e a equipe da clinica tem visibilidade total das conversas e agendamentos em tempo real.

## Requirements

### Validated

- ✓ Agente IA Sofia conversa com pacientes via WhatsApp — existing
- ✓ Agente Carla formata respostas para WhatsApp — existing
- ✓ Agendamento de consultas com verificacao de disponibilidade — existing
- ✓ Follow-up automatico de pacientes — existing
- ✓ RAG com historico de conversas para contexto — existing
- ✓ Integracao Evolution API para WhatsApp — existing
- ✓ Persistencia de sessao em Redis — existing
- ✓ Banco PostgreSQL com pacientes, consultas, medicos — existing
- ✓ Observabilidade via Langfuse — existing
- ✓ Landing page de captura com redirect para WhatsApp — v1.0
- ✓ Autenticacao e controle de acesso (Admin, Recepcionista, Medico) — v1.0
- ✓ Multi-tenancy: isolamento de dados por clinica — v1.0
- ✓ Dashboard principal com metricas (ocupacao, confirmacoes, conversas) — v1.0
- ✓ Painel WhatsApp: conversas em tempo real — v1.0
- ✓ Painel WhatsApp: historico completo com busca — v1.0
- ✓ Painel WhatsApp: takeover manual (humano assume da IA) — v1.0
- ✓ Painel WhatsApp: templates e campanhas de mensagens em massa — v1.0
- ✓ Gestao de agenda (visualizacao, bloqueio de horarios, remarcacao) — v1.0
- ✓ Gestao de pacientes (cadastro, historico, contatos) — v1.0
- ✓ Gestao de medicos/profissionais (perfil, especialidades, horarios) — v1.0
- ✓ Gestao de usuarios do sistema (CRUD, permissoes por role) — v1.0
- ✓ API REST para o frontend consumir dados do backend existente — v1.0

### Active

(Fresh for next milestone — define via `/gsd:new-milestone`)

### Out of Scope

- Prontuario Eletronico (PEP) — complexidade CFM/TISS, meses de trabalho, sem diferencial WhatsApp
- Portal do paciente (login paciente) — dobra complexidade auth, compete com canal WhatsApp
- Pagamento online / billing — PCI compliance, gateway, seguro — v2+
- App mobile nativo — web responsivo resolve v1, PWA como ponte
- Video consulta / telemedicina — categoria de produto diferente (WebRTC)
- Multi-idioma — pt-BR unico mercado v1, i18n sem valor agora
- Integracao TISS/ANS — cada plano tem regras diferentes, escopo proprio
- SEO avancado na landing — SEO basico sim, blog/conteudo nao
- Offline mode — real-time e core value

## Context

**Shipped v1.0 MVP** with ~18,363 LOC (9,667 frontend TypeScript/CSS + 8,696 backend Python) in 7 days.

**Tech stack:**
- Frontend: Next.js 16 + Tailwind CSS 4 + shadcn/ui + Recharts + Socket.IO client
- Backend: Python/FastAPI + LangGraph (Sofia/Carla agents) + Socket.IO server
- Database: PostgreSQL with RLS policies + Redis sessions
- Auth: NextAuth v5 + FastAPI JWT/Argon2
- WhatsApp: Evolution API
- LLM: OpenRouter
- Observability: Langfuse

**Known issues:**
- 2/3 tenant isolation tests fail because RLS migration not applied to live DB (infrastructure deployment gap)
- Phase 2 RLS migration needs `alembic upgrade head` on production database

## Constraints

- **Tech stack frontend**: Next.js + Tailwind CSS — decisao do usuario
- **Tech stack backend**: Python/FastAPI — ja existe, manter
- **WhatsApp**: Evolution API — ja integrado, manter
- **LLM**: OpenRouter — ja configurado, manter
- **Multi-tenancy**: Dados isolados por clinica desde v1
- **Idioma**: Interface em portugues brasileiro (pt-BR)
- **Design**: Seguir identidade visual do site.html (paleta verde, tipografia DM)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Next.js + Tailwind para frontend | Stack moderna, SSR para landing page SEO, produtividade alta | ✓ Good |
| SaaS multi-tenant desde v1 | Evita rewrite futuro, arquitetura escalavel | ✓ Good |
| Landing page redireciona para WhatsApp | Funil direto, sem sequencia de emails, conversao imediata | ✓ Good |
| Sem portal do paciente em v1 | Foco na equipe da clinica, reduz escopo | ✓ Good |
| Tres roles: Admin, Recepcionista, Medico | Cobre os fluxos essenciais sem complexidade excessiva | ✓ Good |
| Tailwind 4 CSS-first (sem tailwind.config.ts) | Design tokens via @theme em globals.css | ✓ Good |
| Raw SQL migrations via op.execute() | Sem ORM models no agent-service (psycopg2 only) | ✓ Good |
| BYPASSRLS para bot pipeline | WhatsApp bot pipeline funciona sem tenant context | ✓ Good |
| NextAuth v5 + proxy.ts route protection | Next.js 16.2.1 pattern per research | ✓ Good |
| Custom calendar com date-fns | Controle total da paleta verde, sem FullCalendar | ✓ Good |
| python-socketio ASGI mount | Socket.IO server co-hosted com FastAPI | ✓ Good |
| FOR UPDATE SKIP LOCKED para campaigns | Previne double-dispatch em APScheduler concorrente | ✓ Good |
| unstable_retry em error boundaries | Next.js 16.2.x breaking change (nao reset) | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-30 after v1.0 milestone*
