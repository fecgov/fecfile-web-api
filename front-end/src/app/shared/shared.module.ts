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

@NgModule({
  imports: [
    CommonModule,
    NgbModule,
    FormsModule,
    ReactiveFormsModule,
  ],
  declarations: [
    StepsComponent,
    SignAndSubmitComponent,
    SubTransactionsTableComponent,
    SubmitComponent,
    ValidateComponent
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
    SignAndSubmitComponent,
    SubTransactionsTableComponent, 
    SubmitComponent
  ], 
  providers: [
    DecimalPipe,
    DatePipe,
    UtilService,
    OrderByPipe,
    CurrencyPipe
  ],
})
export class SharedModule { }
