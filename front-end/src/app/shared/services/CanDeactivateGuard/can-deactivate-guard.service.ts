import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
// import { CanDeactivate, CanComponentDeactivate } from '../../interfaces/can-deactivate';

@Injectable({
  providedIn: 'root'
})
export class CanDeactivateGuardService /*implements CanDeactivate<CanComponentDeactivate>*/ {

  constructor() { }

  /*canDeactivate(component: CanComponentDeactivate,
           route: ActivatedRouteSnapshot,
           state: RouterStateSnapshot) {

     let url: string = state.url;
     console.log('Url: '+ url);

     return component.canDeactivate ? component.canDeactivate() : true;
  }*/
}
