import { LoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <>
      {/* Left illustration panel — D-05 */}
      <div className="hidden lg:flex w-1/2 bg-green-600 flex-col items-center justify-center p-12">
        <div className="text-center text-white">
          <h1 className="font-serif text-5xl mb-4">MedIA</h1>
          <p className="text-green-100 text-lg mb-8">
            Gestao inteligente para sua clinica
          </p>
          {/* Medical icon — simple SVG stethoscope */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="80"
            height="80"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="mx-auto opacity-60"
            aria-hidden="true"
          >
            <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3" />
            <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4" />
            <circle cx="20" cy="10" r="2" />
          </svg>
        </div>
      </div>

      {/* Right form panel */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-off-white">
        <div className="w-full max-w-md px-8">
          <h2 className="font-serif text-2xl text-gray-800 mb-2">Entrar</h2>
          <p className="text-gray-600 mb-8">Acesse o painel da sua clinica</p>
          <LoginForm />
          <p className="text-center text-gray-400 text-sm mt-12">MedIA</p>
        </div>
      </div>
    </>
  );
}
