import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { ImportTransactionsRoutingModule } from './import-transactions-routing.module';
import { ImportTransactionsComponent } from './import-transactions/import-transactions.component';
import { ImportTrxHowToComponent } from './import-transactions/import-trx-how-to/import-trx-how-to.component';
import { ImportTrxStartComponent } from './import-transactions/import-trx-start/import-trx-start.component';
import { ImportTrxUploadComponent } from './import-transactions/import-trx-upload/import-trx-upload.component';
import { ImportTrxSidebarComponent } from './import-transactions/import-trx-sidebar/import-trx-sidebar.component';
import { ImportTrxReviewComponent } from './import-transactions/import-trx-review/import-trx-review.component';
import { ImportTrxDoneComponent } from './import-transactions/import-trx-done/import-trx-done.component';
import { ImportTrxCleanComponent } from './import-transactions/import-trx-clean/import-trx-clean.component';
import { UploadCompleteMessageComponent } from './import-transactions/import-trx-review/upload-complete-message/upload-complete-message.component';
import { ImportTrxFileSelectComponent } from './import-transactions/import-trx-file-select/import-trx-file-select.component';

@NgModule({
  imports: [SharedModule, ImportTransactionsRoutingModule, NgbDropdownModule],
  declarations: [
    ImportTransactionsComponent,
    ImportTrxHowToComponent,
    ImportTrxStartComponent,
    ImportTrxUploadComponent,
    ImportTrxSidebarComponent,
    ImportTrxReviewComponent,
    ImportTrxDoneComponent,
    ImportTrxCleanComponent,
    UploadCompleteMessageComponent,
    ImportTrxFileSelectComponent
  ],
  entryComponents: [UploadCompleteMessageComponent]
})
export class ImportTransactionsModule {}
