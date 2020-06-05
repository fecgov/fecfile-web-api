import {AbstractControl} from '@angular/forms';

export class CustomValidator {
   static noBlankSpaces(control: AbstractControl) {
        if (control && control.value && !control.value.replace(/\s/g, '').length) {
            control.setValue('');
            return {required: true};
        } else {
            return null;
        }
    }
}
