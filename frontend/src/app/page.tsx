import { supabase, Channel } from "@/lib/supabase";
import Link from "next/link";

const GENRE_COLORS: Record<string, string> = {
  geopolitics:  "bg-blue-900/40 text-blue-300",
  defense:      "bg-red-900/40 text-red-300",
  tech:         "bg-cyan-900/40 text-cyan-300",
  ai:           "bg-violet-900/40 text-violet-300",
  startups:     "bg-indigo-900/40 text-indigo-300",
  economy:      "bg-green-900/40 text-green-300",
  finance:      "bg-emerald-900/40 text-emerald-300",
  energy:       "bg-amber-900/40 text-amber-300",
  science:      "bg-purple-900/40 text-purple-300",
  health:       "bg-pink-900/40 text-pink-300",
  environment:  "bg-lime-900/40 text-lime-300",
  society:      "bg-orange-900/40 text-orange-300",
  romania:      "bg-yellow-900/40 text-yellow-300",
};

async function getFeaturedChannels(): Promise<Channel[]> {
  const { data } = await supabase
    .from("channels")
    .select("*")
    .eq("is_active", true)
    .order("sort_order")
    .limit(6);
  return data ?? [];
}

export default async function HomePage() {
  const channels = await getFeaturedChannels();

  return (
    <div>
      {/* Hero */}
      <section className="py-20 text-center">
        <p className="text-subtle text-sm uppercase tracking-widest mb-4">
          World news, daily
        </p>
        <h1 className="text-5xl md:text-6xl font-bold text-heading mb-6 leading-tight">
          Your news.<br />Your language.
        </h1>
        <p className="text-lg text-body max-w-xl mx-auto mb-10 leading-relaxed">
          37 news sources across 6 languages — geopolitics, tech, economy, Romania,
          and more — summarised daily and delivered to your inbox.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/subscribe"
            className="px-7 py-3 bg-accent text-white rounded-full font-semibold text-base hover:bg-blue-700 transition-colors"
          >
            Subscribe free →
          </Link>
          <Link
            href="/channels"
            className="px-7 py-3 border border-border text-subtle rounded-full font-semibold text-base hover:border-heading hover:text-heading transition-colors"
          >
            Browse channels
          </Link>
        </div>
      </section>

      {/* Stats bar */}
      <section className="border border-border rounded-xl p-6 mb-16 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
        {[
          ["37", "Sources"],
          ["6", "Languages"],
          ["7", "Channels"],
          ["Daily", "Digest"],
        ].map(([val, label]) => (
          <div key={label}>
            <p className="text-3xl font-bold text-heading">{val}</p>
            <p className="text-sm text-subtle mt-1">{label}</p>
          </div>
        ))}
      </section>

      {/* Featured channels */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-heading">Featured channels</h2>
          <Link href="/channels" className="text-sm text-subtle hover:text-heading transition-colors">
            View all →
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {channels.map((ch) => (
            <Link
              key={ch.id}
              href={`/channels/${ch.slug}`}
              className="group block p-5 border border-border rounded-xl bg-surface hover:border-accent-light/50 transition-all hover:bg-surface/80"
            >
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">{ch.icon}</span>
                <h3 className="font-semibold text-heading group-hover:text-accent-light transition-colors">
                  {ch.name}
                </h3>
              </div>
              <p className="text-sm text-subtle leading-relaxed mb-4 line-clamp-2">
                {ch.description}
              </p>
              {ch.genre_filters && (
                <div className="flex flex-wrap gap-1.5">
                  {ch.genre_filters.slice(0, 3).map((g) => (
                    <span
                      key={g}
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        GENRE_COLORS[g] ?? "bg-gray-800 text-gray-400"
                      }`}
                    >
                      {g}
                    </span>
                  ))}
                </div>
              )}
            </Link>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="mt-24">
        <h2 className="text-2xl font-bold text-heading mb-10 text-center">How it works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              n: "1",
              title: "We crawl 37 sources daily",
              body: "RSS feeds cover Reuters, BBC, Al Jazeera, TechCrunch, Digi24, HotNews and more — geopolitics, tech, economy, and Romanian news in 6 languages.",
            },
            {
              n: "2",
              title: "AI summarises & translates",
              body: "Each article gets a 3-sentence summary, topic tags, and content type. Then it's translated into your chosen language.",
            },
            {
              n: "3",
              title: "You get a morning digest",
              body: "One clean email per channel, every morning. Direct links to original articles. One-click unsubscribe.",
            },
          ].map((step) => (
            <div key={step.n} className="p-6 border border-border rounded-xl">
              <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center text-white font-bold text-sm mb-4">
                {step.n}
              </div>
              <h3 className="font-semibold text-heading mb-2">{step.title}</h3>
              <p className="text-sm text-subtle leading-relaxed">{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mt-24 text-center py-16 border border-border rounded-2xl bg-surface">
        <h2 className="text-3xl font-bold text-heading mb-4">Ready to subscribe?</h2>
        <p className="text-subtle mb-8 max-w-md mx-auto">
          Pick your channels, choose your language, enter your email. That's it. No account needed.
        </p>
        <Link
          href="/subscribe"
          className="px-8 py-3.5 bg-accent text-white rounded-full font-semibold text-base hover:bg-blue-700 transition-colors"
        >
          Get started — it's free →
        </Link>
      </section>
    </div>
  );
}
