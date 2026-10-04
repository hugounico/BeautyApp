from django.contrib.admin.sites import site as admin_site
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.test import RequestFactory, TestCase

from apps.proveedores.admin import ProveedorProfesionalAdmin
from apps.proveedores.models import ModalidadChoices, ProveedorProfesional

Usuario = get_user_model()


class ProveedorProfesionalModelTests(TestCase):
    """Tests unitarios basados en ejemplos para el modelo ProveedorProfesional.

    Cubre Requirements 4.8 y 4.9.
    """

    def test_creacion_valida(self):
        """Un ProveedorProfesional con datos válidos se crea y persiste correctamente."""
        proveedor = ProveedorProfesional.objects.create(
            nombre_comercial='Estudio de Belleza Aurora',
            es_negocio=True,
            modalidad=ModalidadChoices.EN_LOCAL,
            ubicacion='Av. Siempre Viva 123',
            biografia='Salón especializado en tratamientos capilares.',
        )

        self.assertIsNotNone(proveedor.pk)
        self.assertEqual(proveedor.nombre_comercial, 'Estudio de Belleza Aurora')
        self.assertTrue(proveedor.es_negocio)
        self.assertEqual(proveedor.modalidad, ModalidadChoices.EN_LOCAL)
        self.assertTrue(proveedor.activo)

    def test_creacion_valida_con_defaults(self):
        """Los defaults (es_negocio=False, modalidad=A_DOMICILIO, activo=True) se aplican."""
        proveedor = ProveedorProfesional.objects.create(
            nombre_comercial='Manicura a Domicilio',
        )

        self.assertFalse(proveedor.es_negocio)
        self.assertEqual(proveedor.modalidad, ModalidadChoices.A_DOMICILIO)
        self.assertTrue(proveedor.activo)

    def test_str_retorna_nombre_comercial(self):
        """__str__ retorna el nombre_comercial de la instancia."""
        proveedor = ProveedorProfesional.objects.create(
            nombre_comercial='Barbería El Corte',
        )

        self.assertEqual(str(proveedor), 'Barbería El Corte')

    def test_modalidad_fuera_de_choices_rechazada_via_full_clean(self):
        """Una modalidad fuera de ModalidadChoices es rechazada por full_clean() (Req 4.9)."""
        proveedor = ProveedorProfesional(
            nombre_comercial='Proveedor Inválido',
            modalidad='modalidad_inexistente',
        )

        with self.assertRaises(ValidationError) as contexto:
            proveedor.full_clean()

        self.assertIn('modalidad', contexto.exception.message_dict)

    def test_nombre_comercial_vacio_rechazado_via_full_clean(self):
        """Un nombre_comercial vacío es rechazado por full_clean() (Req 4.8)."""
        proveedor = ProveedorProfesional(
            nombre_comercial='',
            modalidad=ModalidadChoices.A_DOMICILIO,
        )

        with self.assertRaises(ValidationError) as contexto:
            proveedor.full_clean()

        self.assertIn('nombre_comercial', contexto.exception.message_dict)

    def test_nombre_comercial_muy_largo_rechazado_via_full_clean(self):
        """Un nombre_comercial de más de 150 caracteres es rechazado por full_clean() (Req 4.8)."""
        proveedor = ProveedorProfesional(
            nombre_comercial='a' * 151,
            modalidad=ModalidadChoices.A_DOMICILIO,
        )

        with self.assertRaises(ValidationError) as contexto:
            proveedor.full_clean()

        self.assertIn('nombre_comercial', contexto.exception.message_dict)


class ProveedorUsuarioVinculoTests(TestCase):
    """Tests del vínculo opcional Usuario ⇄ ProveedorProfesional (R1)."""

    def test_campo_usuario_definicion(self):
        """R1.1: el campo `usuario` es OneToOne con related_name='perfil_proveedor',
        null=True, blank=True y on_delete=CASCADE."""
        campo = ProveedorProfesional._meta.get_field('usuario')

        self.assertIsInstance(campo, models.OneToOneField)
        self.assertEqual(campo.remote_field.related_name, 'perfil_proveedor')
        self.assertTrue(campo.null)
        self.assertTrue(campo.blank)
        self.assertEqual(campo.remote_field.on_delete, models.CASCADE)
        self.assertEqual(campo.remote_field.model, Usuario)

    def test_guardar_sin_usuario(self):
        """R1.2 / R1.6: guardar un ProveedorProfesional sin `usuario` no lanza error
        y el campo queda nulo (equivalente a filas existentes tras la migración
        nullable sin backfill)."""
        proveedor = ProveedorProfesional.objects.create(
            nombre_comercial='Proveedor Sin Cuenta',
        )

        self.assertIsNone(proveedor.usuario)
        proveedor.refresh_from_db()
        self.assertIsNone(proveedor.usuario)

    def test_usuario_ya_vinculado_es_rechazado(self):
        """R1.3: asociar un Usuario ya vinculado a otro ProveedorProfesional es
        rechazado por unicidad del OneToOneField; el vínculo previo queda intacto."""
        usuario = Usuario.objects.create_user(username='prov_uno', password='Clave12345!')
        primero = ProveedorProfesional.objects.create(
            nombre_comercial='Proveedor Primero',
            usuario=usuario,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProveedorProfesional.objects.create(
                    nombre_comercial='Proveedor Segundo',
                    usuario=usuario,
                )

        primero.refresh_from_db()
        self.assertEqual(primero.usuario_id, usuario.pk)
        self.assertEqual(
            ProveedorProfesional.objects.filter(usuario=usuario).count(),
            1,
        )

    def test_cascade_al_borrar_usuario(self):
        """R1.4: borrar el Usuario vinculado elimina su ProveedorProfesional (CASCADE)."""
        usuario = Usuario.objects.create_user(username='prov_cascade', password='Clave12345!')
        proveedor = ProveedorProfesional.objects.create(
            nombre_comercial='Proveedor Cascade',
            usuario=usuario,
        )
        proveedor_pk = proveedor.pk

        usuario.delete()

        self.assertFalse(
            ProveedorProfesional.objects.filter(pk=proveedor_pk).exists(),
        )

    def test_usuario_sin_cliente_ni_proveedor(self):
        """R1.8: un Usuario puede existir sin Cliente ni ProveedorProfesional
        (sin exclusión mutua ni sistema de roles)."""
        usuario = Usuario.objects.create_user(username='usuario_neutro', password='Clave12345!')

        self.assertFalse(hasattr(usuario, 'perfil_cliente'))
        self.assertFalse(hasattr(usuario, 'perfil_proveedor'))


class ProveedorProfesionalAdminTests(TestCase):
    """Tests del admin del vínculo (R1.5)."""

    def test_usuario_es_editable_en_admin(self):
        """R1.5: el admin expone `usuario` como campo editable (asociar/desasociar)."""
        admin_obj = ProveedorProfesionalAdmin(ProveedorProfesional, admin_site)

        # `usuario` está expuesto y no es de solo lectura.
        self.assertIn('usuario', admin_obj.fields)
        self.assertNotIn('usuario', admin_obj.get_readonly_fields(request=None))

        # El form del admin incluye `usuario` como campo editable. Se usa un
        # request con superusuario porque el admin consulta permisos de
        # relaciones al construir el formulario.
        admin_usuario = Usuario.objects.create_superuser(
            username='admin_r15', password='Clave12345!'
        )
        request = RequestFactory().get('/')
        request.user = admin_usuario

        form_class = admin_obj.get_form(request)
        self.assertIn('usuario', form_class.base_fields)
