import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'front';

  constructor(private translate: TranslateService) {
    this.translate.addLangs(['en', 'es']);
    this.translate.setFallbackLang('es'); // Español por defecto

    // Detectar el idioma del navegador
    const browserLang = this.translate.getBrowserLang();
    // Usar el del navegador si está soportado, si no 'es'
    this.translate.use(browserLang?.match(/en|es/) ? browserLang : 'es');
  }
}
