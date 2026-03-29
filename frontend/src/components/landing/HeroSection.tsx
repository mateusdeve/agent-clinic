const WHATSAPP_NUMBER = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER ?? "5511999999999";
const WA_MESSAGE = encodeURIComponent("Ola! Quero saber mais sobre o MedIA para minha clinica.");
const WA_URL = `https://wa.me/${WHATSAPP_NUMBER}?text=${WA_MESSAGE}`;

export default function HeroSection() {
  return (
    <section className="min-h-screen grid grid-cols-2 max-[900px]:grid-cols-1 items-center pt-[100px] px-12 pb-[60px] gap-[60px] max-[900px]:px-6 relative overflow-hidden">
      {/* Radial gradient blob */}
      <div
        className="absolute -top-48 -right-48 w-[700px] h-[700px] rounded-full pointer-events-none z-0"
        style={{ background: "radial-gradient(circle, #edf7f0 0%, transparent 70%)" }}
      />

      {/* Hero content */}
      <div className="z-10 relative">
        {/* Badge */}
        <div
          className="inline-flex items-center gap-1.5 bg-green-50 border border-green-100 text-green-600 px-3.5 py-1.5 rounded-full text-sm font-medium mb-7"
          style={{ animation: "fadeUp 0.6s ease both" }}
        >
          <span className="text-[0.5rem] text-green-400" style={{ animation: "pulse 2s infinite" }}>●</span>
          Lancamento em breve
        </div>

        {/* H1 */}
        <h1
          className="font-serif text-green-900 mb-6 leading-[1.1]"
          style={{ fontSize: "clamp(2.4rem, 4vw, 3.6rem)", animation: "fadeUp 0.6s 0.1s ease both" }}
        >
          O atendente que <em className="italic text-green-500">nunca</em> tira folga da sua clinica
        </h1>

        {/* Subtitle */}
        <p
          className="text-gray-600 font-light leading-relaxed max-w-lg mb-10"
          style={{ animation: "fadeUp 0.6s 0.2s ease both" }}
        >
          Agendamentos, confirmacoes, lembretes e duvidas — tudo resolvido por IA, 24 horas por dia. Sua equipe foca no que realmente importa: os pacientes.
        </p>

        {/* CTA button */}
        <a
          href={WA_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-green-500 hover:bg-green-600 text-white font-semibold px-7 py-3.5 rounded-xl transition-all hover:-translate-y-0.5 hover:shadow-lg"
          style={{ animation: "fadeUp 0.6s 0.3s ease both" }}
        >
          Falar com especialista →
        </a>

        {/* Social proof */}
        <div
          className="flex items-center gap-3 mt-10"
          style={{ animation: "fadeUp 0.6s 0.5s ease both" }}
        >
          <div className="flex">
            <div className="w-9 h-9 rounded-full border-2 border-white bg-green-400 flex items-center justify-center text-xs font-semibold text-white">AC</div>
            <div className="w-9 h-9 rounded-full border-2 border-white bg-green-500 flex items-center justify-center text-xs font-semibold text-white -ml-2">MD</div>
            <div className="w-9 h-9 rounded-full border-2 border-white bg-green-600 flex items-center justify-center text-xs font-semibold text-white -ml-2">RS</div>
            <div className="w-9 h-9 rounded-full border-2 border-white flex items-center justify-center text-xs font-semibold text-white -ml-2" style={{ background: "#6cc494" }}>+</div>
          </div>
          <span className="text-sm text-gray-600">
            <strong className="text-green-600">+230 clinicas</strong> ja na fila de espera
          </span>
        </div>
      </div>

      {/* Hero visual (chat card) */}
      <div
        className="z-10 relative max-[900px]:hidden"
        style={{ animation: "fadeUp 0.6s 0.2s ease both" }}
      >
        <div
          className="bg-white rounded-[20px] p-6 border border-gray-200 max-w-[420px] mx-auto"
          style={{ boxShadow: "0 20px 60px rgba(46,158,96,0.12), 0 4px 16px rgba(0,0,0,0.06)" }}
        >
          {/* Chat header */}
          <div className="flex items-center gap-3 pb-4 border-b border-gray-200 mb-5">
            <div className="w-[42px] h-[42px] bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center text-xl">
              🤖
            </div>
            <div>
              <div className="font-semibold text-[0.95rem]">Assistente da Clinica</div>
              <div className="text-xs text-green-500 flex items-center gap-1">● Online agora</div>
            </div>
            <div className="ml-auto bg-green-50 text-green-600 text-[0.7rem] font-semibold px-2.5 py-1 rounded-full">
              IA Ativa
            </div>
          </div>

          {/* Chat messages */}
          <div className="flex flex-col gap-3">
            <div
              className="p-3 px-4 rounded-[14px] rounded-bl-sm text-sm leading-relaxed max-w-[85%] bg-off-white text-gray-800 self-start"
              style={{ animation: "fadeMsg 0.4s 0.5s ease both", opacity: 0 }}
            >
              Ola! Sou o assistente virtual da Clinica. Como posso ajudar voce hoje? 😊
            </div>
            <div
              className="p-3 px-4 rounded-[14px] rounded-br-sm text-sm leading-relaxed max-w-[85%] bg-green-500 text-white self-end"
              style={{ animation: "fadeMsg 0.4s 0.9s ease both", opacity: 0 }}
            >
              Preciso marcar uma consulta para amanha de manha
            </div>
            <div
              className="p-3 px-4 rounded-[14px] rounded-bl-sm text-sm leading-relaxed max-w-[85%] bg-off-white text-gray-800 self-start"
              style={{ animation: "fadeMsg 0.4s 1.3s ease both", opacity: 0 }}
            >
              Claro! Temos horarios disponiveis as <strong>09h00</strong> e <strong>10h30</strong> com a Dra. Ana. Qual prefere?
            </div>
            <div
              className="p-3 px-4 rounded-[14px] rounded-br-sm text-sm leading-relaxed max-w-[85%] bg-green-500 text-white self-end"
              style={{ animation: "fadeMsg 0.4s 1.7s ease both", opacity: 0 }}
            >
              09h00 perfeito!
            </div>
            {/* Typing indicator */}
            <div
              className="flex gap-1 p-3 px-4 bg-off-white rounded-[14px] rounded-bl-sm w-fit"
              style={{ animation: "fadeMsg 0.4s 2.1s ease both", opacity: 0 }}
            >
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full" style={{ animation: "bounce 1.2s infinite" }} />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full" style={{ animation: "bounce 1.2s 0.2s infinite" }} />
              <span className="w-1.5 h-1.5 bg-gray-400 rounded-full" style={{ animation: "bounce 1.2s 0.4s infinite" }} />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
