import { SidebarTrigger } from "./ui/sidebar";

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen flex w-full bg-gradient-to-br from-background via-muted/30 to-secondary/10">
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
