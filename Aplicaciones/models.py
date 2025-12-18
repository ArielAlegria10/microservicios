from django.db import models
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# =====================
# SUCURSAL Y USUARIO
# =====================
class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("El usuario debe tener un username")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('rol', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    nombre = models.CharField(max_length=150)
    apellido = models.CharField(max_length=150, blank=True, null=True)
    cedula = models.CharField(max_length=20, blank=True, null=True)
    rol = models.CharField(max_length=50, default='user')
    sucursal = models.ForeignKey('Sucursal', on_delete=models.SET_NULL, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['nombre']

    def __str__(self):
        return f"{self.username} ({self.rol})"


# =====================
# CAJA Y CIERRE
# =====================
class Caja(models.Model):
    ESTADO_CHOICES = [('Activo', 'Activo'), ('Inactivo', 'Inactivo')]
    nombre = models.CharField(max_length=50)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    responsable = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Activo')

    def __str__(self):
        resp = f' - {self.responsable}' if self.responsable else ''
        return f'{self.nombre} ({self.sucursal.nombre}){resp}'

    @property
    def total_subtotal(self):
        return sum(v.subtotal for v in self.ventas.filter(reembolso=False))

    @property
    def total_comisiones(self):
        return sum(v.comision_total for v in self.ventas.filter(reembolso=False))

    @property
    def total_iva(self):
        return sum(v.total_iva_detalles for v in self.ventas.filter(reembolso=False))

    @property
    def total_reembolsos(self):
        return sum(r.monto for r in self.reembolsos.all())

    @property
    def total_neto(self):
        return self.total_subtotal + self.total_comisiones + self.total_iva - self.total_reembolsos


class CierreCaja(models.Model):
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name='cierres')
    fecha = models.DateTimeField(default=timezone.now)
    total_ventas = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_comision = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_iva = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_recibido = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_vuelto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Cierre Caja {self.caja.nombre} - {self.fecha.date()}"

    def fecha_formateada(self):
        return self.fecha.strftime('%d/%m/%Y %H:%M')


# =====================
# MÉTODO DE PAGO
# =====================
class MetodoPago(models.Model):
    ESTADO_CHOICES = [('Activo', 'Activo'), ('Inactivo', 'Inactivo')]
    descripcion = models.CharField(max_length=100)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Activo')
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.descripcion} ({self.estado})"


# =====================
# COMISIÓN
# =====================
class Comision(models.Model):
    desde = models.DecimalField(max_digits=10, decimal_places=2)
    hasta = models.DecimalField(max_digits=10, decimal_places=2)
    comision_banco = models.DecimalField(max_digits=10, decimal_places=2)
    comision_local = models.DecimalField(max_digits=10, decimal_places=2)
    extra_local = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.desde} - {self.hasta}"


# =====================
# VENTA Y DETALLE
# =====================
class Venta(models.Model):
    cedula = models.CharField(max_length=13, blank=True, null=True)
    nombre = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    vendedor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    plataforma = models.CharField(max_length=100, blank=True, null=True)
    caja = models.ForeignKey(Caja, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    comision = models.ForeignKey(Comision, on_delete=models.SET_NULL, null=True, blank=True)
    cerrado_en = models.ForeignKey(CierreCaja, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas_cerradas')
    reembolso = models.BooleanField(default=False)
    monto_reembolso = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        cliente = f"{self.nombre} ({self.cedula})" if self.nombre else "Cliente no registrado"
        return f"Venta #{self.id} - Total: {self.total_con_comision:.2f} - {cliente}"

    @property
    def subtotal(self):
        return sum(det.subtotal for det in self.detalles.all())

    @property
    def total_iva_detalles(self):
        return sum(det.iva for det in self.detalles.all())

    @property
    def comision_total(self):
        return sum(det.comision for det in self.detalles.all())

    @property
    def total(self):
        return self.subtotal + self.total_iva_detalles

    @property
    def total_con_comision(self):
        return self.total + self.comision_total

    @property
    def total_pagado(self):
        return sum(p.monto_pagado for p in self.pagos.all())

    @property
    def vuelto(self):
        return self.total_pagado - self.total_con_comision


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    comision = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    plataforma = models.CharField(max_length=50, blank=True, null=True)

    IVA_PERCENT = Decimal('0.15')

    @property
    def subtotal(self):
        return self.cantidad * self.precio

    @property
    def iva(self):
        return self.comision * self.IVA_PERCENT

    @property
    def total_con_comision(self):
        return self.subtotal + self.comision + self.iva

    def __str__(self):
        return f"{self.producto} x{self.cantidad} - Total: {self.total_con_comision:.2f}"


class Pago(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='pagos')
    metodo = models.ForeignKey(MetodoPago, on_delete=models.CASCADE)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.metodo.descripcion}: {self.monto_pagado}"


# =====================
# REEMBOLSO
# =====================
class Reembolso(models.Model):
    TIPO_CHOICES = [
        ("Reembolso", "Reembolso"),
        ("Transferencia", "Transferencia"),
        ("Deposito", "Depósito"),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="Reembolso")
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name='reembolsos')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='reembolsos')
    cierre_caja = models.ForeignKey(CierreCaja, on_delete=models.SET_NULL, null=True, blank=True, related_name='reembolsos')
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    motivo = models.TextField(blank=True)
    fecha = models.DateField(auto_now_add=True)
    imagen = models.ImageField(upload_to='consultorio/reembolsos/', blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - ${self.monto:.2f} - {self.sucursal.nombre}"
