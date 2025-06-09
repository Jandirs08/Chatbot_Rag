
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Settings, Save, RotateCcw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function BotConfiguration() {
  const [prompt, setPrompt] = useState(`Eres un asistente virtual especializado en el programa de Becas Grupo Romero. Tu objetivo es ayudar a los estudiantes proporcionando información precisa y útil sobre:

- Requisitos y criterios de elegibilidad para las becas
- Proceso de postulación paso a paso
- Fechas importantes y plazos
- Documentación necesaria
- Beneficios incluidos en las becas
- Preguntas frecuentes

Mantén un tono amable, profesional y motivador. Si no tienes información específica sobre algo, recomienda contactar directamente con el equipo de Becas Grupo Romero.`);

  const [temperature, setTemperature] = useState([0.7]);
  const { toast } = useToast();

  const handleSave = () => {
    toast({
      title: "Configuración guardada",
      description: "Los cambios han sido aplicados al bot exitosamente",
    });
  };

  const handleReset = () => {
    setPrompt(`Eres un asistente virtual especializado en el programa de Becas Grupo Romero. Tu objetivo es ayudar a los estudiantes proporcionando información precisa y útil sobre:

- Requisitos y criterios de elegibilidad para las becas
- Proceso de postulación paso a paso
- Fechas importantes y plazos
- Documentación necesaria
- Beneficios incluidos en las becas
- Preguntas frecuentes

Mantén un tono amable, profesional y motivador. Si no tienes información específica sobre algo, recomienda contactar directamente con el equipo de Becas Grupo Romero.`);
    setTemperature([0.7]);
    toast({
      title: "Configuración restablecida",
      description: "Se han restaurado los valores por defecto",
    });
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-foreground">
          Configuración del Bot
        </h1>
        <p className="text-xl text-muted-foreground">
          Ajusta el comportamiento y personalidad del chatbot
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Configuración principal */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-primary" />
                Prompt del Sistema
              </CardTitle>
              <CardDescription>
                Define la personalidad y contexto del bot para las conversaciones
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="system-prompt">Instrucciones del Sistema</Label>
                <Textarea
                  id="system-prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="mt-2 min-h-[300px] font-mono text-sm"
                  placeholder="Escribe las instrucciones para el bot..."
                />
                <p className="text-xs text-muted-foreground mt-2">
                  Caracteres: {prompt.length}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/50">
            <CardHeader>
              <CardTitle>Temperatura del Modelo</CardTitle>
              <CardDescription>
                Controla la creatividad vs precisión en las respuestas (0 = más preciso, 1 = más creativo)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-4">
                  <Label>Temperatura: {temperature[0].toFixed(1)}</Label>
                  <span className="text-sm text-muted-foreground">
                    {temperature[0] < 0.3 ? "Muy Preciso" : 
                     temperature[0] < 0.7 ? "Balanceado" : "Creativo"}
                  </span>
                </div>
                <Slider
                  value={temperature}
                  onValueChange={setTemperature}
                  max={1}
                  min={0}
                  step={0.1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-2">
                  <span>Preciso</span>
                  <span>Creativo</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Panel lateral */}
        <div className="space-y-6">
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle>Estado del Bot</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-950/20 rounded-lg border border-green-200 dark:border-green-800">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-green-800 dark:text-green-200">Activo</span>
                </div>
              </div>
              <div className="text-sm text-muted-foreground space-y-1">
                <p>Última actualización: Hace 5 min</p>
                <p>Documentos procesados: 3</p>
                <p>Consultas hoy: 247</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/50">
            <CardHeader>
              <CardTitle>Acciones</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button onClick={handleSave} className="w-full gradient-primary hover:opacity-90">
                <Save className="w-4 h-4 mr-2" />
                Guardar Cambios
              </Button>
              <Button onClick={handleReset} variant="outline" className="w-full">
                <RotateCcw className="w-4 h-4 mr-2" />
                Restablecer
              </Button>
            </CardContent>
          </Card>

          <Card className="border-border/50 bg-muted/30">
            <CardHeader>
              <CardTitle className="text-sm">Recomendaciones</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground space-y-2">
              <p>• Usa un prompt claro y específico</p>
              <p>• Temperatura baja (0.3-0.5) para respuestas más consistentes</p>
              <p>• Incluye ejemplos de cómo debe responder</p>
              <p>• Define límites claros de conocimiento</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
