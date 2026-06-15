import { Component, EventEmitter, HostListener, Input, Output } from '@angular/core';

// import { Component, Input, Output, EventEmitter, HostListener } from '@angular/common';
import { CommonModule } from '@angular/common';
import { DragDropModule, CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';

@Component({
  selector: 'app-image-manager',
  standalone: true,
  imports: [CommonModule, DragDropModule],
  templateUrl: './image-manager.component.html',
  styleUrls: ['./image-manager.component.css']
})
export class ImageManagerComponent {
  // Recibimos los datos de la variante
  @Input() imagenes: string[] = []; 
  @Input() imagenesFiles: (File | null)[] = [];
  @Input() variantId: string = ''; // Usado para IDs únicos en el input file

  // Emitimos los cambios al padre para mantener la sincronización
  @Output() imagesChanged = new EventEmitter<{ imagenes: string[], files: (File | null)[] }>();

  // Estado del Modal (Carrusel)
  mostrarModal = false;
  indiceActivo = 0;

  // --- GESTIÓN DE ARCHIVOS ---
  // --- GESTIÓN DE ARCHIVOS (Dentro de ImageManagerComponent) ---
  // ================== GESTIÓN DE ARCHIVOS ==================
  // --- GESTIÓN DE ARCHIVOS (HIJO) ---
  async onFilesSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const files = input.files;
    
    if (!files || files.length === 0) return;

    const filesArray = Array.from(files);
    
    for (const file of filesArray) {
      const base64 = await this.fileToBase64(file);
      
      // El hijo solo actualiza sus propios Inputs y avisa al padre
      this.imagenesFiles = [...this.imagenesFiles, file];
      this.imagenes = [...this.imagenes, base64];
    }
    
    // Notificamos al Padre (AddProductComponent) que las fotos cambiaron
    this.notificarCambio();

    // Limpiamos el input
    input.value = '';
  }

  eliminarImagen(index: number) {
    this.imagenes.splice(index, 1);
    this.imagenesFiles.splice(index, 1);
    this.notificarCambio();
  }

  onImageDrop(event: CdkDragDrop<string[]>) {
    moveItemInArray(this.imagenes, event.previousIndex, event.currentIndex);
    moveItemInArray(this.imagenesFiles, event.previousIndex, event.currentIndex);
    this.notificarCambio();
  }

  // --- LÓGICA DEL CARRUSEL ---
  abrirModal(index: number) {
    this.indiceActivo = index;
    this.mostrarModal = true;
    document.body.style.overflow = 'hidden'; // Bloquea scroll de fondo
  }

  cerrarModal() {
    this.mostrarModal = false;
    document.body.style.overflow = 'auto';
  }

  navegar(dir: number, event: Event) {
    event.stopPropagation();
    const total = this.imagenes.length;
    this.indiceActivo = (this.indiceActivo + dir + total) % total;
  }

  @HostListener('document:keydown', ['$event'])
  handleKeyboard(event: KeyboardEvent) {
    if (!this.mostrarModal) return;
    if (event.key === 'ArrowRight') this.navegar(1, event);
    if (event.key === 'ArrowLeft') this.navegar(-1, event);
    if (event.key === 'Escape') this.cerrarModal();
  }

  private fileToBase64(file: File): Promise<string> {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.readAsDataURL(file);
    });
  }

  private notificarCambio() {
    this.imagesChanged.emit({
      imagenes: this.imagenes,
      files: this.imagenesFiles
    });
  }
}