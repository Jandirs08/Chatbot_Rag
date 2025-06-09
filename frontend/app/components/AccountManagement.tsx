
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User, Mail, Key, Shield } from "lucide-react";

export function AccountManagement() {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-foreground">
          Gestión de Cuenta
        </h1>
        <p className="text-xl text-muted-foreground">
          Administra tu acceso y configuración personal
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Información personal */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5 text-primary" />
              Información Personal
            </CardTitle>
            <CardDescription>
              Actualiza tus datos de perfil
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name">Nombre completo</Label>
              <Input
                id="name"
                defaultValue="Administrador Becas"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="email">Correo electrónico</Label>
              <Input
                id="email"
                type="email"
                defaultValue="admin@becas-grupo-romero.com"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="role">Rol</Label>
              <Input
                id="role"
                defaultValue="Administrador"
                disabled
                className="mt-1 bg-muted"
              />
            </div>
            <Button className="w-full gradient-primary hover:opacity-90">
              Actualizar Información
            </Button>
          </CardContent>
        </Card>

        {/* Seguridad */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="w-5 h-5 text-primary" />
              Seguridad
            </CardTitle>
            <CardDescription>
              Gestiona tu contraseña y seguridad
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="current-password">Contraseña actual</Label>
              <Input
                id="current-password"
                type="password"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="new-password">Nueva contraseña</Label>
              <Input
                id="new-password"
                type="password"
                className="mt-1"
              />
            </div>
            <div>
              <Label htmlFor="confirm-password">Confirmar contraseña</Label>
              <Input
                id="confirm-password"
                type="password"
                className="mt-1"
              />
            </div>
            <Button variant="outline" className="w-full">
              Cambiar Contraseña
            </Button>
          </CardContent>
        </Card>

        {/* Sesión actual */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Sesión Actual
            </CardTitle>
            <CardDescription>
              Información sobre tu sesión activa
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Último acceso:</span>
                <span>Hoy, 14:30</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">IP de acceso:</span>
                <span>192.168.1.100</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Dispositivo:</span>
                <span>Chrome en Windows</span>
              </div>
            </div>
            <Button variant="outline" className="w-full text-destructive hover:text-destructive">
              Cerrar Sesión
            </Button>
          </CardContent>
        </Card>

        {/* Configuración de notificaciones */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-primary" />
              Notificaciones
            </CardTitle>
            <CardDescription>
              Configura qué notificaciones recibir
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-sm text-muted-foreground">
              <p className="mb-4">Próximamente: Configuración de notificaciones por email para:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>Nuevos documentos procesados</li>
                <li>Errores en el bot</li>
                <li>Actualizaciones del sistema</li>
                <li>Reportes semanales de uso</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
