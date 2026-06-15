import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ClientesService, ClienteData } from '../../../core/services/clientes.service';

@Component({
  selector: 'app-add-clients',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './add-clients.component.html',
  styleUrl: './add-clients.component.css'
})
export class AddClientsComponent implements OnInit {
  // Flag de control
  isEditMode: boolean = false;
  errorMessage: string | null = null;
  successMessage: string | null = null;
  clienteId: number | null = null;
  cargando: boolean = false;
  isSubmitting: boolean = false;

  listaPaises = [
    { nombre: 'España', bandera: '🇪🇸' },
    { nombre: 'Francia', bandera: '🇫🇷' },
    { nombre: 'Italia', bandera: '🇮🇹' },
    { nombre: 'Portugal', bandera: '🇵🇹' },
    { nombre: 'Bélgica', bandera: '🇧🇪' },
    { nombre: 'Alemania', bandera: '🇩🇪' },
    { nombre: 'Países Bajos', bandera: '🇳🇱' },
    { nombre: 'Reino Unido', bandera: '🇬🇧' },
    { nombre: 'Luxemburgo', bandera: '🇱🇺' },
    { nombre: 'Otros', bandera: '🌍' }
  ];

  cliente: ClienteData = {
    nombre: '', apellidos: '', email: '', telefono: '',
    usuario_vinted: '', usuario_wallapop: '', dni_nie: '',
    direccion: '', ciudad: '', codigo_postal: '', provincia: '',
    pais: 'España', notas_internas: '', 
    exento_comision: false,
    exento_tarifa_fija: false,
  };

  constructor(
    private clientesService: ClientesService,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      this.isEditMode = true; // 👈 Activamos el modo edición
      this.clienteId = Number(idParam);
      this.cargarDatos();
    }
  }

  cargarDatos() {
    if (!this.clienteId) return;
    this.cargando = true;
    this.clientesService.obtenerClientePorId(this.clienteId).subscribe({
      next: (data) => {
        this.cliente = { ...this.cliente, ...data };
        this.cargando = false;
      },
      error: () => {
        alert('❌ Error al cargar los datos del cliente.');
        this.volver();
      }
    });
  }



guardar() {
    // 1. Limpiamos mensajes anteriores
    this.errorMessage = null;
    this.successMessage = null;

    // 2. VALIDACIÓN LÓGICA: Exigimos AL MENOS UN identificador
    const tieneEmail = !!this.cliente.email?.trim();
    const tieneTelefono = !!this.cliente.telefono?.trim();
    const tieneUsuario = !!(this.cliente.usuario_vinted?.trim() || this.cliente.usuario_wallapop?.trim());

    if (!tieneEmail && !tieneTelefono && !tieneUsuario) {
      this.errorMessage = '⚠️ Debes indicar al menos un identificador (Correo, Teléfono o Usuario) para poder registrar al cliente.';
      window.scrollTo({ top: 0, behavior: 'smooth' }); 
      return;
    }

    this.isSubmitting = true;

    // 3. Destructuración: Extraemos lo que sobra
    const { id, total_ventas, fecha_registro, activo, ...payload } = this.cliente as any;

    // 4. EL CEPILLO DINÁMICO (Sin excepciones)
    // Como ahora TODO (excepto el país) es Optional en Python, 
    // podemos convertir tranquilamente cualquier texto vacío en 'null'
    Object.keys(payload).forEach(key => {
      if (typeof payload[key] === 'string' && payload[key].trim() === '') {
        // Protegemos el país para que nunca se vaya nulo si por algún motivo lo borran
        if (key === 'pais') {
          payload[key] = 'España';
        } else {
          payload[key] = null;
        }
      }
    });

    // 5. Limpieza de arrobas (@) en los usuarios de plataformas
    if (payload.usuario_vinted) {
      payload.usuario_vinted = payload.usuario_vinted.replace('@', '').trim();
    }
    if (payload.usuario_wallapop) {
      payload.usuario_wallapop = payload.usuario_wallapop.replace('@', '').trim();
    }

    console.log("Enviando al backend:", JSON.stringify(payload, null, 2));

    // 6. Decidimos si creamos o actualizamos
    const peticion = this.isEditMode && this.clienteId
      ? this.clientesService.actualizarCliente(this.clienteId, payload)
      : this.clientesService.crearCliente(payload);

    // 7. Ejecutamos la petición al servidor
    peticion.subscribe({
      next: () => {
        this.successMessage = this.isEditMode 
          ? '✅ Cambios guardados correctamente.' 
          : '✅ Cliente registrado con éxito.';
        
        setTimeout(() => this.volver(), 2000);
      },
      error: (err) => {
        this.isSubmitting = false;
        console.error('🔥 EL ERROR EXACTO ES:', JSON.stringify(err.error, null, 2));

        const backendError = err.error?.detail;

        if (typeof backendError === 'string') {
          this.errorMessage = `⚠️ ${backendError}`;
        } 
        else if (Array.isArray(backendError)) {
          const campoQueFalla = backendError[0]?.loc[backendError[0]?.loc.length - 1] || 'desconocido';
          this.errorMessage = `⚠️ Error de validación en el campo: "${campoQueFalla}". Revisa el formato.`;
        } 
        else {
          this.errorMessage = '❌ Ocurrió un error inesperado al guardar. Revisa los datos e inténtalo de nuevo.';
        }
        
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  }

  desactivar() {
    if (this.isEditMode && this.clienteId) {
      const confirmar = confirm(`¿Quieres desactivar a ${this.cliente.nombre}? No aparecerá en las listas activas.`);
      if (confirmar) {
        this.isSubmitting = true;
        this.clientesService.desactivarCliente(this.clienteId).subscribe({
          next: () => {
            alert('✅ Cliente desactivado.');
            this.volver();
          },
          error: () => this.isSubmitting = false
        });
      }
    }
  }

  volver() {
    this.router.navigate(['/clientes']);
  }
}