import { HttpClient } from '@angular/common/http';
import { ViewEncapsulation } from '@angular/compiler/src/core';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { ReportsService } from 'src/app/reports/service/report.service';
import { FormsService } from 'src/app/shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { F3xMessageService } from '../../form-3x/service/f3x-message.service';
import { TransactionTypeService } from '../../form-3x/transaction-type/transaction-type.service';
import { LoanMessageService } from '../../sched-c/service/loan-message.service';
import { SchedHMessageServiceService } from '../../sched-h-service/sched-h-message-service.service';
import { SchedHServiceService } from '../../sched-h-service/sched-h-service.service';
import { ReportTypeService } from './../../../forms/form-3x/report-type/report-type.service';
import { F3xComponent } from './../../form-3x/f3x/f3x.component';

@Component({
  selector: 'app-f3l',
  templateUrl: './f3l.component.html',
  styleUrls: ['./f3l.component.scss'], 
  encapsulation: ViewEncapsulation.None,
  // changeDetection: ChangeDetectionStrategy.OnPush
})
export class F3lComponent extends F3xComponent implements OnInit {


  constructor( _reportTypeService: ReportTypeService,
     _transactionTypeService: TransactionTypeService,
     _formService: FormsService,
     _http: HttpClient,
     _fb: FormBuilder,
     _config: NgbTooltipConfig,
     _router: Router,
     _f3xMessageService: F3xMessageService,
     _loanMessageService: LoanMessageService,
     _schedHMessageServce: SchedHMessageServiceService,
     _schedHService: SchedHServiceService,
     _messageService: MessageService,
     reportsService:ReportsService,
     _activatedRoute: ActivatedRoute,
     cd:ChangeDetectorRef){
      super(_reportTypeService,_transactionTypeService,_formService,_http,_fb,_config,_router,_activatedRoute, _f3xMessageService,
        _loanMessageService,_schedHMessageServce,_schedHService,_messageService,reportsService);
    }

  ngOnInit() {
    // this.transactionCategories = this.transactionCategories.transactionCategories;
    super.ngOnInit();
  }

}
