export default function TestimonialSection() {
  return (
    <section className="bg-green-50 py-[80px] px-12 max-[900px]:py-[60px] max-[900px]:px-6 flex items-center justify-center text-center">
      <div className="max-w-[680px]">
        <div className="text-[#f4c245] text-xl mb-6 tracking-widest">★★★★★</div>
        <p
          className="font-serif text-green-900 leading-snug italic mb-7"
          style={{ fontSize: "clamp(1.3rem, 2.5vw, 1.9rem)" }}
        >
          &ldquo;Finalmente consegui sair de ferias sem me preocupar com o agendamento. A IA atendeu mais de 80 pacientes enquanto eu estava viajando.&rdquo;
        </p>
        <p className="text-sm text-gray-600 font-medium">
          <strong className="text-green-600">Dra. Mariana Souza</strong> — Dermatologista, Sao Paulo
        </p>
      </div>
    </section>
  );
}
