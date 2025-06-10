import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { RootLayoutClient } from "./components/RootLayoutClient";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Panel de Control del Chatbot",
  description: "Panel de administración para el chatbot personalizado",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="h-full">
      <body className={`${inter.className} h-full`}>
        <RootLayoutClient>{children}</RootLayoutClient>
      </body>
    </html>
  );
}
