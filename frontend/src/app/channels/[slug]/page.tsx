import { supabase, Channel, Article } from "@/lib/supabase";
import { notFound } from "next/navigation";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import type { Metadata } from "next";

export const revalidate = 3600;  // ISR — revalidate every hour

interface Props {
  params: { slug: string };
  searchParams: { lang?: string };
}

const LANG_LABELS: Record<string, string> = {
  en: "English", ro: "Română", fr: "Français",
  de: "Deutsch", it: "Italiano", es: "Español",
};

const GENRE_COLORS: Record<string, string> = {
  indie: "bg-violet-900/40 text-violet-300",
  metal: "bg-red-900/40 text-red-300",
  jazz: "bg-amber-900/40 text-amber-300",
  electronic: "bg-cyan-900/40 text-cyan-300",
  techno: "bg-blue-900/40 text-blue-300",
  underground: "bg-green-900/40 text-green-300",
  rock: "bg-orange-900/40 text-orange-300",
  folk: "bg-yellow-900/40 text-yellow-300",
  "hip-hop": "bg-pink-900/40 text-pink-300",
  experimental: "bg-purple-900/40 text-purple-300",
  punk: "bg-rose-900/40 text-rose-300",
};

async function getChannel(slug: string): Promise<Channel | null> {
  const { data } = await supabase
    .from("channels")
    .select("*")
    .eq("slug", slug)
    .eq("is_active", true)
    .single();
  return data;
}

async function getArticles(channel: Channel, lang: string): Promise<Article[]> {
  // Build base query
  let q = supabase
    .from("articles")
    .select(`
      id, url, title, author, image_url, published_at,
      summary_en, genres, content_type, sentiment,
      sources(name, language)
    `)
    .eq("is_processed", true)
    .order("published_at", { ascending: false })
    .limit(20);

  const { data } = await q;
  const articles: Article[] = data ?? [];

  // Apply channel filters in JS (Supabase can't do array-overlap in free plan without RPC)
  let filtered = articles;
  if (channel.genre_filters?.length) {
    filtered = filtered.filter((a) =>
      (a.genres ?? []).some((g) => channel.genre_filters!.includes(g))
    );
  }
  if (channel.content_filters?.length) {
    filtered = filtered.filter((a) =>
      channel.content_filters!.includes(a.content_type ?? "")
    );
  }

  // Fetch translations if lang !== "en"
  if (lang !== "en" && filtered.length > 0) {
    const ids = filtered.map((a) => a.id);
    const { data: translations } = await supabase
      .from("article_translations")
      .select("article_id, summary_translated")
      .in("article_id", ids)
      .eq("language", lang);

    const transMap: Record<string, string> = {};
    for (const t of translations ?? []) {
      transMap[t.article_id] = t.summary_translated;
    }
    return filtered.map((a) => ({
      ...a,
      display_summary: transMap[a.id] ?? a.summary_en ?? "",
    })) as Article[];
  }

  return filtered.map((a) => ({ ...a, display_summary: a.summary_en ?? "" })) as Article[];
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const channel = await getChannel(params.slug);
  if (!channel) return {};
  return {
    title: `${channel.name} — Music Digest`,
    description: channel.description,
  };
}

export default async function ChannelPage({ params, searchParams }: Props) {
  const channel = await getChannel(params.slug);
  if (!channel) notFound();

  const lang = searchParams.lang ?? "en";
  const articles = await getArticles(channel, lang);

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <Link href="/channels" className="text-subtle text-sm hover:text-heading transition-colors mb-4 inline-block">
          ← All channels
        </Link>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-4xl font-bold text-heading flex items-center gap-3">
              <span>{channel.icon}</span> {channel.name}
            </h1>
            <p className="text-subtle mt-2 max-w-xl">{channel.description}</p>
          </div>
          <Link
            href={`/subscribe?channel=${channel.slug}`}
            className="shrink-0 px-5 py-2.5 bg-accent text-white rounded-full font-semibold text-sm hover:bg-blue-700 transition-colors"
          >
            Subscribe
          </Link>
        </div>
      </div>

      {/* Language switcher */}
      <div className="flex items-center gap-2 mb-8 flex-wrap">
        <span className="text-xs text-muted uppercase tracking-wider mr-1">Preview in:</span>
        {Object.entries(LANG_LABELS).map(([code, label]) => (
          <Link
            key={code}
            href={`/channels/${channel.slug}?lang=${code}`}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              lang === code
                ? "bg-accent text-white"
                : "border border-border text-subtle hover:border-heading hover:text-heading"
            }`}
          >
            {label}
          </Link>
        ))}
      </div>

      {/* Article count */}
      <p className="text-subtle text-sm mb-6">
        {articles.length} recent article{articles.length !== 1 ? "s" : ""}
        {lang !== "en" && (
          <span className="ml-2 text-xs text-muted">
            (summaries translated to {LANG_LABELS[lang]})
          </span>
        )}
      </p>

      {/* Articles */}
      {articles.length === 0 ? (
        <div className="text-center py-24 border border-border rounded-xl">
          <p className="text-subtle text-lg mb-2">No articles yet</p>
          <p className="text-muted text-sm">Check back after the first crawl runs at 6am UTC.</p>
        </div>
      ) : (
        <div className="space-y-px border border-border rounded-xl overflow-hidden">
          {articles.map((article, i) => {
            const src = article.sources as { name: string; language: string } | null;
            const displaySummary = (article as any).display_summary ?? article.summary_en;
            const pubDate = article.published_at
              ? formatDistanceToNow(new Date(article.published_at), { addSuffix: true })
              : null;

            return (
              <article
                key={article.id}
                className={`p-6 bg-surface hover:bg-border/20 transition-colors ${
                  i > 0 ? "border-t border-border" : ""
                }`}
              >
                {/* Tags row */}
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {(article.genres ?? []).slice(0, 3).map((g) => (
                    <span
                      key={g}
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        GENRE_COLORS[g] ?? "bg-gray-800 text-gray-400"
                      }`}
                    >
                      {g}
                    </span>
                  ))}
                  {article.content_type && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-900/30 text-emerald-400 font-medium">
                      {article.content_type.replace("-", " ")}
                    </span>
                  )}
                </div>

                {/* Title */}
                <h2 className="text-lg font-semibold text-heading mb-1 leading-snug">
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-accent-light transition-colors"
                  >
                    {article.title}
                  </a>
                </h2>

                {/* Meta */}
                <p className="text-xs text-muted mb-3">
                  {src?.name}
                  {pubDate && <> &middot; {pubDate}</>}
                  {article.author && <> &middot; {article.author}</>}
                </p>

                {/* Summary */}
                {displaySummary && (
                  <p className="text-sm text-body leading-relaxed mb-4">
                    {displaySummary}
                  </p>
                )}

                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-medium text-accent-light hover:underline"
                >
                  Read original →
                </a>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
