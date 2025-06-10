"use client";

import { AppSidebar } from "./AppSidebar";
import { SidebarProvider, useSidebar } from "./ui/sidebar"; // Import useSidebar
import { Button } from "./ui/button"; // Import Button
import { PanelLeft } from "lucide-react"; // Import PanelLeft icon
import { Toaster } from "./ui/toaster"; // Import Toaster component

export function RootLayoutClient({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <RootLayoutContent>{children}</RootLayoutContent>
      <Toaster /> {/* Add Toaster component here */}
    </SidebarProvider>
  );
}

// Nuevo componente interno para acceder al contexto del sidebar
function RootLayoutContent({ children }: { children: React.ReactNode }) {
  const { toggleSidebar, state } = useSidebar();

  return (
    <div className="flex h-full bg-background">
      <AppSidebar />
      <div className="flex-1 flex flex-col">
        {/* Eliminado: El header con el botón de colapso que agregamos */}
        <main className="flex-1 p-4">{children}</main>
      </div>
    </div>
  );
}
