const stats = [
  { num: "24h", label: "Atendimento ininterrupto, todos os dias" },
  { num: "-70%", label: "Reducao de faltas com lembretes automaticos" },
  { num: "3x", label: "Mais agendamentos sem aumentar a equipe" },
];

export default function StatsSection() {
  return (
    <section className="bg-green-900 py-[60px] px-12 max-[900px]:py-12 max-[900px]:px-6 grid grid-cols-3 max-[900px]:grid-cols-1 gap-10 text-center">
      {stats.map((stat, i) => (
        <div key={stat.num} className="relative">
          {/* Divider for non-last items */}
          {i < stats.length - 1 && (
            <div className="absolute right-0 top-[20%] h-[60%] w-px bg-white/10 max-[900px]:hidden" />
          )}
          <span className="font-serif text-5xl text-green-400 block leading-none mb-2">{stat.num}</span>
          <div className="text-sm text-white/60 leading-snug">{stat.label}</div>
        </div>
      ))}
    </section>
  );
}
