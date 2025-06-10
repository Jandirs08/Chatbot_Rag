import React from "react";
import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/app/components/ui/card";
import { Button } from "@/app/components/ui/button";
import { Input } from "@/app/components/ui/input";
import { Label } from "@/app/components/ui/label";
import { Copy, Eye, MessageCircle } from "lucide-react";
import { useToast } from "@/app/hooks/use-toast";
import { FloatingChatWidget } from "./FloatingChatWidget";

export function WidgetPreview() {
  const widgetUrl =
    process.env.NEXT_PUBLIC_VITE_WIDGET_URL ||
    "https://widget.becas-grupo-romero.com/chat";

  const { toast } = useToast();

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-foreground">Widget del Bot</h1>
        <p className="text-xl text-muted-foreground">
          Previsualiza y obtén el código para incrustar el chatbot
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Vista previa */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5 text-primary" />
              Vista Previa
            </CardTitle>
            <CardDescription>
              Así se verá el bot en tu sitio web
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative bg-gradient-to-br from-muted/30 to-secondary/10 p-8 rounded-lg min-h-[400px] border border-border/30">
              {/* Simulación de una página web */}

              <div className="space-y-4 text-sm text-muted-foreground">
                <div className="h-4 bg-muted rounded w-3/4"></div>
                <div className="h-4 bg-muted rounded w-1/2"></div>
                <div className="h-4 bg-muted rounded w-5/6"></div>
                <div className="h-16 bg-muted rounded"></div>
                <div className="h-4 bg-muted rounded w-2/3"></div>
              </div>

              {/* Directamente renderizar FloatingChatWidget */}
              <div className="absolute bottom-4 right-4">
                <FloatingChatWidget />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Código del iframe */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Copy className="w-5 h-5 text-primary" />
              Código para Incrustar
            </CardTitle>
            <CardDescription>
              Copia este código y pégalo en tu sitio web
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="iframe-code">Código iframe</Label>
              <div className="relative mt-2">
                <textarea
                  id="iframe-code"
                  value={widgetUrl}
                  className="w-full h-32 p-3 text-sm border border-border rounded-md bg-background font-mono resize-none"
                  readOnly
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Instrucciones */}
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Instrucciones de Instalación</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 border border-border/30 rounded-lg">
              <div className="w-10 h-10 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center mx-auto mb-3">
                1
              </div>
              <h3 className="font-semibold mb-2">Copia el código</h3>
              <p className="text-sm text-muted-foreground">
                Haz clic en el botón copiar para obtener el código iframe
              </p>
            </div>
            <div className="text-center p-4 border border-border/30 rounded-lg">
              <div className="w-10 h-10 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center mx-auto mb-3">
                2
              </div>
              <h3 className="font-semibold mb-2">Pega en tu web</h3>
              <p className="text-sm text-muted-foreground">
                Inserta el código en el HTML de tu sitio web
              </p>
            </div>
            <div className="text-center p-4 border border-border/30 rounded-lg">
              <div className="w-10 h-10 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center mx-auto mb-3">
                3
              </div>
              <h3 className="font-semibold mb-2">¡Listo!</h3>
              <p className="text-sm text-muted-foreground">
                El chatbot aparecerá como una burbuja flotante
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
