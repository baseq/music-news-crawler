import { supabase, Channel } from "@/lib/supabase";
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "All Channels — Music Digest",
  description: "Browse all 14 music digest channels — indie, metal, jazz, electronic, underground and more.",
};

const GENRE_COLORS: Record<string, string> = {
  indie:        "bg-violet-900/40 text-violet-300",
  metal:        "bg-red-900/40 text-red-300",
  jazz:         "bg-amber-900/40 text-amber-300",
  electronic:   "bg-cyan-900/40 text-cyan-300",
  techno:       "bg-blue-900/40 text-blue-300",
  underground:  "bg-green-900/40 text-green-300",
  rock:         "bg-orange-900/40 text-orange-300",
  folk:         "bg-yellow-900/40 text-yellow-300",
  "hip-hop":    "bg-pink-900/40 text-pink-300",
  experimental: "bg-purple-900/40 text-purple-300",
  punk:         "bg-rose-900/40 text-rose-300",
};

async function getChannels(): Promise<Channel[]> {
  const { data } = await supabase
    .from("channels")
    .select("*")
    .eq("is_active", true)
    .order("sort_order");
  return data ?? [];
}

export default async function ChannelsPage() {
  const channels = await getChannels();

  return (
    <div>
      <div className="mb-10">
        <h1 className="text-4xl font-bold text-heading mb-3">All channels</h1>
        <p className="text-subtle">
          {channels.length} channels available. Subscribe to as many as you like.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {channels.map((ch) => (
          <div
            key={ch.id}
            className="flex flex-col p-5 border border-border rounded-xl bg-surface"
          >
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">{ch.icon}</span>
              <h2 className="font-semibold text-heading text-lg">{ch.name}</h2>
            </div>

            <p className="text-sm text-subtle leading-relaxed mb-4 flex-1">
              {ch.description}
            </p>

            {ch.genre_filters && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                {ch.genre_filters.map((g) => (
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

            {ch.content_filters && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                {ch.content_filters.map((c) => (
                  <span
                    key={c}
                    className="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 font-medium"
                  >
                    {c.replace("-", " ")}
                  </span>
                ))}
              </div>
            )}

            <div className="flex gap-2 mt-auto">
              <Link
                href={`/channels/${ch.slug}`}
                className="flex-1 text-center px-3 py-2 border border-border rounded-lg text-sm text-subtle hover:border-heading hover:text-heading transition-colors"
              >
                Preview
              </Link>
              <Link
                href={`/subscribe?channel=${ch.slug}`}
                className="flex-1 text-center px-3 py-2 bg-accent text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                Subscribe
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
