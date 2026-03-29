const WHATSAPP_NUMBER = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER ?? "5511999999999";
const WA_MESSAGE = encodeURIComponent("Ola! Quero saber mais sobre o MedIA para minha clinica.");
const WA_URL = `https://wa.me/${WHATSAPP_NUMBER}?text=${WA_MESSAGE}`;

export default function NavBar() {
  return (
    <nav
      className="fixed top-0 left-0 right-0 z-[100] flex items-center justify-between px-12 py-5 border-b border-gray-200 max-[900px]:px-6 max-[900px]:py-4"
      style={{ background: "rgba(255,255,255,0.88)", backdropFilter: "blur(12px)" }}
    >
      <div className="font-serif text-2xl text-green-600" style={{ letterSpacing: "-0.5px" }}>
        Med<span className="italic text-green-400">IA</span>
      </div>
      <a
        href={WA_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="bg-green-500 hover:bg-green-600 hover:-translate-y-px text-white text-sm font-medium px-6 py-2.5 rounded-full transition-all duration-200 no-underline"
      >
        Entrar na lista
      </a>
    </nav>
  );
}
