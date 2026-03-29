const steps = [
  {
    num: "1",
    title: "Cadastre sua clinica",
    body: "Informe os dados basicos, especialidades e horarios de atendimento.",
  },
  {
    num: "2",
    title: "Conecte o WhatsApp",
    body: "Integracao simples com o numero ja usado pela sua clinica.",
  },
  {
    num: "3",
    title: "Personalize o atendente",
    body: "Nome, tom de voz e respostas especificas para sua especialidade.",
  },
  {
    num: "4",
    title: "Ative e descanse",
    body: "A IA cuida do atendimento. Voce foca nos pacientes presenciais.",
  },
];

export default function HowItWorksSection() {
  return (
    <section className="bg-white py-[100px] px-12 max-[900px]:py-[60px] max-[900px]:px-6">
      <div className="text-xs font-semibold tracking-[2px] uppercase text-green-500 mb-3">Como funciona</div>
      <h2
        className="font-serif text-green-900 max-w-[520px] leading-snug"
        style={{ fontSize: "clamp(2rem, 3vw, 2.8rem)" }}
      >
        Simples de configurar, <em className="italic text-green-500">poderoso</em> na pratica
      </h2>

      {/* Steps container */}
      <div className="grid grid-cols-4 max-[900px]:grid-cols-2 gap-8 mt-[60px] relative">
        {/* Dashed connector line */}
        <div
          className="absolute top-7 left-[12%] right-[12%] h-px max-[900px]:hidden"
          style={{ background: "repeating-linear-gradient(90deg, #b4dfc4 0 8px, transparent 8px 16px)" }}
        />

        {steps.map((step) => (
          <div key={step.num} className="text-center relative">
            <div className="w-14 h-14 bg-green-500 text-white rounded-full flex items-center justify-center font-serif text-xl mx-auto mb-5 relative z-10 shadow-[0_0_0_8px_white]">
              {step.num}
            </div>
            <h4 className="font-serif text-base text-green-900 mb-2">{step.title}</h4>
            <p className="text-sm text-gray-600 leading-relaxed font-light">{step.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
