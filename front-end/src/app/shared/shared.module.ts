import { PhonePipe } from './pipes/phone-number/phone-number.pipe';
import { ValidateComponent } from './partials/validate/validate.component';
import { SubmitComponent } from './partials/submit/submit.component';
import { NgModule } from '@angular/core';
import { CommonModule, CurrencyPipe, DecimalPipe, DatePipe } from '@angular/common';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgSelectModule } from '@ng-select/ng-select';
import { NgxPaginationModule } from 'ngx-pagination';
import { StepsComponent } from './partials/steps/steps.component';
import { SignAndSubmitComponent } from './partials/sign-and-submit/sign-and-submit.component';
import { SubTransactionsTableComponent } from './components/sub-transactions-table/sub-transactions-table.component';
import { UtilService } from './utils/util.service';
import { OrderByPipe } from 'ngx-pipes';
import { ModalModule } from 'ngx-bootstrap';
import { InputModalComponent } from './partials/input-modal/input-modal.component';
import { ExportDirective } from './directives/export.directive';
import { ReportTypeSidebarComponent } from '../forms/form-3x/report-type-sidebar/report-type-sidebar.component';
import { ReportTypeComponent } from '../forms/form-3x/report-type/report-type.component';
import { SpinnerComponent } from './partials/spinner/spinner.component';

@NgModule({
  imports: [
    CommonModule,
    NgbModule,
    FormsModule,
    ReactiveFormsModule,
  ],
  declarations: [
    StepsComponent,
    ReportTypeSidebarComponent,
    SignAndSubmitComponent,
    SubTransactionsTableComponent,
    SubmitComponent,
    ReportTypeComponent,
    ValidateComponent,
    PhonePipe,
    InputModalComponent,
    SpinnerComponent
  ],
  exports: [
    CommonModule,
    NgbModule,
    NgSelectModule,
    FormsModule,
    ReactiveFormsModule,
    NgxPaginationModule,
    ModalModule,
    StepsComponent,
    ReportTypeSidebarComponent,
    SignAndSubmitComponent,
    SubTransactionsTableComponent,
    SubmitComponent,
    ReportTypeComponent,
    InputModalComponent,
    SpinnerComponent
  ],
  providers: [
    DecimalPipe,
    DatePipe,
    UtilService,
    OrderByPipe,
    PhonePipe,
    CurrencyPipe,
    ExportDirective
  ],
  entryComponents: [InputModalComponent]
})
export class SharedModule { }
