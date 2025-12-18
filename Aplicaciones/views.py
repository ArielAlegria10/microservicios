from email import parser
from reportlab.lib.styles import getSampleStyleSheet
from django.template.loader import render_to_string
from reportlab.platypus import Table, TableStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from django.http import JsonResponse
from django.utils.timezone import make_naive
from django.core.paginator import Paginator
from functools import wraps
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from django.db.models import Q
from pydoc import html
import re
from django.utils import timezone
from time import localtime
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.template.loader import get_template
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils.timezone import localdate
from datetime import datetime, date, time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from django.utils.timezone import now
from dateutil import parser as date_parser


from .models import (
    Pago, Venta, DetalleVenta, Sucursal, Usuario, MetodoPago,
    Caja, Comision, Reembolso, CierreCaja, 
)

# =====================
# Decorador de roles
# =====================
def rol_required(roles_permitidos):
    """
    Decorador que valida roles permitidos.
    El administrador puede entrar a TODO automáticamente.
    El rol 'user' solo puede acceder a ventas, cajas y reembolsos.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # Validación autenticación
            if not request.user.is_authenticated:
                return redirect('login')

            # ADMIN → acceso total sin restricciones
            if getattr(request.user, 'rol', None) == 'admin':
                return view_func(request, *args, **kwargs)

            # CAJERO → acceso a casi todo excepto gestión de usuarios
            if request.user.rol == 'cajero':
                # Cajero no puede gestionar usuarios
                if view_func.__name__ in ['listado_usuarios', 'nuevo_usuario', 'editar_usuario', 'eliminar_usuario']:
                    messages.error(request, "No tienes permiso para acceder a esta página.")
                    return redirect('index')
                return view_func(request, *args, **kwargs)

            # USER → solo ventas, cajas y reembolsos
            if request.user.rol == 'user':
                # Lista de funciones permitidas para usuarios normales
                funciones_permitidas_user = [
                    'index', 'listado_ventas', 'nueva_venta', 'editar_venta', 
                    'eliminar_venta', 'detalle_venta_ajax', 'imprimir_venta',
                    'listado_cajas', 'nueva_caja', 'editar_caja', 'eliminar_caja',
                    'listado_reembolsos', 'nuevo_reembolso', 'editar_reembolso',
                    'eliminar_reembolso', 'cierre_caja', 'vista_cierre_caja',
                    'imprimir_cierre_caja', 'reporte_diario_pdf_tabla'
                ]
                
                if view_func.__name__ in funciones_permitidas_user:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, "No tienes permiso para acceder a esta página. Tu rol solo permite gestionar ventas, cajas y reembolsos.")
                    return redirect('index')

            # Validar si el usuario tiene el rol permitido
            if hasattr(request.user, 'rol') and request.user.rol in roles_permitidos:
                return view_func(request, *args, **kwargs)

            # Si no tiene permiso
            messages.error(request, "No tienes permiso para acceder a esta página.")
            return redirect('index')

        return wrapper
    return decorator

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('index')  # Cambia si tu página de inicio se llama diferente
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login') 

# =====================
# INDEX
# =====================
@rol_required(['cajero', 'user'])
def index(request):
    return render(request, 'index.html')
def parse_decimal_safe(value, default=Decimal('0.00')):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return default


@rol_required(['cajero', 'user'])
def listado_ventas(request):
    query = request.GET.get('q', '')

    # Queryset principal con prefeteched
    ventas_queryset = Venta.objects.all().prefetch_related('detalles', 'pagos__metodo')

    # Filtro de búsqueda
    if query:
        ventas_queryset = ventas_queryset.filter(
            Q(nombre__icontains=query) |
            Q(cedula__icontains=query) |
            Q(descripcion__icontains=query)
        )

    # Agregamos campos calculados directamente al diccionario
    ventas_con_totales = []
    for venta in ventas_queryset:
        subtotal = Decimal('0')
        comision_total = Decimal('0')
        total_iva_detalles = Decimal('0')
        total_con_comision = Decimal('0')
        detalles_con_totales = []

        for det in venta.detalles.all():
            precio = det.precio or Decimal('0')
            cantidad = det.cantidad or Decimal('0')
            comision = det.comision or Decimal('0')

            subtotal_producto = precio * cantidad
            iva_producto = comision * Decimal('0.15')
            total_producto = subtotal_producto + comision + iva_producto

            subtotal += subtotal_producto
            comision_total += comision
            total_iva_detalles += iva_producto
            total_con_comision += total_producto

            detalles_con_totales.append({
                'producto': det.producto.nombre if hasattr(det.producto, 'nombre') else str(det.producto),
                'cantidad': cantidad,
                'precio': precio,
                'comision': comision,
                'iva': iva_producto,
                'total': total_producto,
                'plataforma': det.plataforma,
            })

        total_pagado = sum([p.monto_pagado for p in venta.pagos.all()]) if venta.pagos.exists() else Decimal('0')
        vuelto = total_pagado - total_con_comision

        ventas_con_totales.append({
            'venta': venta,  # objeto completo, para que template use venta.id
            'subtotal': subtotal,
            'comision_total': comision_total,
            'total_iva_detalles': total_iva_detalles,
            'total_con_comision': total_con_comision,
            'detalles_con_totales': detalles_con_totales,
            'total_pagado': total_pagado,
            'vuelto': vuelto,
        })

    # Paginación
    paginator = Paginator(ventas_con_totales, 10)
    page_number = request.GET.get('page')
    ventas_page = paginator.get_page(page_number)

    context = {
        'ventas': ventas_page,
        'query': query,
    }
    return render(request, 'listado_ventas.html', context)


@rol_required(['cajero', 'user'])
def nueva_venta(request):
    if request.method == "POST":
        try:
            # DATOS PRINCIPALES
            cedula = request.POST.get("txt_cedula")
            nombre = request.POST.get("txt_nombre")
            descripcion = request.POST.get("txt_descripcion")
            plataforma = request.POST.get("plataforma", "")
            caja_id = request.POST.get("select_caja")
            sucursal_id = request.POST.get("select_sucursal")

            caja = Caja.objects.filter(id=caja_id).first() if caja_id else None
            sucursal = Sucursal.objects.filter(id=sucursal_id).first() if sucursal_id else None

            venta = Venta.objects.create(
                cedula=cedula,
                nombre=nombre,
                descripcion=descripcion,
                plataforma=plataforma,
                caja=caja,
                sucursal=sucursal,
                reembolso=False
            )

            # DETALLES
            i = 0
            while f'productos[{i}][nombre]' in request.POST:
                nombre_producto = request.POST.get(f'productos[{i}][nombre]').strip()
                precio = parse_decimal_safe(request.POST.get(f'productos[{i}][precio]', '0'))
                cantidad = parse_decimal_safe(request.POST.get(f'productos[{i}][cantidad]', '1'))
                plataforma_producto = request.POST.get(f'productos[{i}][plataforma]', '').strip()
                comision = precio * Decimal('0.01')  # ejemplo: 1%

                if nombre_producto:
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=nombre_producto,
                        cantidad=cantidad,
                        precio=precio,
                        comision=comision,
                        plataforma=plataforma_producto
                    )
                i += 1

            # PAGOS
            for key, value in request.POST.items():
                if key.startswith("pagos[") and value:
                    metodo_id = key.split("[")[1].split("]")[0]
                    monto = parse_decimal_safe(value)
                    if monto > 0:
                        metodo = MetodoPago.objects.filter(id=metodo_id).first()
                        if metodo:
                            Pago.objects.create(
                                venta=venta,
                                metodo=metodo,
                                monto_pagado=monto
                            )

            messages.success(request, f"Venta #{venta.id} creada correctamente.")
            return redirect("listado_ventas")

        except Exception as e:
            messages.error(request, f"Error al registrar la venta: {str(e)}")
            return redirect("nueva_venta")

    # GET request
    context = {
        "metodos_pago": MetodoPago.objects.filter(estado="Activo"),
        "cajas": Caja.objects.filter(estado="Activo"),
        "sucursales": Sucursal.objects.all(),
    }
    return render(request, "nueva_venta.html", context)


@rol_required(['cajero', 'user'])
def editar_venta(request, id):
    venta = get_object_or_404(Venta, id=id)

    if request.method == 'POST':
        # CAMPOS GENERALES
        venta.cedula = request.POST.get('txt_cedula', '').strip()
        venta.nombre = request.POST.get('txt_nombre', '').strip()
        venta.descripcion = request.POST.get('txt_descripcion', '').strip()
        venta.caja = Caja.objects.filter(id=request.POST.get('select_caja')).first()
        venta.sucursal = Sucursal.objects.filter(id=request.POST.get('select_sucursal')).first()
        venta.save()

        # DETALLES
        venta.detalles.all().delete()
        i = 0
        while f'productos[{i}][nombre]' in request.POST:
            nombre = request.POST.get(f'productos[{i}][nombre]').strip()
            cantidad = parse_decimal_safe(request.POST.get(f'productos[{i}][cantidad]', '1'))
            precio = parse_decimal_safe(request.POST.get(f'productos[{i}][precio]', '0'))
            comision = parse_decimal_safe(request.POST.get(f'productos[{i}][comision]', '0'))
            plataforma = request.POST.get(f'productos[{i}][plataforma]', '').strip()

            if nombre:
                venta.detalles.create(
                    producto=nombre,
                    cantidad=cantidad,
                    precio=precio,
                    comision=comision,
                    plataforma=plataforma
                )
            i += 1

        # PAGOS
        venta.pagos.all().delete()
        for metodo in MetodoPago.objects.all():
            monto = parse_decimal_safe(request.POST.get(f'pagos[{metodo.id}][monto]', '0'))
            if monto > 0:
                Pago.objects.create(
                    venta=venta,
                    metodo=metodo,
                    monto_pagado=monto
                )

        messages.success(request, "Venta actualizada correctamente")
        return redirect('listado_ventas')

    context = {
        'venta': venta,
        'sucursales': Sucursal.objects.all(),
        'usuarios': Usuario.objects.all(),
        'metodos_pago': MetodoPago.objects.all(),
        'cajas': Caja.objects.all(),
        'detalles': venta.detalles.all(),
        'pagos_dict': {p.metodo.id: p.monto_pagado for p in venta.pagos.all()},
    }
    return render(request, 'editar_venta.html', context)


@rol_required(['cajero', 'user'])
def eliminar_venta(request, id):
    venta = get_object_or_404(Venta, id=id)
    venta.delete()
    messages.success(request, "Venta eliminada correctamente")
    return redirect('listado_ventas')

# =====================
# CRUD SUCURSAL - SOLO ADMIN
# =====================
@rol_required(['admin'])
def listado_sucursales(request):
    return render(request, 'listado_sucursales.html', {'sucursales': Sucursal.objects.all()})

@rol_required(['admin'])
def nueva_sucursal(request):
    if request.method == 'POST':
        Sucursal.objects.create(
            nombre=request.POST['txt_nombre'],
            direccion=request.POST['txt_direccion']
        )
        messages.success(request, "Sucursal creada correctamente")
        return redirect('listado_sucursales')
    return render(request, 'nueva_sucursal.html')

@rol_required(['admin'])
def editar_sucursal(request, id):
    sucursal = get_object_or_404(Sucursal, id=id)
    if request.method == 'POST':
        sucursal.nombre = request.POST['txt_nombre']
        sucursal.direccion = request.POST['txt_direccion']
        sucursal.save()
        messages.success(request, "Sucursal actualizada correctamente")
        return redirect('listado_sucursales')
    return render(request, 'editar_sucursal.html', {'sucursal': sucursal})

@rol_required(['admin'])
def eliminar_sucursal(request, id):
    sucursal = get_object_or_404(Sucursal, id=id)
    sucursal.delete()
    messages.success(request, "Sucursal eliminada correctamente")
    return redirect('listado_sucursales')





@rol_required(['cajero', 'user'])
def detalle_venta_ajax(request, id):
    venta = get_object_or_404(Venta, id=id)

    # Preparar detalles
    detalles_con_totales = []
    subtotal = comision_total = total_iva_detalles = total_con_comision = 0

    for det in venta.detalles.all():
        precio = det.precio or 0
        cantidad = det.cantidad or 0
        comision = det.comision or 0
        iva = comision * 0.15
        total = precio * cantidad + comision + iva

        subtotal += precio * cantidad
        comision_total += comision
        total_iva_detalles += iva
        total_con_comision += total

        detalles_con_totales.append({
            'producto': det.producto,
            'cantidad': cantidad,
            'precio': precio,
            'comision': comision,
            'iva': iva,
            'total': total,
            'plataforma': det.plataforma,
        })

    total_pagado = sum([p.monto_pagado for p in venta.pagos.all()]) if venta.pagos.exists() else 0
    vuelto = total_pagado - total_con_comision

    context = {
        'venta': venta,
        'detalles': detalles_con_totales,
        'subtotal': subtotal,
        'comision_total': comision_total,
        'total_iva_detalles': total_iva_detalles,
        'total_con_comision': total_con_comision,
        'total_pagado': total_pagado,
        'vuelto': vuelto,
    }

    html = render_to_string("detalle_venta_modal.html", context, request=request)
    return JsonResponse({'html': html})


# =====================
# CRUD USUARIO - SOLO ADMIN
# =====================
@rol_required(['admin'])
def listado_usuarios(request):
    return render(request, 'listado_usuarios.html', {'usuarios': Usuario.objects.all()})

@rol_required(['admin'])
def nuevo_usuario(request):
    if request.method == 'POST':
        usuario = Usuario.objects.create(
            nombre=request.POST['txt_nombre'],
            apellido=request.POST['txt_apellido'],
            cedula=request.POST['txt_cedula'],
            rol=request.POST['select_rol'],
            sucursal=Sucursal.objects.filter(id=request.POST.get('select_sucursal')).first()
        )
        messages.success(request, "Usuario creado correctamente")
        return redirect('listado_usuarios')
    return render(request, 'nuevo_usuario.html', {'sucursales': Sucursal.objects.all()})

@rol_required(['admin'])
def editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    if request.method == 'POST':
        usuario.nombre = request.POST['txt_nombre']
        usuario.apellido = request.POST['txt_apellido']
        usuario.cedula = request.POST['txt_cedula']
        usuario.rol = request.POST['select_rol']
        usuario.sucursal = Sucursal.objects.filter(id=request.POST.get('select_sucursal')).first()
        usuario.save()
        messages.success(request, "Usuario actualizado correctamente")
        return redirect('listado_usuarios')
    return render(request, 'editar_usuario.html', {'usuario': usuario, 'sucursales': Sucursal.objects.all()})

@rol_required(['admin'])
def eliminar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    usuario.delete()
    messages.success(request, "Usuario eliminado correctamente")
    return redirect('listado_usuarios')

# =====================
# CRUD METODO PAGO - ADMIN Y CAJERO (NO USER)
# =====================
@rol_required(['admin', 'cajero'])
def listado_metodopago(request):
    return render(request, 'listado_metodopago.html', {'metodospago': MetodoPago.objects.all()})

@rol_required(['admin', 'cajero'])
def nuevo_metodopago(request):
    if request.method == 'POST':
        descripcion = request.POST.get('txt_descripcion', '').strip()
        estado = request.POST.get('select_estado', 'Activo')
        if not descripcion:
            messages.error(request, "La descripción es obligatoria.")
            return render(request, 'nuevo_metodopago.html')
        MetodoPago.objects.create(descripcion=descripcion, estado=estado)
        messages.success(request, "Método de pago creado correctamente.")
        return redirect('listado_metodopago')
    return render(request, 'nuevo_metodopago.html')

@rol_required(['admin', 'cajero'])
def editar_metodopago(request, id):
    metodo = get_object_or_404(MetodoPago, id=id)
    if request.method == 'POST':
        metodo.descripcion = request.POST['txt_descripcion']
        metodo.estado = request.POST['select_estado']
        metodo.save()
        messages.success(request, "Método de pago actualizado correctamente")
        return redirect('listado_metodopago')
    return render(request, 'editar_metodopago.html', {'metodo': metodo})

@rol_required(['admin', 'cajero'])
def eliminar_metodopago(request, id):
    metodo = get_object_or_404(MetodoPago, id=id)
    metodo.delete()
    messages.success(request, "Método de pago eliminado correctamente")
    return redirect('listado_metodopago')

# =====================
# CRUD CAJA - CAJERO Y USER
# =====================
@rol_required(['cajero', 'user'])
def listado_cajas(request):
    return render(request, 'listado_caja.html', {'cajas': Caja.objects.select_related('sucursal', 'responsable').all()})

@rol_required(['cajero', 'user'])
def nueva_caja(request):
    if request.method == 'POST':
        caja = Caja.objects.create(
            nombre=request.POST.get('txt_nombre', '').strip(),
            estado=request.POST.get('select_estado', 'Activo'),
            sucursal=Sucursal.objects.filter(id=request.POST.get('select_sucursal')).first(),
            responsable=Usuario.objects.filter(id=request.POST.get('select_responsable')).first()
        )
        messages.success(request, f"Caja '{caja.nombre}' creada correctamente.")
        return redirect('listado_cajas')
    context = {'sucursales': Sucursal.objects.all(), 'usuarios': Usuario.objects.all()}
    return render(request, 'nueva_caja.html', context)

@rol_required(['cajero', 'user'])
def editar_caja(request, caja_id):
    caja = get_object_or_404(Caja, id=caja_id)

    if request.method == 'POST':
        caja.nombre = request.POST.get('txt_nombre')
        caja.estado = request.POST.get('select_estado')

        sucursal_id = request.POST.get('select_sucursal')
        responsable_id = request.POST.get('select_responsable')

        caja.sucursal = (
            Sucursal.objects.get(id=sucursal_id)
            if sucursal_id else None
        )

        caja.responsable = (
            Usuario.objects.get(id=responsable_id)
            if responsable_id else None
        )

        caja.save()
        messages.success(request, "Caja actualizada correctamente")
        return redirect('listado_cajas')

    return render(request, 'editar_caja.html', {
        'caja': caja,
        'sucursales': Sucursal.objects.all(),
        'usuarios': Usuario.objects.all()
    })


@rol_required(['cajero', 'user'])
def eliminar_caja(request, id):
    caja = get_object_or_404(Caja, id=id)
    caja.delete()
    messages.success(request, "Caja eliminada correctamente")
    return redirect('listado_cajas')


# =====================
# REEMBOLSOS - CAJERO Y USER
# =====================
@rol_required(['cajero', 'user'])
def listado_reembolsos(request):
    movimientos = Reembolso.objects.all().order_by('-fecha')
    saldo_actual = Decimal('0.00')
    for m in movimientos:
        m.saldo_anterior = saldo_actual
        if m.tipo in ['Deposito', 'Transferencia']:
            saldo_actual += m.monto
        else:
            saldo_actual -= m.monto
        m.saldo_actual = saldo_actual
    return render(request, 'listado_reembolsos.html', {'movimientos': movimientos})

@rol_required(['cajero', 'user'])
def nuevo_reembolso(request, tipo):
    if request.method == 'POST':
        try:
            # Validar monto
            monto = Decimal(request.POST.get('monto', '0'))
            if monto <= 0:
                raise ValueError("El monto debe ser mayor a 0.")

            # Obtener relaciones foráneas de forma segura
            sucursal_id = request.POST.get('sucursal')
            caja_id = request.POST.get('caja')
            cierre_id = request.POST.get('cierre_caja')

            sucursal = Sucursal.objects.filter(id=sucursal_id).first() if sucursal_id else None
            caja = Caja.objects.filter(id=caja_id).first() if caja_id else None
            cierre_caja = CierreCaja.objects.filter(id=cierre_id).first() if cierre_id else None

            # Crear objeto
            Reembolso.objects.create(
                tipo=tipo,
                monto=monto,
                motivo=request.POST.get('motivo', '').strip(),
                sucursal=sucursal,
                caja=caja,
                cierre_caja=cierre_caja,
                imagen=request.FILES.get('imagen')
            )
            messages.success(request, f"{tipo} registrado correctamente.")
            return redirect('listado_reembolsos')
        except Exception as e:
            messages.error(request, f"Error al guardar {tipo.lower()}: {e}")

    context = {
        'tipo': tipo,
        'sucursales': Sucursal.objects.all(),
        'cajas': Caja.objects.all(),
        'cierres': CierreCaja.objects.all(),
    }
    return render(request, 'nuevo_reembolso.html', context)

# === Editar reembolso ===
@rol_required(['cajero', 'user'])
def editar_reembolso(request, id):
    reembolso = get_object_or_404(Reembolso, id=id)
    if request.method == 'POST':
        try:
            # Validar monto
            monto = Decimal(request.POST.get('monto', '0'))
            if monto <= 0:
                raise ValueError("El monto debe ser mayor a 0.")
            reembolso.monto = monto

            # Motivo
            reembolso.motivo = request.POST.get('motivo', '').strip()

            # Relaciones foráneas
            sucursal_id = request.POST.get('sucursal')
            caja_id = request.POST.get('caja')
            cierre_id = request.POST.get('cierre_caja')

            reembolso.sucursal = Sucursal.objects.filter(id=sucursal_id).first() if sucursal_id else None
            reembolso.caja = Caja.objects.filter(id=caja_id).first() if caja_id else None
            reembolso.cierre_caja = CierreCaja.objects.filter(id=cierre_id).first() if cierre_id else None

            # Imagen (opcional)
            imagen = request.FILES.get('imagen')
            if imagen:
                reembolso.imagen = imagen

            reembolso.save()
            messages.success(request, "Registro actualizado correctamente.")
            return redirect('listado_reembolsos')
        except Exception as e:
            messages.error(request, f"Error al actualizar: {e}")

    context = {
        'reembolso': reembolso,
        'sucursales': Sucursal.objects.all(),
        'cajas': Caja.objects.all(),
        'cierres': CierreCaja.objects.all(),
    }
    return render(request, 'editar_reembolso.html', context)

@rol_required(['cajero', 'user'])
def eliminar_reembolso(request, id):
    reembolso = get_object_or_404(Reembolso, id=id)
    reembolso.delete()
    messages.success(request, "Registro eliminado correctamente.")
    return redirect('listado_reembolsos')

# =====================
# IMPRESIÓN DE VENTA - CAJERO Y USER
# =====================
@rol_required(['cajero', 'user'])
def imprimir_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = DetalleVenta.objects.filter(venta=venta)
    context = {
        'venta': venta,
        'detalles': detalles,
        'subtotal_total': sum(det.subtotal for det in detalles),
        'iva_con_comision_total': sum(det.comision + det.iva for det in detalles),
        'total_con_comision_total': sum(det.total_con_comision for det in detalles),
    }
    return render(request, 'imprimir_venta.html', context)

# =====================
# CIERRE DE CAJA - CAJERO Y USER
# =====================
IVA_PERCENT = Decimal('0.15')
@rol_required(['cajero', 'user'])
def cierre_caja(request, caja_id):
    # Obtener la caja a cerrar
    caja = get_object_or_404(Caja, id=caja_id)
    ventas_pendientes = Venta.objects.filter(caja=caja, cerrado_en__isnull=True, reembolso=False)
    reembolsos = Reembolso.objects.filter(caja=caja)

    # Verificar si ya existe un cierre hoy
    hoy = date.today()
    if CierreCaja.objects.filter(caja=caja, fecha=hoy).exists():
        messages.warning(request, f"La caja {caja.nombre} ya tiene un cierre generado hoy.")
        return redirect('listado_cajas')

    # Si el formulario fue enviado (POST)
    if request.method == 'POST':
        if not ventas_pendientes.exists():
            messages.warning(request, "No hay ventas pendientes para cerrar.")
            return redirect('listado_cajas')

        # Calcular los totales de ventas y reembolsos
        total_ventas = sum((v.total or Decimal('0.00')) for v in ventas_pendientes)
        total_reembolsos = sum((r.monto or Decimal('0.00')) for r in reembolsos)
        total_final = total_ventas - total_reembolsos

        # Crear el cierre de caja
        cierre = CierreCaja.objects.create(
            caja=caja,
            fecha=hoy,  # Usamos la fecha de hoy para evitar múltiples cierres
            total_ventas=total_ventas,
            total_recibido=total_final,
            total_vuelto=total_reembolsos
        )

        # Actualizar las ventas y reembolsos con el cierre
        ventas_pendientes.update(cerrado_en=cierre)
        reembolsos.update(cierre_caja=cierre)

        messages.success(request, f"Caja {caja.nombre} cerrada correctamente.")
        return redirect('listado_cajas')

    # Renderizar el template de cierre de caja
    return render(request, 'cierre_caja.html', {
        'caja': caja,
        'ventas_pendientes': ventas_pendientes,
        'reembolsos': reembolsos
    })


# ---------------------------
# REPORTE DIARIO PDF
# ---------------------------

# ---------------------------
# FUNCIONES DE CÁLCULO
# ---------------------------
def calcular_totales(venta):
    subtotal = sum((det.precio or Decimal('0.00')) * (det.cantidad or Decimal('0.00')) for det in venta.detalles.all())
    comision_total = sum(det.comision or Decimal('0.00') for det in venta.detalles.all())
    iva_total = comision_total * IVA_PERCENT
    total = subtotal + comision_total + iva_total
    return subtotal, comision_total, iva_total, total

def calcular_totales_reembolso(reembolso):
    monto = reembolso.monto or Decimal('0.00')
    comision_total = getattr(reembolso, 'comision', Decimal('0.00'))
    iva_total = comision_total * IVA_PERCENT
    subtotal = monto - comision_total - iva_total
    total = -monto
    return subtotal, comision_total, iva_total, total

# ---------------------------
# REPORTE DIARIO PDF CON TABLA - CAJERO Y USER
# ---------------------------
@rol_required(['cajero', 'user'])
def reporte_diario_pdf_tabla(request, caja_id):
    caja = get_object_or_404(Caja, id=caja_id)
    fecha_seleccionada = request.GET.get('fecha')
    fecha_filtrada = None
    if fecha_seleccionada:
        try:
            fecha_filtrada = date_parser.parse(fecha_seleccionada, dayfirst=True).date()
        except Exception:
            fecha_filtrada = None

    ventas = Venta.objects.filter(caja=caja)
    reembolsos = Reembolso.objects.filter(caja=caja)
    if fecha_filtrada:
        ventas = ventas.filter(fecha__date=fecha_filtrada)
        reembolsos = reembolsos.filter(fecha__date=fecha_filtrada)

    movimientos = []

    for v in ventas:
        subtotal, comision_total, iva_total, total = calcular_totales(v)
        productos = ", ".join(
            f"{d.producto if isinstance(d.producto, str) else getattr(d.producto, 'nombre', str(d.producto))} x{d.cantidad}"
            for d in v.detalles.all()
        )
        movimientos.append({
            'fecha': v.fecha or timezone.now(),
            'tipo': 'Venta',
            'cliente': v.nombre or '-',
            'motivo': f"Venta #{v.id}",
            'productos': productos,
            'subtotal': subtotal,
            'comision': comision_total,
            'iva': iva_total,
            'reembolsos': Decimal('0.00'),
            'total_neto': total
        })

    for r in reembolsos:
        subtotal, comision_total, iva_total, total = calcular_totales_reembolso(r)
        movimientos.append({
            'fecha': r.fecha or timezone.now(),
            'tipo': 'Reembolso',
            'cliente': '-',
            'motivo': r.motivo or '-',
            'productos': '',
            'subtotal': Decimal('0.00'),
            'comision': Decimal('0.00'),
            'iva': Decimal('0.00'),
            'reembolsos': -total,
            'total_neto': total
        })

    movimientos.sort(key=lambda x: x['fecha'])

    # Totales generales
    total_subtotal = sum(m['subtotal'] for m in movimientos)
    total_comision = sum(m['comision'] for m in movimientos)
    total_iva = sum(m['iva'] for m in movimientos)
    total_reembolsos = sum(m['reembolsos'] for m in movimientos)
    total_general = sum(m['total_neto'] for m in movimientos)

    # PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename=Reporte_Caja_{caja.id}_{fecha_filtrada or "todas"}_.pdf'
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y = height - 50

    # Cabecera
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"REPORTE DE CAJA: {caja.nombre}")
    y -= 25
    p.setFont("Helvetica", 10)
    fecha_str = fecha_filtrada.strftime('%d/%m/%Y') if fecha_filtrada else "Todas las fechas"
    p.drawString(50, y, f"Fecha: {fecha_str}")
    y -= 30

    # Tabla de movimientos
    data = [["Fecha", "Tipo", "Cliente/Motivo", "Productos", "Subtotal", "Comisión", "IVA", "Reembolsos", "Total Neto"]]

    for m in movimientos:
        data.append([
            m['fecha'].strftime('%d/%m/%Y %H:%M'),
            m['tipo'],
            f"{m['cliente']} {m['motivo']}",
            m['productos'],
            f"${m['subtotal']:.2f}",
            f"${m['comision']:.2f}",
            f"${m['iva']:.2f}",
            f"${m['reembolsos']:.2f}",
            f"${m['total_neto']:.2f}"
        ])

    # Totales al final
    data.append([
        "TOTALES", "", "", "",
        f"${total_subtotal:.2f}",
        f"${total_comision:.2f}",
        f"${total_iva:.2f}",
        f"${total_reembolsos:.2f}",
        f"${total_general:.2f}"
    ])

    table = Table(data, colWidths=[70, 50, 120, 120, 50, 50, 50, 50, 50])
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.gray),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(4,1),(-1,-1),'RIGHT'),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 8)
    ])
    table.setStyle(style)

    # Ajustar altura de tabla y dividir en páginas si es necesario
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.platypus import Table as PLTable, TableStyle as PLTableStyle
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"REPORTE DE CAJA: {caja.nombre} - Fecha: {fecha_str}", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(table)
    doc.build(elements)

    return response

@rol_required(['cajero', 'user'])
def vista_cierre_caja(request, caja_id):
    caja = get_object_or_404(Caja, id=caja_id)

    # Fecha opcional
    fecha_seleccionada = request.GET.get('fecha')
    fecha_filtrada = None
    if fecha_seleccionada:
        try:
            fecha_filtrada = date_parser.parse(fecha_seleccionada, dayfirst=True).date()
        except Exception:
            fecha_filtrada = None

    ventas = Venta.objects.filter(caja=caja)
    reembolsos = Reembolso.objects.filter(caja=caja)

    if fecha_filtrada:
        ventas = ventas.filter(fecha__date=fecha_filtrada)
        reembolsos = reembolsos.filter(fecha__date=fecha_filtrada)

    movimientos = []
    saldo_acumulado = Decimal('0.00')

    # Ventas
    for v in ventas:
        subtotal = sum(
            (d.precio or Decimal('0.00')) * (d.cantidad or Decimal('0.00'))
            for d in v.detalles.all()
        )
        comision_total = sum(d.comision or Decimal('0.00') for d in v.detalles.all())
        iva_total = comision_total * Decimal('0.15')
        total_neto = subtotal + comision_total + iva_total

        movimientos.append({
            'fecha': v.fecha or timezone.now(),
            'tipo': 'Venta',
            'cliente': v.nombre or '-',
            'motivo': f'Venta #{v.id}',
            'productos': [
                {
                    'nombre': d.producto.nombre if hasattr(d.producto, 'nombre') else str(d.producto),
                    'cantidad': d.cantidad or Decimal('0.00'),
                    'precio': d.precio or Decimal('0.00')
                } for d in v.detalles.all()
            ],
            'total_ventas': subtotal,
            'total_comision': comision_total,
            'total_iva': iva_total,
            'total_reembolsos': Decimal('0.00'),
            'total_neto': total_neto,
            'saldo_anterior': saldo_acumulado
        })

        saldo_acumulado += total_neto
        movimientos[-1]['saldo_actual'] = saldo_acumulado

    # Reembolsos
    for r in reembolsos:
        monto = r.monto or Decimal('0.00')
        total_neto = -monto

        movimientos.append({
            'fecha': r.fecha or timezone.now(),
            'tipo': 'Reembolso',
            'cliente': '-',
            'motivo': r.motivo or '-',
            'productos': [],
            'total_ventas': Decimal('0.00'),
            'total_comision': Decimal('0.00'),
            'total_iva': Decimal('0.00'),
            'total_reembolsos': monto,
            'total_neto': total_neto,
            'saldo_anterior': saldo_acumulado,
            'saldo_actual': saldo_acumulado + total_neto
        })

        saldo_acumulado += total_neto

    # 🔥 ORDEN CORRECTO (AQUÍ ESTÁ LA CLAVE)


    # Totales
    total_ventas = sum(m['total_ventas'] for m in movimientos)
    total_comision = sum(m['total_comision'] for m in movimientos)
    total_iva = sum(m['total_iva'] for m in movimientos)
    total_reembolsos = sum(m['total_reembolsos'] for m in movimientos)
    total_final = sum(m['total_neto'] for m in movimientos)

    context = {
        'caja': caja,
        'movimientos': movimientos,
        'fecha_seleccionada': fecha_seleccionada,
        'total_ventas': total_ventas,
        'total_comision': total_comision,
        'total_iva': total_iva,
        'total_reembolsos': total_reembolsos,
        'total_final': total_final,
    }

    return render(request, 'cierre_caja.html', context)

@login_required
@rol_required(['cajero', 'user'])
def imprimir_cierre_caja(request, caja_id):
    """Generar PDF del cierre de caja con diseño profesional"""
    caja = get_object_or_404(Caja, id=caja_id)
    
    # Obtener fecha de filtro
    fecha_seleccionada = request.GET.get('fecha')
    fecha_filtrada = None
    
    if fecha_seleccionada:
        try:
            fecha_filtrada = date_parser.parse(fecha_seleccionada, dayfirst=True).date()
        except Exception:
            fecha_filtrada = None
    
    # Obtener ventas y reembolsos
    ventas = Venta.objects.filter(caja=caja)
    reembolsos = Reembolso.objects.filter(caja=caja)
    
    if fecha_filtrada:
        ventas = ventas.filter(fecha__date=fecha_filtrada)
        reembolsos = reembolsos.filter(fecha__date=fecha_filtrada)
    
    # Calcular totales
    total_ventas = Decimal('0.00')
    total_comision = Decimal('0.00')
    total_iva = Decimal('0.00')
    total_reembolsos = Decimal('0.00')
    
    movimientos = []
    
    # Procesar ventas
    for venta in ventas:
        subtotal = Decimal('0.00')
        comision_venta = Decimal('0.00')
        iva_venta = Decimal('0.00')
        
        for detalle in venta.detalles.all():
            precio = detalle.precio or Decimal('0.00')
            cantidad = detalle.cantidad or 1
            comision = detalle.comision or Decimal('0.00')
            
            # Calcular subtotal
            subtotal_linea = precio * cantidad
            subtotal += subtotal_linea
            
            # Calcular comisión (10%)
            comision_linea = subtotal_linea * Decimal('0.10')
            comision_venta += comision_linea
            
            # Calcular IVA (16%)
            iva_linea = subtotal_linea * Decimal('0.16')
            iva_venta += iva_linea
        
        total_venta = subtotal - comision_venta + iva_venta
        
        movimientos.append({
            'fecha': venta.fecha or timezone.now(),
            'tipo': 'Venta',
            'cliente': venta.nombre or 'Consumidor Final',
            'motivo': f'Venta #{venta.id}',
            'subtotal': subtotal,
            'comision': comision_venta,
            'iva': iva_venta,
            'reembolsos': Decimal('0.00'),
            'total_neto': total_venta
        })
        
        total_ventas += total_venta
        total_comision += comision_venta
        total_iva += iva_venta
    
    # Procesar reembolsos
    for reembolso in reembolsos:
        monto = reembolso.monto or Decimal('0.00')
        
        movimientos.append({
            'fecha': reembolso.fecha or timezone.now(),
            'tipo': 'Reembolso',
            'cliente': '-',
            'motivo': reembolso.motivo or '-',
            'subtotal': Decimal('0.00'),
            'comision': Decimal('0.00'),
            'iva': Decimal('0.00'),
            'reembolsos': monto,
            'total_neto': -monto
        })
        
        total_reembolsos += monto
    
    # Ordenar por fecha
    movimientos.sort(key=lambda x: x['fecha'])
    
    # Calcular total general
    total_general = total_ventas - total_reembolsos
    
    # Crear PDF
    response = HttpResponse(content_type='application/pdf')
    fecha_str = fecha_filtrada.strftime('%Y%m%d') if fecha_filtrada else "todas"
    response['Content-Disposition'] = f'attachment; filename="cierre_caja_{caja.nombre}_{fecha_str}.pdf"'
    
    # Crear documento
    doc = SimpleDocTemplate(response, pagesize=letter, 
                           rightMargin=30, leftMargin=30, 
                           topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Título principal
    elements.append(Paragraph("REPORTE DE CIERRE DE CAJA", styles['Title']))
    elements.append(Spacer(1, 10))
    
    # Información de la caja
    info_data = [
        ["Caja:", caja.nombre],
        ["Sucursal:", caja.sucursal.nombre],
        ["Fecha:", fecha_filtrada.strftime('%d/%m/%Y') if fecha_filtrada else "Todas las fechas"],
        ["Generado:", timezone.now().strftime('%d/%m/%Y %H:%M')],
        ["Estado:", caja.estado]
    ]
    
    if caja.responsable:
        info_data.insert(2, ["Responsable:", caja.responsable.get_full_name()])
    
    # Crear tabla de información
    info_table = Table(info_data, colWidths=[100, 300])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # Resumen financiero
    elements.append(Paragraph("RESUMEN FINANCIERO", styles['Heading2']))
    elements.append(Spacer(1, 10))
    
    resumen_data = [
        ["CONCEPTO", "MONTO"],
        ["Total Ventas", f"${total_ventas:,.2f}"],
        ["Total Comisiones", f"${total_comision:,.2f}"],
        ["Total IVA", f"${total_iva:,.2f}"],
        ["Total Reembolsos", f"${total_reembolsos:,.2f}"],
        ["", ""],
        ["TOTAL NETO", f"${total_general:,.2f}"]
    ]
    
    resumen_table = Table(resumen_data, colWidths=[250, 100])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
    ]))
    elements.append(resumen_table)
    elements.append(Spacer(1, 20))
    
    # Detalle de movimientos
    if movimientos:
        elements.append(Paragraph("DETALLE DE MOVIMIENTOS", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        # Encabezado de la tabla
        data = [["Fecha", "Tipo", "Cliente/Motivo", "Subtotal", "Comisión", "IVA", "Reembolso", "Neto"]]
        
        for m in movimientos:
            tipo_color = colors.green if m['tipo'] == 'Venta' else colors.red
            
            data.append([
                m['fecha'].strftime('%d/%m/%Y %H:%M'),
                m['tipo'],
                f"{m['cliente']} - {m['motivo']}"[:40],
                f"${m['subtotal']:,.2f}",
                f"${m['comision']:,.2f}",
                f"${m['iva']:,.2f}",
                f"${m['reembolsos']:,.2f}" if m['reembolsos'] else "$0.00",
                f"${m['total_neto']:,.2f}"
            ])
        
        # Crear tabla
        table = Table(data, colWidths=[70, 50, 140, 60, 60, 60, 60, 60])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        # Totales al final
        totales_data = [
            ["TOTAL VENTAS:", f"${total_ventas:,.2f}"],
            ["TOTAL COMISIONES:", f"${total_comision:,.2f}"],
            ["TOTAL IVA:", f"${total_iva:,.2f}"],
            ["TOTAL REEMBOLSOS:", f"${total_reembolsos:,.2f}"],
            ["", ""],
            ["TOTAL GENERAL:", f"${total_general:,.2f}"]
        ]
        
        totales_table = Table(totales_data, colWidths=[150, 100])
        totales_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LINEABOVE', (0, -2), (-1, -2), 1, colors.grey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#27ae60')),
        ]))
        
        elements.append(totales_table)
    else:
        elements.append(Paragraph("No hay movimientos registrados en esta fecha", styles['Normal']))
    
    elements.append(Spacer(1, 30))
    
    # Pie de página
    elements.append(Paragraph("_" * 60, styles['Normal']))
    elements.append(Paragraph("Firma del Responsable", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Documento válido como constancia de cierre de caja", 
                            styles['Italic']))
    
    # Construir documento
    doc.build(elements)
    
    return response