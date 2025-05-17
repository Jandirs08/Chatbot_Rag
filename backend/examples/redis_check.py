#!/usr/bin/env python
"""Script para verificar la conexión a Redis y proporcionar información diagnóstica."""
import sys
import os
import time
from pathlib import Path
import redis

# Agregar el directorio raíz al path para importaciones
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.config import settings

def check_redis_connection():
    """Verifica la conexión a Redis y proporciona información de diagnóstico."""
    print("\n=== Redis Connection Checker ===")
    print("Este script verifica la conexión a Redis y proporciona información diagnóstica.")
    
    # Verificar configuración
    print("\n[1] Verificando configuración de Redis...")
    if not hasattr(settings, 'redis_url') or not settings.redis_url:
        print("❌ No se encontró URL de Redis en la configuración.")
        print("   - Asegúrate de definir REDIS_URL en tu archivo .env")
        print("   - Ejemplo: REDIS_URL=redis://localhost:6379/0")
        return False
    
    redis_url = settings.redis_url.get_secret_value()
    print(f"✅ URL de Redis configurada: {redis_url}")
    
    # Intentar conexión
    print("\n[2] Intentando conexión a Redis...")
    try:
        start_time = time.time()
        redis_client = redis.from_url(redis_url, socket_connect_timeout=2.0)
        ping_result = redis_client.ping()
        end_time = time.time()
        
        if ping_result:
            print(f"✅ Conexión exitosa a Redis ({(end_time - start_time) * 1000:.2f}ms)")
            
            # Información del servidor
            print("\n[3] Información del servidor Redis:")
            info = redis_client.info()
            print(f"   - Versión: {info.get('redis_version', 'Desconocida')}")
            print(f"   - Modo: {info.get('redis_mode', 'Standalone')}")
            print(f"   - Memoria usada: {int(info.get('used_memory', 0)) / (1024*1024):.2f} MB")
            print(f"   - Clientes conectados: {info.get('connected_clients', 0)}")
            print(f"   - Tiempo de actividad: {info.get('uptime_in_seconds', 0) / 3600:.1f} horas")
            
            # Probar operaciones básicas
            print("\n[4] Probando operaciones básicas...")
            # Set
            set_start = time.time()
            redis_client.set('test_key', 'test_value', ex=60)
            set_end = time.time()
            print(f"   - SET: ✅ ({(set_end - set_start) * 1000:.2f}ms)")
            
            # Get
            get_start = time.time()
            value = redis_client.get('test_key')
            get_end = time.time()
            if value == b'test_value':
                print(f"   - GET: ✅ ({(get_end - get_start) * 1000:.2f}ms)")
            else:
                print(f"   - GET: ❌ (valor incorrecto: {value})")
            
            # Delete
            del_start = time.time()
            redis_client.delete('test_key')
            del_end = time.time()
            print(f"   - DEL: ✅ ({(del_end - del_start) * 1000:.2f}ms)")
            
            print("\n✅ Redis está funcionando correctamente.")
            return True
            
    except redis.RedisError as e:
        print(f"❌ Error al conectar a Redis: {str(e)}")
        
        # Consejos para solucionar
        print("\n[!] Posibles soluciones:")
        print("   1. Asegúrate de que el servicio Redis esté en ejecución")
        print("   2. Verifica que el host y puerto sean correctos")
        print("   3. Si Redis está en otro servidor, verifica la configuración de firewall")
        print("   4. Para Windows, considera usar Redis a través de WSL o Docker")
        
        if "localhost" in redis_url and "Windows" in os.environ.get('OS', ''):
            print("\n[i] En Windows, puedes instalar Redis así:")
            print("   - Opción 1: Descargar Redis para Windows de https://github.com/microsoftarchive/redis/releases")
            print("   - Opción 2: Usar Docker: docker run --name redis -p 6379:6379 -d redis")
        
        return False

if __name__ == "__main__":
    check_redis_connection() 