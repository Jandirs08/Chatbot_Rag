"use client";

import { Bot, FileText, Settings, BarChart3, Code, User } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  useSidebar,
} from "@/components/ui/sidebar";

const menuItems = [
  {
    title: "Dashboard",
    url: "/",
    icon: BarChart3,
  },
  {
    title: "Widget",
    url: "/widget",
    icon: Code,
  },
  {
    title: "Documentos",
    url: "/Documents",
    icon: FileText,
  },
  {
    title: "Configuración",
    url: "/configuracion",
    icon: Settings,
  },
  {
    title: "Cuenta",
    url: "/cuenta",
    icon: User,
  },
];

export function AppSidebar() {
  const { state } = useSidebar();
  return (
    <Sidebar className="border-r border-border/50">
      <SidebarHeader className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg gradient-primary flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div className={state === "collapsed" ? "hidden" : ""}>
            <h2 className="text-lg font-bold text-foreground">RAG Bot</h2>
            <p className="text-sm text-muted-foreground">Becas Grupo Romero</p>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel
            className={
              state === "collapsed" ? "hidden" : "text-primary font-semibold"
            }
          >
            Gestión del Bot
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    className="hover:bg-primary/10 hover:text-primary transition-all duration-200"
                  >
                    <a href={item.url} className="flex items-center gap-3">
                      <item.icon className="w-5 h-5" />
                      {state !== "collapsed" && <span>{item.title}</span>}
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
