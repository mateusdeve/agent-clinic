# PRD — Agente de Atendimento para Clínica

## Contexto do Projeto

Construir um agente conversacional para atendimento de pacientes de uma clínica, utilizando **LangChain + LangGraph** para orquestração e **Langfuse** para observabilidade de todas as interações.

---

## Stack Técnica

| Componente             | Tecnologia                            |
| ---------------------- | ------------------------------------- |
| Orquestração do agente | LangGraph                             |
| LLM client             | LangChain                             |
| Modelo LLM             | via OpenRouter (`OPENROUTER_API_KEY`) |
| Observabilidade        | Langfuse (SDK v3)                     |
| Runtime                | Python 3.9+                           |

### Variáveis de Ambiente Disponíveis

```env
# Langfuse
LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_HOST=

# OpenRouter
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=
LLM_MODEL=
```

---

## Objetivo

Criar um agente que consiga realizar o atendimento inicial de pacientes de uma clínica, com capacidade de:

1. Recepcionar o paciente
2. Coletar informações básicas
3. Identificar o motivo da consulta
4. Verificar disponibilidade de agenda (mock)
5. Agendar consulta (mock)
6. Responder dúvidas frequentes

---

## Arquitetura do Agente (LangGraph)

### Grafo de Estados

```
[START]
   ↓
[recepcionar]          → Saúda o paciente e coleta nome
   ↓
[identificar_motivo]   → Pergunta o motivo da consulta / especialidade
   ↓
[coletar_dados]        → Coleta data de nascimento, convênio
   ↓
[verificar_agenda]     → Tool: consulta disponibilidade (mock)
   ↓
[confirmar_agendamento] → Confirma ou oferece alternativas
   ↓
[encerrar]             → Despede o paciente com resumo
```

### Estado do Agente

```python
class ClinicaState(TypedDict):
    messages: list[BaseMessage]
    nome_paciente: str
    motivo_consulta: str
    especialidade: str
    data_nascimento: str
    convenio: str
    data_agendamento: str
    horario_agendamento: str
    etapa: str  # recepcionar | identificar_motivo | coletar_dados | verificar_agenda | confirmar | encerrar
```

---

## Tools do Agente

### 1. `verificar_disponibilidade`

- **Input:** especialidade, data desejada
- **Output:** lista de horários disponíveis (mock)
- **Mock:** retorna horários fixos para fins de desenvolvimento

### 2. `agendar_consulta`

- **Input:** nome, especialidade, data, horário, convênio
- **Output:** código de confirmação (mock)
- **Mock:** gera UUID como protocolo

### 3. `buscar_faq`

- **Input:** pergunta do paciente
- **Output:** resposta baseada em FAQ pré-definido
- **FAQ cobre:** horários da clínica, convênios aceitos, endereço, preparo para exames

---

## Especialidades Disponíveis (Mock)

- Clínica Geral
- Cardiologia
- Dermatologia
- Ortopedia
- Ginecologia
- Pediatria

---

## Convênios Aceitos (Mock)

- Unimed
- Bradesco Saúde
- SulAmérica
- Amil
- Particular

---

## Integração com Langfuse

Todos os nós do grafo devem ser instrumentados com Langfuse v3:

```python
from langfuse import get_client

langfuse = get_client()

# Cada nó do grafo deve criar um span
with langfuse.start_as_current_observation(as_type="span", name="nome-do-no") as span:
    span.update(input=state, metadata={"etapa": state["etapa"]})
    # ... lógica do nó
    span.update(output=resultado)
```

### Dados a Rastrear por Trace

- Etapa atual do atendimento
- Especialidade solicitada
- Convênio informado
- Duração total do atendimento
- Se o agendamento foi concluído ou abandonado

---

## Estrutura de Arquivos

```
agent-clinic/
├── .env
├── requirements.txt
├── tests/
│   └── test_connections.py       ✅ já existe
├── src/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py              # Definição do grafo LangGraph
│   │   ├── state.py              # ClinicaState TypedDict
│   │   ├── nodes.py              # Funções de cada nó
│   │   └── prompts.py            # System prompts de cada etapa
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── agenda.py             # verificar_disponibilidade, agendar_consulta
│   │   └── faq.py                # buscar_faq
│   └── observability/
│       ├── __init__.py
│       └── langfuse_setup.py     # Configuração e helpers do Langfuse
└── main.py                       # Entry point CLI para testar o agente
```

---

## Comportamento Esperado

### Exemplo de Conversa

```
Agente: Olá! Bem-vindo à Clínica Saúde+. Meu nome é Sofia, sou a assistente virtual.
        Pode me informar seu nome, por favor?

Paciente: Meu nome é João Silva.

Agente: Olá, João! Em que posso te ajudar hoje?
        Você gostaria de agendar uma consulta ou tem alguma dúvida?

Paciente: Quero agendar com cardiologista.

Agente: Certo! Para qual data você prefere? Temos disponibilidade
        de segunda a sexta.

Paciente: Próxima terça-feira de manhã.

Agente: Encontrei os seguintes horários disponíveis para Cardiologia
        na próxima terça:
        - 08:00
        - 09:30
        - 11:00
        Qual prefere?

Paciente: 09:30

Agente: Perfeito! Você possui convênio?

Paciente: Unimed

Agente: ✅ Consulta agendada com sucesso!

        Resumo:
        - Paciente: João Silva
        - Especialidade: Cardiologia
        - Data: [próxima terça]
        - Horário: 09:30
        - Convênio: Unimed
        - Protocolo: #A2F4-9X1Z

        Até logo, João! Caso precise de mais informações, estou à disposição.
```

---

## Requisitos Não-Funcionais

- Respostas em **português brasileiro**
- Tom **cordial e profissional**
- Timeout por mensagem: **30 segundos**
- O agente deve **sempre confirmar** dados antes de finalizar o agendamento
- Em caso de erro, deve **informar o paciente** e oferecer alternativa humana

---

## Critérios de Aceite

- [ ] Agente consegue completar um agendamento do início ao fim
- [ ] Todos os nós do grafo aparecem como spans no Langfuse
- [ ] Tools mock retornam dados consistentes
- [ ] Agente responde FAQ corretamente
- [ ] Estado é mantido durante toda a conversa
- [ ] `main.py` permite testar via terminal

---

## Fora do Escopo (v1)

- Integração com sistema real de agenda
- Autenticação de pacientes
- Envio de confirmação por email/SMS
- Interface web ou WhatsApp
- Banco de dados persistente
