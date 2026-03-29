# MedIA — Sistema de Gestao de Clinicas com IA

## What This Is

Plataforma SaaS multi-tenant de gestao de clinicas medicas com atendente de IA no WhatsApp. O sistema combina um agente conversacional inteligente (agendamento, follow-up, FAQ, lembretes) com um painel web completo para administradores, recepcionistas e medicos. Inclui landing page de captura que redireciona leads direto para o WhatsApp.

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

### Active

- [ ] Landing page de captura com redirect para WhatsApp
- [ ] Autenticacao e controle de acesso (Admin, Recepcionista, Medico)
- [ ] Multi-tenancy: isolamento de dados por clinica
- [ ] Dashboard principal com metricas (ocupacao, confirmacoes, conversas)
- [ ] Painel WhatsApp: conversas em tempo real
- [ ] Painel WhatsApp: historico completo com busca
- [ ] Painel WhatsApp: takeover manual (humano assume da IA)
- [ ] Painel WhatsApp: templates e campanhas de mensagens em massa
- [ ] Gestao de agenda (visualizacao, bloqueio de horarios, remarcacao)
- [ ] Gestao de pacientes (cadastro, historico, contatos)
- [ ] Gestao de medicos/profissionais (perfil, especialidades, horarios)
- [ ] Gestao de usuarios do sistema (CRUD, permissoes por role)
- [ ] API REST para o frontend consumir dados do backend existente

### Out of Scope

- Portal do paciente (app/web para paciente acessar) — complexidade alta, foco v1 na equipe da clinica
- Integracao com prontuario eletronico (PEP) — depende de cada sistema, v2+
- Pagamentos/billing online — v2, foco v1 no atendimento
- App mobile nativo — web-first, responsivo resolve v1
- Video consulta / telemedicina — fora do escopo do produto

## Context

**Backend existente:** Python/FastAPI com pipeline dual-agent (Sofia + Carla) usando LangGraph. Integracao WhatsApp via Evolution API, banco PostgreSQL, sessoes em Redis, observabilidade Langfuse. O backend funciona standalone via webhook — precisa de API REST para o frontend.

**Frontend:** Apenas `site.html` estatico (landing page de referencia visual). O sistema web completo sera construido do zero com Next.js + Tailwind CSS.

**Modelo de negocio:** SaaS multi-tenant. Cada clinica tera seus dados isolados (tenant_id). Landing page captura leads e redireciona para WhatsApp com agente de vendas.

**Referencia visual:** `frontend/site.html` define a identidade visual (cores verdes, DM Serif Display + DM Sans, bordas arredondadas, estilo clean/medico).

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
| Next.js + Tailwind para frontend | Stack moderna, SSR para landing page SEO, produtividade alta | — Pending |
| SaaS multi-tenant desde v1 | Evita rewrite futuro, arquitetura escalavel | — Pending |
| Landing page redireciona para WhatsApp | Funil direto, sem sequencia de emails, conversao imediata | — Pending |
| Sem portal do paciente em v1 | Foco na equipe da clinica, reduz escopo | — Pending |
| Tres roles: Admin, Recepcionista, Medico | Cobre os fluxos essenciais sem complexidade excessiva | — Pending |

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
*Last updated: 2026-03-29 after initialization*
