import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { CanDeactivateGuardService } from '../shared/services/CanDeactivateGuard/can-deactivate-guard.service';
import { CanActivateGuard } from '../shared/utils/can-activate/can-activate.guard';
import { ImportFecFileComponent } from './import-fecfile/import-fecfile.component';



const routes: Routes = [
  {
    path: '',
    component: ImportFecFileComponent,
    pathMatch: 'full',
    canActivate: [CanActivateGuard],
    canDeactivate: [CanDeactivateGuardService]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ImportFecFileRoutingModule { }
