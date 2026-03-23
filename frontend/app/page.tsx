import { BirthForm } from "@/components/BirthForm";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-bg to-brand-surface">
      <header className="pt-16 pb-4 text-center">
        <h1 className="font-heading text-5xl font-extrabold tracking-tight text-white">
          Be Better
        </h1>
        <p className="mt-3 text-lg text-brand-muted">
          找到你的天賦方向，成為更好的自己
        </p>
      </header>

      <main className="mx-auto max-w-xl px-4 pb-20">
        <BirthForm />
      </main>
    </div>
  );
}
