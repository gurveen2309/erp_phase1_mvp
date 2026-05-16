const COMPANY_NAME = process.env.NEXT_PUBLIC_COMPANY_NAME || "Saini Enterprises";
const COMPANY_ADDRESS =
  process.env.NEXT_PUBLIC_COMPANY_ADDRESS ||
  "#5, St. No.1 (Band gali), Sua road, Ganpati Estate (near Lakshmi Kanda), Sahnewal";
const COMPANY_GSTIN = process.env.NEXT_PUBLIC_COMPANY_GSTIN || "";
const COMPANY_PHONE = process.env.NEXT_PUBLIC_COMPANY_PHONE || "";
const COMPANY_EMAIL = process.env.NEXT_PUBLIC_COMPANY_EMAIL || "";
const ADMIN_URL = process.env.NEXT_PUBLIC_ADMIN_URL || "http://localhost:8000/admin/";

const SERVICES = [
  {
    title: "Annealing",
    description: "Softening metals through controlled heating and slow cooling to relieve internal stresses.",
  },
  {
    title: "Stress Relieving",
    description: "Reducing residual stresses from machining or welding without altering microstructure.",
  },
  {
    title: "Hardening",
    description: "Increasing surface and core hardness for high-tensile fasteners and components.",
  },
  {
    title: "Tempering",
    description: "Post-hardening heat treatment to improve toughness and reduce brittleness.",
  },
  {
    title: "Normalisation",
    description: "Restoring uniform grain structure for consistent mechanical properties across the batch.",
  },
];

const WHY_US = [
  "Specialists in high tensile nuts, bolts, and fastener heat treatment",
  "GST registered — compliant invoicing for all clients",
  "Consistent quality across high-volume production runs",
  "Reliable turnaround with on-time delivery",
  "Experienced team with decades of industry knowledge",
];

export default function MarketingHomepage() {
  return (
    <div className="min-h-screen flex flex-col bg-white text-zinc-900">

      {/* Navbar */}
      <nav className="flex items-center justify-between px-6 py-4 bg-blue-950 shadow-md">
        <span className="text-lg font-bold tracking-tight text-white">{COMPANY_NAME}</span>
        <a
          href={ADMIN_URL}
          className="text-sm font-semibold px-4 py-2 rounded-md bg-amber-500 text-blue-950 hover:bg-amber-400 transition-colors"
        >
          Back Office
        </a>
      </nav>

      {/* Hero */}
      <section className="relative min-h-[600px] flex items-center overflow-hidden">
        {/* Photo — full bleed, anchored to show the glowing bolts/fire on the right */}
        <div
          className="absolute inset-0"
          style={{ backgroundImage: "url('/hero-cropped.jpg')", backgroundSize: "cover", backgroundPosition: "center right" }}
        />
        {/* Gradient: solid blue-950 left → transparent right, so text sits on clean dark and image bleeds through */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-950 via-blue-950/95 via-40% to-blue-950/10" />

        {/* Amber glow accent — echoes the gold swoosh on the banner */}
        <div className="absolute bottom-0 left-0 w-2/3 h-1 bg-gradient-to-r from-amber-500 to-transparent" />

        {/* Content — left-aligned, sitting on the solid gradient */}
        <div className="relative z-10 px-8 md:px-16 py-24 max-w-2xl">
          <p className="text-amber-400 text-sm font-semibold uppercase tracking-widest mb-4">
            Since Sahnewal, Ludhiana
          </p>
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-white leading-tight">
            {COMPANY_NAME}
          </h1>
          <div className="mt-5 flex items-center gap-3">
            <div className="h-px w-8 bg-amber-500" />
            <p className="text-lg font-bold text-amber-400">
              Specialists in High Tensile Nuts &amp; Bolts
            </p>
          </div>
          <p className="mt-2 ml-11 text-base font-semibold text-amber-300/80">
            All Types of Heat Treatment
          </p>
          <p className="mt-5 text-base text-blue-200/70 max-w-md leading-relaxed">
            Precision heat treatment for the manufacturing industry — quality you can measure,
            reliability you can count on.
          </p>
        </div>
      </section>

      {/* What We Do */}
      <section className="px-6 py-20 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-blue-950 mb-2 text-center">What We Do</h2>
          <p className="text-center text-zinc-400 mb-10 text-sm">All types of heat treatment for nuts, bolts &amp; industrial components</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {SERVICES.map((s) => (
              <div key={s.title} className="rounded-xl border border-zinc-200 p-6 hover:shadow-md transition-shadow">
                <div className="w-8 h-1 rounded-full bg-amber-500 mb-4" />
                <h3 className="text-base font-bold text-blue-950 mb-2">{s.title}</h3>
                <p className="text-sm text-zinc-500 leading-relaxed">{s.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="bg-blue-950 px-6 py-20">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-white mb-8 text-center">Why Choose Us</h2>
          <ul className="space-y-4">
            {WHY_US.map((item) => (
              <li key={item} className="flex items-start gap-3 text-blue-100">
                <span className="mt-1.5 h-2 w-2 rounded-full bg-amber-400 flex-shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Contact */}
      <section className="px-6 py-20 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-blue-950 mb-2">Reach Out to Us</h2>
          <p className="text-zinc-400 text-sm mb-10">We&apos;re happy to discuss your heat treatment requirements.</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">

            {COMPANY_PHONE && (
              <a
                href={`tel:${COMPANY_PHONE.replace(/\s/g, "")}`}
                className="flex flex-col items-center gap-3 rounded-xl border border-zinc-200 p-6 hover:border-amber-400 hover:shadow-md transition-all group"
              >
                <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center group-hover:bg-amber-100 transition-colors">
                  <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
                  </svg>
                </div>
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Call Us</span>
                <span className="text-sm font-semibold text-blue-950">{COMPANY_PHONE}</span>
              </a>
            )}

            {COMPANY_EMAIL && (
              <a
                href={`mailto:${COMPANY_EMAIL}`}
                className="flex flex-col items-center gap-3 rounded-xl border border-zinc-200 p-6 hover:border-amber-400 hover:shadow-md transition-all group"
              >
                <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center group-hover:bg-amber-100 transition-colors">
                  <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                  </svg>
                </div>
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Email Us</span>
                <span className="text-sm font-semibold text-blue-950 break-all">{COMPANY_EMAIL}</span>
              </a>
            )}

            {COMPANY_ADDRESS && (
              <div className="flex flex-col items-center gap-3 rounded-xl border border-zinc-200 p-6">
                <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center">
                  <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                  </svg>
                </div>
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">Visit Us</span>
                <span className="text-sm font-semibold text-blue-950 text-center leading-relaxed">{COMPANY_ADDRESS}</span>
              </div>
            )}

          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-blue-950 border-t border-blue-900 px-6 py-8 text-center text-sm space-y-1">
        <p className="font-bold text-white">{COMPANY_NAME}</p>
        {COMPANY_ADDRESS && <p className="text-blue-300">{COMPANY_ADDRESS}</p>}
        {COMPANY_GSTIN && <p className="text-blue-400">GSTIN: {COMPANY_GSTIN}</p>}
      </footer>
    </div>
  );
}
