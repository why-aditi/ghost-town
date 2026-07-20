import type { Metadata } from "next";
import { Cinzel, Caveat, Spectral } from "next/font/google";
import "./globals.css";

const cinzel = Cinzel({ subsets: ["latin"], weight: ["500", "700"], variable: "--font-display" });
const caveat = Caveat({ subsets: ["latin"], weight: ["500", "700"], variable: "--font-hand" });
const spectral = Spectral({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-serif" });

export const metadata: Metadata = {
  title: "Ghost Town",
  description: "A village of eight where whispers travel — watch gossip spread.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${cinzel.variable} ${caveat.variable} ${spectral.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
