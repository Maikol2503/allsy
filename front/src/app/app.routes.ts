import { Routes } from '@angular/router';
import { LayoutComponent } from './layout/layout.component';
import { LoginComponent } from './features/auth/login/login.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { authGuard } from './core/guards/auth.guard';
import { AddProductComponent } from './features/products/add-product/add-product.component';
import { ProductsListComponent } from './features/products/products-list/products-list.component';
import { ProductDetailComponent } from './features/products/product-detail/product-detail.component';
import { StockDetailComponent } from './features/products/stock-detail/stock-detail.component';
import { EditStockComponent } from './features/products/edit-stock/edit-stock.component';
import { PapeleraComponent } from './features/products/papelera/papelera.component';

import { PosComponent } from './features/pos/pos-create/pos.component';
import { EditSaleComponent } from './features/pos/edit-sale/edit-sale.component';
import { SalesListComponent } from './features/pos/sales-list/sales-list.component';
import { OrderFulfillmentComponent } from './features/pos/order-fulfillment/order-fulfillment.component';
import { EgresosListComponent } from './features/egresos/egresos-list/egresos-list.component';
import { EgresosCreateComponent } from './features/egresos/egresos-create/egresos-create.component';
import { StatisticsComponent } from './features/statistics/statistics.component';

import { ListClientsComponent } from './features/clients/list-clients/list-clients.component';
import { AddClientsComponent } from './features/clients/add-clients/add-clients.component';
import { ClientDetailComponent } from './features/clients/client-detail/client-detail.component';
import { AuditPageComponent } from './features/audit/audit-page.component';
import { OnlineOrdersComponent } from './features/pos/online-orders/online-orders.component';
import { LocationsComponent } from './features/settings/locations/locations.component';
import { OrderDetailComponent } from './features/pos/order-detail/order-detail.component';

export const routes: Routes = [
  // Ruta pública (login)
  { path: 'login', component: LoginComponent },

  // Rutas protegidas (dashboard, etc.)
  {
    path: '',
    component: LayoutComponent,
    canActivate: [authGuard], 
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent },
      
      // --- PRODUCTOS ---
      { path: 'new', component: AddProductComponent },
      { path: 'edit/:id', component: AddProductComponent },
      { path: 'view-products', component: ProductsListComponent },
      { path: 'detail-product/:id', component: ProductDetailComponent },
      { path: 'stock-detail/:id', component: StockDetailComponent },
      { path: 'edit-stock/:id', component: EditStockComponent },
      { path: 'papelera', component: PapeleraComponent },

      // --- VENTAS (POS) ---
      { path: 'pos', component: PosComponent },
      { path: 'sales-list', component: SalesListComponent },
      { path: 'online-orders', component: OnlineOrdersComponent },
      { path: 'order-detail/:id', component: OrderDetailComponent },
      { path: 'edit-sale/:id', component: EditSaleComponent },
      { path: 'fulfillment', component: OrderFulfillmentComponent },

      // --- EGRESOS ---
      { path: 'egresos', component: EgresosListComponent },
      { path: 'egresos/nuevo', component: EgresosCreateComponent },
      { path: 'egresos/editar/:id', component: EgresosCreateComponent },

      // --- ESTADÍSTICAS ---
      { path: 'statistics', component: StatisticsComponent },

      // --- CLIENTES CRM ---
      { path: 'clientes', component: ListClientsComponent },
      { path: 'clientes/nuevo', component: AddClientsComponent },
      { path: 'clientes/editar/:id', component: AddClientsComponent },
      { path: 'clientes/detalle/:id', component: ClientDetailComponent },
      { path: 'audit', component: AuditPageComponent },
      { path: 'locations', component: LocationsComponent },
    ],
  },

  // Si no existe, redirigir al login
  { path: '**', redirectTo: 'login' },
];
