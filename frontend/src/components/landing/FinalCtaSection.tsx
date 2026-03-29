const WHATSAPP_NUMBER = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER ?? "5511999999999";
const WA_MESSAGE = encodeURIComponent("Ola! Quero saber mais sobre o MedIA para minha clinica.");
const WA_URL = `https://wa.me/${WHATSAPP_NUMBER}?text=${WA_MESSAGE}`;

export default function FinalCtaSection() {
  return (
    <section className="bg-white py-[100px] px-12 max-[900px]:py-[60px] max-[900px]:px-6 text-center relative overflow-hidden">
      {/* Radial gradient blob */}
      <div
        className="absolute bottom-[-200px] left-1/2 -translate-x-1/2 w-[800px] h-[800px] rounded-full z-0"
        style={{ background: "radial-gradient(circle, #edf7f0 0%, transparent 60%)" }}
      />

      {/* Content wrapper */}
      <div className="relative z-10">
        {/* Badge */}
        <div className="inline-flex items-center gap-1.5 bg-green-50 border border-green-100 text-green-600 px-3.5 py-1.5 rounded-full text-sm font-medium mb-7">
          <span className="text-[0.5rem] text-green-400" style={{ animation: "pulse 2s infinite" }}>●</span>
          Vagas limitadas no lancamento
        </div>

        {/* H2 */}
        <h2
          className="font-serif text-green-900 max-w-[600px] mx-auto mb-5 leading-snug"
          style={{ fontSize: "clamp(2rem, 3.5vw, 3rem)" }}
        >
          Garanta acesso <em className="italic text-green-500">antecipado</em> com desconto exclusivo
        </h2>

        {/* Subtitle */}
        <p className="text-gray-600 font-light max-w-[480px] mx-auto mb-10">
          Os primeiros inscritos terao preco especial de fundadores e suporte prioritario na configuracao.
        </p>

        {/* CTA button */}
        <a
          href={WA_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-green-500 hover:bg-green-600 text-white font-semibold px-8 py-4 rounded-[14px] transition-all hover:-translate-y-0.5 text-base"
          style={{ boxShadow: "none" }}
          onMouseOver={undefined}
        >
          Falar com especialista →
        </a>
      </div>
    </section>
  );
}
