
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FileText, Upload, Trash2, Eye, Search } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";

const mockDocuments = [
  {
    id: 1,
    nombre: "Requisitos_Becas_2024.pdf",
    fecha: "2024-01-15",
    tamaño: "2.3 MB",
    estado: "Procesado"
  },
  {
    id: 2,
    nombre: "Proceso_Postulacion.pdf",
    fecha: "2024-01-10",
    tamaño: "1.8 MB",
    estado: "Procesado"
  },
  {
    id: 3,
    nombre: "FAQ_Becas_Grupo_Romero.pdf",
    fecha: "2024-01-08",
    tamaño: "956 KB",
    estado: "Procesando"
  }
];

export function DocumentManagement() {
  const [documents, setDocuments] = useState(mockDocuments);
  const [searchTerm, setSearchTerm] = useState("");
  const { toast } = useToast();

  const handleUpload = () => {
    toast({
      title: "Función en desarrollo",
      description: "La subida de archivos se implementará con el backend",
    });
  };

  const handleDelete = (id: number) => {
    setDocuments(documents.filter(doc => doc.id !== id));
    toast({
      title: "Documento eliminado",
      description: "El PDF ha sido eliminado del sistema",
    });
  };

  const filteredDocuments = documents.filter(doc =>
    doc.nombre.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-foreground">
          Gestión de Documentos
        </h1>
        <p className="text-xl text-muted-foreground">
          Administra los PDFs que alimentan el conocimiento del bot
        </p>
      </div>

      {/* Controles superiores */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Buscar documentos..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button onClick={handleUpload} className="gradient-primary hover:opacity-90">
          <Upload className="w-4 h-4 mr-2" />
          Subir PDF
        </Button>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Documentos
            </CardTitle>
            <FileText className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{documents.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              PDFs en el sistema
            </p>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Procesados
            </CardTitle>
            <Eye className="h-4 w-4 text-accent" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">
              {documents.filter(doc => doc.estado === "Procesado").length}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Listos para usar
            </p>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Tamaño Total
            </CardTitle>
            <Upload className="h-4 w-4 text-secondary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">5.1 MB</div>
            <p className="text-xs text-muted-foreground mt-1">
              Espacio utilizado
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabla de documentos */}
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle>Documentos Subidos</CardTitle>
          <CardDescription>
            Lista de todos los PDFs procesados por el sistema RAG
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead>Tamaño</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDocuments.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-primary" />
                      {doc.nombre}
                    </div>
                  </TableCell>
                  <TableCell>{doc.fecha}</TableCell>
                  <TableCell>{doc.tamaño}</TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      doc.estado === "Procesado" 
                        ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                        : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
                    }`}>
                      {doc.estado}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex gap-2 justify-end">
                      <Button variant="outline" size="sm">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => handleDelete(doc.id)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
