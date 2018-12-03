import { Injectable, Inject } from '@angular/core';
import { CanDeactivate } from '@angular/router';
import { FormsComponent } from '../../../forms/forms.component';


@Injectable()
export class CanDeactivateGuard implements CanDeactivate<FormsComponent> {
  canDeactivate(component: FormsComponent): boolean {
   
    if(component.hasUnsavedData()){
        if (confirm('You have unsaved changes! If you leave, your changes will be lost.')) {
            return true;
        } else {
            return false;
        }
    }
    return true;
  }
}