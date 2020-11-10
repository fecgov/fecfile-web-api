import { NgModule } from '@angular/core';
import { SharedModule } from '../shared/shared.module';
import { NgbDropdownModule } from '@ng-bootstrap/ng-bootstrap';
import { ImportTransactionsRoutingModule } from './import-transactions-routing.module';
import { ImportTransactionsComponent } from './import-transactions/import-transactions.component';
import { ImportTrxHowToComponent } from './import-transactions/import-trx-how-to/import-trx-how-to.component';
import { ImportTrxStartComponent } from './import-transactions/import-trx-start/import-trx-start.component';
import { ImportTrxUploadComponent } from './import-transactions/import-trx-upload/import-trx-upload.component';

@NgModule({
  imports: [SharedModule, ImportTransactionsRoutingModule, NgbDropdownModule],
  declarations: [ImportTransactionsComponent, ImportTrxHowToComponent, ImportTrxStartComponent, ImportTrxUploadComponent]
})
export class ImportTransactionsModule {}
