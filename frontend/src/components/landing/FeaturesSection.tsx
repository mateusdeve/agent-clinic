const features = [
  {
    icon: "📅",
    title: "Agendamento Inteligente",
    body: "O paciente agenda pelo WhatsApp ou site em segundos. O sistema verifica disponibilidade e confirma automaticamente.",
  },
  {
    icon: "🔔",
    title: "Lembretes Automaticos",
    body: "Reduza faltas com mensagens automaticas 24h antes da consulta. Confirmacao com um clique, remarcacao sem esforco.",
  },
  {
    icon: "💬",
    title: "Atendimento 24/7",
    body: "Responde duvidas, fornece endereco, preparo para exames e muito mais — enquanto voce e sua equipe descansam.",
  },
  {
    icon: "📊",
    title: "Dashboard da Clinica",
    body: "Acompanhe ocupacao, taxa de confirmacao e historico de conversas em um painel simples e intuitivo.",
  },
  {
    icon: "⚡",
    title: "Integracao Rapida",
    body: "Conecta com seu sistema de prontuario atual. Configuracao em menos de 1 dia, sem precisar de TI.",
  },
  {
    icon: "🩺",
    title: "Personalizado para Saude",
    body: "Treinado com linguagem medica e protocolos de atendimento. Nunca da orientacoes clinicas — apenas logistica.",
  },
];

export default function FeaturesSection() {
  return (
    <section className="bg-off-white py-[100px] px-12 max-[900px]:py-[60px] max-[900px]:px-6">
      <div className="text-xs font-semibold tracking-[2px] uppercase text-green-500 mb-3">Recursos</div>
      <h2
        className="font-serif text-green-900 max-w-[520px] leading-snug mb-[60px]"
        style={{ fontSize: "clamp(2rem, 3vw, 2.8rem)" }}
      >
        Tudo que sua clinica precisa, <em className="italic text-green-500">automatizado</em>
      </h2>
      <div className="grid grid-cols-3 max-[900px]:grid-cols-1 gap-6">
        {features.map((feat) => (
          <div
            key={feat.title}
            className="bg-white rounded-[20px] p-8 border border-gray-200 transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_16px_40px_rgba(46,158,96,0.1)]"
          >
            <div className="w-[52px] h-[52px] bg-green-50 rounded-[14px] flex items-center justify-center text-2xl mb-5">
              {feat.icon}
            </div>
            <h3 className="font-serif text-xl text-green-900 mb-2.5">{feat.title}</h3>
            <p className="text-sm text-gray-600 leading-relaxed font-light">{feat.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
