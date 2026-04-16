import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Antigravity | Knowledge Engine",
  description: "Sistema Autônomo de Gestão de Conhecimento para Obsidian",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
