import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ImportContactsRoutingModule } from './import-contact-routing.module';
import { ImportContactsComponent } from './import-contacts/import-contacts.component';
import { UploadContactsComponent } from './import-contacts/upload-contacts/upload-contacts.component';
import { ConfigureContactsComponent } from './import-contacts/configure-contacts/configure-contacts.component';
import { CleanContactsComponent } from './import-contacts/clean-contacts/clean-contacts.component';
import { ImportDoneContactsComponent } from './import-contacts/import-done-contacts/import-done-contacts.component';
import { FooComponent } from './foo/foo.component';
import { SharedModule } from '../shared/shared.module';

@NgModule({
  imports: [
    SharedModule,
    ImportContactsRoutingModule
  ],
  declarations: [
    FooComponent,
    ImportContactsComponent,
    UploadContactsComponent,
    ConfigureContactsComponent,
    CleanContactsComponent,
    ImportDoneContactsComponent
  ]
})
export class ImportContactsModule { }
