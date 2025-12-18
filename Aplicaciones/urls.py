from django.urls import path
from . import views

urlpatterns = [
    # =======================
    #     LOGIN / LOGOUT
    # =======================
    path('', views.index, name='index'),  # <--- Esta línea hace que / vaya al index

    # =======================
    #     VENTAS
    # =======================
    path('ventas/', views.listado_ventas, name='listado_ventas'),
    path('ventas/nueva/', views.nueva_venta, name='nueva_venta'),
    path('editar_venta/<int:venta_id>/', views.editar_venta, name='editar_venta'),
    path('ventas/eliminar/<int:id>/', views.eliminar_venta, name='eliminar_venta'),
    path('ventas/detalle/<int:id>/', views.detalle_venta_ajax, name='detalle_venta_ajax'),  # <-- aquí

    path('ventas/imprimir/<int:venta_id>/', views.imprimir_venta, name='imprimir_venta'),

    # =======================
    #     SUCURSALES
    # =======================
    path('sucursales/', views.listado_sucursales, name='listado_sucursales'),
    path('sucursales/nueva/', views.nueva_sucursal, name='nueva_sucursal'),
    path('sucursales/editar/<int:id>/', views.editar_sucursal, name='editar_sucursal'),
    path('sucursales/eliminar/<int:id>/', views.eliminar_sucursal, name='eliminar_sucursal'),

    # =======================
    #     USUARIOS
    # =======================
    path('usuarios/', views.listado_usuarios, name='listado_usuarios'),
    path('usuarios/nuevo/', views.nuevo_usuario, name='nuevo_usuario'),
    path('usuarios/editar/<int:id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),

    # =======================
    #     MÉTODOS DE PAGO
    # =======================
    path('metodospago/', views.listado_metodopago, name='listado_metodopago'),
    path('metodospago/nuevo/', views.nuevo_metodopago, name='nuevo_metodopago'),
    path('metodospago/editar/<int:id>/', views.editar_metodopago, name='editar_metodopago'),
    path('metodospago/eliminar/<int:id>/', views.eliminar_metodopago, name='eliminar_metodopago'),

    # =======================
    #     CAJAS
    # =======================
    path('cajas/', views.listado_cajas, name='listado_cajas'),

    # Crear nueva caja
    path('cajas/nueva/', views.nueva_caja, name='nueva_caja'),

    # Editar caja
    path('cajas/<int:caja_id>/editar/', views.editar_caja, name='editar_caja'),

    # Eliminar caja
    path('cajas/<int:caja_id>/eliminar/', views.eliminar_caja, name='eliminar_caja'),
    

    # Cerrar caja
    path('cajas/<int:caja_id>/cerrar/', views.cierre_caja, name='cerrar_caja'),

    # Vista de cierre y movimientos (por día)
    path('cajas/<int:caja_id>/movimientos/', views.vista_cierre_caja, name='vista_cierre_caja'),

    # Imprimir cierre de caja en PDF (por día)
    path('cajas/<int:caja_id>/reporte-diario/', views.imprimir_cierre_caja, name='reporte_diario_caja'),
    path('cajas/<int:caja_id>/imprimir-cierre/', views.imprimir_cierre_caja, name='imprimir_cierre_caja'),
    



    # =======================
    #     REEMBOLSOS
    # =======================
   # Listado de movimientos
    path('reembolsos/', views.listado_reembolsos, name='listado_reembolsos'),
    path('reembolsos/nuevo/<str:tipo>/', views.nuevo_reembolso, name='nuevo_movimiento'),
    path('reembolsos/editar/<int:id>/', views.editar_reembolso, name='editar_reembolso'),
    path('reembolsos/eliminar/<int:id>/', views.eliminar_reembolso, name='eliminar_reembolso'),
    path('cajas/<int:caja_id>/cerrar/', views.cierre_caja, name='cierre_caja'),
    
]
