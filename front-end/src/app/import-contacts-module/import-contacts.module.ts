import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ImportContactsRoutingModule } from './import-contact-routing.module';
import { ImportContactsComponent } from './import-contacts/import-contacts.component';
import { UploadContactsComponent } from './import-contacts/upload-contacts/upload-contacts.component';
import { ConfigureContactsComponent } from './import-contacts/configure-contacts/configure-contacts.component';
import { CleanContactsComponent } from './import-contacts/clean-contacts/clean-contacts.component';
import { ImportDoneContactsComponent } from './import-contacts/import-done-contacts/import-done-contacts.component';
import { SharedModule } from '../shared/shared.module';
import { ProgressBarComponent } from './import-contacts/progress-bar/progress-bar.component';
import { DuplicateContactsComponent } from './import-contacts/clean-contacts/duplicate-contacts/duplicate-contacts.component';
import { ErrorContactsComponent } from './import-contacts/clean-contacts/error-contacts/error-contacts.component';
import { ErrorContactsFieldComponent } from './import-contacts/clean-contacts/error-contacts/error-contacts-field/error-contacts-field.component';
import { ReviewUploadComponent } from './import-contacts/review-upload/review-upload.component';

@NgModule({
  imports: [
    SharedModule,
    ImportContactsRoutingModule
  ],
  declarations: [
    ImportContactsComponent,
    UploadContactsComponent,
    ConfigureContactsComponent,
    CleanContactsComponent,
    ImportDoneContactsComponent,
    ProgressBarComponent,
    DuplicateContactsComponent,
    ErrorContactsComponent,
    ErrorContactsFieldComponent,
    ReviewUploadComponent
  ]
})
export class ImportContactsModule { }
