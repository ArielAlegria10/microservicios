from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

Usuario = get_user_model()

class Command(BaseCommand):
    help = 'Crea los usuarios de la tabla (wcofre, acollaguazo, vargas, etc.)'
    
    def handle(self, *args, **options):
        # Importar Sucursal desde tu app Aplicaciones
        try:
            from Aplicaciones.models import Sucursal
        except ImportError:
            self.stdout.write(self.style.ERROR("❌ No se pudo importar el modelo Sucursal"))
            self.stdout.write("   Verifica que exista en Aplicaciones/models.py")
            return
        
        # Datos de usuarios de la tabla
        usuarios_tabla = [
            # (nombre, apellido, username_admin, username_recaudador, password, rol)
            ('Cofre Guanotas', 'Wiliam Patricio', 'wcofre', 'wcofre', '26986352', 'admin'),
            ('Aracelly Mishel', 'Collaguazo', 'acollaguazo', None, 'acollaguazo123', 'admin'),
            ('Rosa Thalia', 'Vargas Vivas', 'vargas', None, 'vargas123', 'admin'),
            ('Olga María', 'Tipanluisa Pilla', 'otipanluisa', 'Caja005', 'otipanluisa123', 'admin'),
            ('Paola Daniela', 'Padilla Almeida', 'ppadilla', 'Caja005', 'ppadilla123', 'admin'),
            ('Joselyn Pamela', 'Cofre Tipan', 'jcofre', 'Caja005', 'jcofre123', 'admin'),
            ('Johan Sebastian', 'Quilumba', 'jquilumba', 'Caja005', 'jquilumba123', 'admin'),
            ('Esthela Maribel', 'Pullotasig', 'epullotasig', 'Caja005', 'epullotasig123', 'admin'),
            ('Rita del Pilar', 'Mallitasig', 'mallitasig', 'Caja005', 'mallitasig123', 'admin'),
            ('Joselin Concepcion', 'Coba', 'jcoba', 'Caja005', 'jcoba123', 'admin'),
            ('Kevin Alexander', 'Lara Quilumba', 'klara', 'Caja005', 'klara123', 'admin'),
            ('Katherine Patricia', 'Cofre', 'kcofre', 'Caja005', 'kcofre123', 'admin'),
        ]
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('CREANDO USUARIOS DESDE TABLA'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # 1. Verificar o crear sucursal
        sucursal_default = Sucursal.objects.first()
        if not sucursal_default:
            self.stdout.write(self.style.WARNING("⚠️ No hay sucursales. Creando una..."))
            sucursal_default = Sucursal.objects.create(
                nombre="Sucursal Principal",
                direccion="Dirección principal"
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Sucursal creada: {sucursal_default.nombre}"))
        
        usuarios_creados = 0
        usuarios_actualizados = 0
        
        with transaction.atomic():
            for nombre, apellido, username_admin, username_recaudador, password, rol in usuarios_tabla:
                try:
                    # CREAR USUARIO ADMIN
                    if Usuario.objects.filter(username=username_admin).exists():
                        # Actualizar usuario existente
                        usuario = Usuario.objects.get(username=username_admin)
                        usuario.nombre = nombre
                        usuario.apellido = apellido
                        usuario.rol = rol
                        usuario.sucursal = sucursal_default
                        usuario.set_password(password)
                        usuario.is_staff = True  # Admin puede entrar al admin de Django
                        usuario.save()
                        usuarios_actualizados += 1
                        self.stdout.write(self.style.WARNING(f"🔄 Admin actualizado: {username_admin}"))
                    else:
                        # Crear nuevo usuario
                        usuario = Usuario.objects.create_user(
                            username=username_admin,
                            password=password,
                            nombre=nombre,
                            apellido=apellido,
                            rol=rol,
                            sucursal=sucursal_default,
                            is_staff=True,  # Todos son admin, pueden entrar al admin
                            is_active=True
                        )
                        usuarios_creados += 1
                        self.stdout.write(self.style.SUCCESS(f"✅ Admin creado: {username_admin}"))
                    
                    # CREAR USUARIO RECAUDADOR (si es diferente del admin)
                    if username_recaudador and username_recaudador != username_admin:
                        if not Usuario.objects.filter(username=username_recaudador).exists():
                            Usuario.objects.create_user(
                                username=username_recaudador,
                                password='Caja005',  # Contraseña fija para recaudadores
                                nombre=nombre,
                                apellido=apellido,
                                rol='user',  # Rol 'user' para recaudadores
                                sucursal=sucursal_default,
                                is_staff=False,  # No pueden entrar al admin
                                is_active=True
                            )
                            usuarios_creados += 1
                            self.stdout.write(self.style.SUCCESS(f"  ✅ Recaudador creado: {username_recaudador}"))
                        else:
                            self.stdout.write(self.style.WARNING(f"  ⚠️ Recaudador ya existe: {username_recaudador}"))
                    
                    # Si es el mismo usuario para ambos roles
                    elif username_recaudador == username_admin:
                        usuario.rol = 'admin'
                        usuario.save()
                        self.stdout.write(f"  ℹ️ Usuario {username_admin} tiene ambos roles")
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error con {username_admin}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f"RESUMEN:"))
        self.stdout.write(self.style.SUCCESS(f"  Usuarios creados: {usuarios_creados}"))
        self.stdout.write(self.style.SUCCESS(f"  Usuarios actualizados: {usuarios_actualizados}"))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Mostrar lista de usuarios
        self.stdout.write("\n📋 LISTA DE USUARIOS:")
        self.stdout.write("-" * 60)
        for usuario in Usuario.objects.all().order_by('rol', 'username'):
            self.stdout.write(f"{usuario.username:15} | {usuario.rol:10} | {usuario.nombre} {usuario.apellido}")