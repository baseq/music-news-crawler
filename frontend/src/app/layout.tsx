import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Music Digest — Daily music news in your language",
  description:
    "Subscribe to daily music news digests across indie, metal, jazz, electronic, underground and more — translated into your language.",
  openGraph: {
    title: "Music Digest",
    description: "Daily music news across 150 sources, 6 languages, 14 channels.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-bg text-body min-h-screen antialiased">
        <nav className="border-b border-border sticky top-0 z-50 bg-bg/90 backdrop-blur">
          <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
            <a href="/" className="font-bold text-heading text-lg tracking-tight">
              🎵 Music Digest
            </a>
            <div className="flex items-center gap-6 text-sm">
              <a href="/channels" className="text-subtle hover:text-heading transition-colors">
                Channels
              </a>
              <a
                href="/subscribe"
                className="px-4 py-1.5 bg-accent text-white rounded-full font-medium hover:bg-blue-700 transition-colors"
              >
                Subscribe
              </a>
            </div>
          </div>
        </nav>
        <main className="max-w-5xl mx-auto px-4 py-10">{children}</main>
        <footer className="border-t border-border mt-16 py-8 text-center text-muted text-sm">
          Music Digest &mdash; 150 sources &middot; 6 languages &middot; 14 channels &middot; $0/month
        </footer>
      </body>
    </html>
  );
}
