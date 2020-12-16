import { ImportContactsModule } from './../import-contacts-module/import-contacts.module';
import { ImportFecFileRoutingModule } from './import-fecfile-routing.module';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ImportFecFileComponent } from './import-fecfile/import-fecfile.component';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { ImportContactsRoutingModule } from '../import-contacts-module/import-contact-routing.module';
import { CancelImportConfirmComponent } from '../import-contacts-module/import-contacts/cancel-import-confirm/cancel-import-confirm.component';
import { CleanContactsComponent } from '../import-contacts-module/import-contacts/clean-contacts/clean-contacts.component';
import { DuplicateContactsComponent } from '../import-contacts-module/import-contacts/clean-contacts/duplicate-contacts/duplicate-contacts.component';
import { ErrorContactsFieldComponent } from '../import-contacts-module/import-contacts/clean-contacts/error-contacts/error-contacts-field/error-contacts-field.component';
import { ErrorContactsComponent } from '../import-contacts-module/import-contacts/clean-contacts/error-contacts/error-contacts.component';
import { ConfigureContactsComponent } from '../import-contacts-module/import-contacts/configure-contacts/configure-contacts.component';
import { ImportContactsComponent } from '../import-contacts-module/import-contacts/import-contacts.component';
import { ImportDoneContactsComponent } from '../import-contacts-module/import-contacts/import-done-contacts/import-done-contacts.component';
import { ImportHowToComponent } from '../import-contacts-module/import-contacts/import-how-to/import-how-to.component';
import { ProgressBarComponent } from '../import-contacts-module/import-contacts/progress-bar/progress-bar.component';
import { ReviewUploadComponent } from '../import-contacts-module/import-contacts/review-upload/review-upload.component';
import { UploadContactsComponent } from '../import-contacts-module/import-contacts/upload-contacts/upload-contacts.component';
import { SharedModule } from '../shared/shared.module';
import { ImportFecfileSuccessComponent } from './import-fecfile/import-fecfile-success/import-fecfile-success.component';

@NgModule({
  imports: [SharedModule, ImportFecFileRoutingModule, NgbDropdownModule, ImportContactsModule],
  declarations: [
    // ImportContactsComponent,
    ImportFecFileComponent,
    ImportFecfileSuccessComponent,
    // UploadContactsComponent,
    // ConfigureContactsComponent,
    // CleanContactsComponent,
    // ImportDoneContactsComponent,
    // ProgressBarComponent,
    // DuplicateContactsComponent,
    // ErrorContactsComponent,
    // ErrorContactsFieldComponent,
    // ReviewUploadComponent,
    // ImportHowToComponent,
    // CancelImportConfirmComponent
  ],
  entryComponents: [CancelImportConfirmComponent]
})
export class ImportFecFile1Module { }
