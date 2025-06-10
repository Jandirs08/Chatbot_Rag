"use client";

import { AppSidebar } from "./AppSidebar";
import { SidebarProvider, useSidebar } from "./ui/sidebar"; // Import useSidebar
import { Button } from "./ui/button"; // Import Button
import { PanelLeft } from "lucide-react"; // Import PanelLeft icon

export function RootLayoutClient({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <RootLayoutContent>{children}</RootLayoutContent>
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
        <header className="p-4 border-b">
          <Button variant="outline" size="icon" onClick={toggleSidebar}>
            <PanelLeft className="h-5 w-5" />
            <span className="sr-only">Toggle Sidebar</span>
          </Button>
        </header>
        <main className="flex-1 p-4">{children}</main>
      </div>
    </div>
  );
}
