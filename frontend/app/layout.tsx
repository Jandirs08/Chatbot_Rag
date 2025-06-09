import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AppSidebar } from "./components/AppSidebar";

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
        <div className="flex h-full" style={{ background: "rgb(38, 38, 41)" }}>
          <AppSidebar />
          <div className="flex-1 md:ml-[var(--sidebar-width)] p-4">
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}
