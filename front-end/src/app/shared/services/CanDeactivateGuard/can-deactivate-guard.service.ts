import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { CanDeactivate, CanComponentDeactivate } from '../../interfaces/CanDeactivate/can-deactivate';
import { FormsComponent } from '../../../forms/forms.component';
import { PreviewComponent } from '../../partials/preview/preview.component';

@Injectable({
  providedIn: 'root'
})
export class CanDeactivateGuardService implements CanDeactivate<FormsComponent | PreviewComponent> {

  constructor() { }

  canDeactivate(
	  component: FormsComponent | PreviewComponent,
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ) {

     let url: string = state.url;

     return component.canDeactivate ? component.canDeactivate() : true;
  }
}
