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
import { Copy, Eye, MessageCircle, X } from "lucide-react";
import { useToast } from "@/app/components/ui/use-toast";

export function WidgetPreview() {
  const [width, setWidth] = useState("400");
  const [height, setHeight] = useState("600");
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [iframeCode, setIframeCode] = useState(
    `<iframe src="${process.env.NEXT_PUBLIC_VITE_WIDGET_URL}" width="${width}" height="${height}" frameborder="0" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.1);"></iframe>`,
  );
  const { toast } = useToast();

  const copyToClipboard = () => {
    navigator.clipboard.writeText(iframeCode);
    toast({
      title: "Código copiado",
      description: "El código del iframe ha sido copiado al portapapeles",
    });
  };

  const updateIframeCode = (newWidth: string, newHeight: string) => {
    setIframeCode(
      `<iframe src="${process.env.NEXT_PUBLIC_VITE_WIDGET_URL}" width="${newWidth}" height="${newHeight}" frameborder="0" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.1);"></iframe>`,
    );
  };

  const handleWidthChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newWidth = e.target.value;
    setWidth(newWidth);
    updateIframeCode(newWidth, height);
  };

  const handleHeightChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newHeight = e.target.value;
    setHeight(newHeight);
    updateIframeCode(width, newHeight);
  };

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
              {!isPreviewOpen && (
                <div className="space-y-4 text-sm text-muted-foreground">
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                  <div className="h-4 bg-muted rounded w-1/2"></div>
                  <div className="h-4 bg-muted rounded w-5/6"></div>
                  <div className="h-16 bg-muted rounded"></div>
                  <div className="h-4 bg-muted rounded w-2/3"></div>
                </div>
              )}

              {/* Widget flotante simulado */}
              {!isPreviewOpen && (
                <div
                  className="absolute bottom-4 right-4 w-16 h-16 rounded-full gradient-primary flex items-center justify-center shadow-lg hover:scale-110 transition-transform cursor-pointer"
                  onClick={() => setIsPreviewOpen(true)}
                >
                  <MessageCircle className="w-8 h-8 text-white" />
                </div>
              )}

              {/* Vista previa del iframe */}
              {isPreviewOpen && (
                <div
                  className="absolute inset-0 flex items-center justify-center z-50"
                  style={{ width: "100%", height: "100%" }}
                >
                  <div
                    className="relative"
                    style={{ width: `${width}px`, height: `${height}px` }}
                  >
                    <iframe
                      src={process.env.NEXT_PUBLIC_VITE_WIDGET_URL}
                      width={width}
                      height={height}
                      style={{
                        border: "none",
                        borderRadius: "16px",
                        boxShadow: "0 8px 32px rgba(0,0,0,0.1)",
                      }}
                    />
                    <button
                      onClick={() => setIsPreviewOpen(false)}
                      className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-destructive text-white flex items-center justify-center shadow-md z-50 hover:bg-destructive/90 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
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
                  value={iframeCode}
                  onChange={(e) => setIframeCode(e.target.value)}
                  className="w-full h-32 p-3 text-sm border border-border rounded-md bg-background font-mono resize-none"
                  readOnly
                />
                <Button
                  size="sm"
                  onClick={copyToClipboard}
                  className="absolute top-2 right-2 gradient-primary hover:opacity-90"
                >
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="width">Ancho (px)</Label>
                <Input
                  id="width"
                  type="number"
                  value={width}
                  onChange={handleWidthChange}
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="height">Alto (px)</Label>
                <Input
                  id="height"
                  type="number"
                  value={height}
                  onChange={handleHeightChange}
                  className="mt-1"
                />
              </div>
            </div>

            <Button
              className="w-full gradient-primary hover:opacity-90"
              onClick={() =>
                toast({
                  title: "Vista previa actualizada",
                  description: "Los cambios se han aplicado a la vista previa",
                })
              }
            >
              Actualizar Vista Previa
            </Button>
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
