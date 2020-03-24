import { Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { BehaviorSubject, of, Subject } from 'rxjs';
import { Subscription } from 'rxjs/Subscription';
import { ReportsService } from 'src/app/reports/service/report.service';
import { UtilService } from 'src/app/shared/utils/util.service';
import { ConfirmModalComponent, ModalHeaderClassEnum } from '../shared/partials/confirm-modal/confirm-modal.component';
import { DialogService } from '../shared/services/DialogService/dialog.service';
import { FormsService } from '../shared/services/FormsService/forms.service';

@Component({
  selector: 'app-forms',
  templateUrl: './forms.component.html',
  styleUrls: ['./forms.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class FormsComponent implements OnInit, OnDestroy {
  public formType: string = '';
  public closeResult: string = '';
  public canContinue: boolean = false;
  public showValidateBar: boolean = false;
  public confirmModal: BehaviorSubject<boolean> = new BehaviorSubject(false);

  private onDestroy$ = new Subject();
  
  private _openModal: any = null;
  private _step: string;
  private _editMode: boolean;
  private queryParamsSubscription:Subscription;
  private paramsSubscription:Subscription;
  public jumpToTransaction: any;
  returnToGlobalAllTransaction: boolean;

  constructor(
    private _activeRoute: ActivatedRoute,
    private _router: Router,
    private _dialogService: DialogService,
    private _formsService: FormsService,
    private _reportsService: ReportsService,
    private _utilService: UtilService
  ) {

    this.queryParamsSubscription = _activeRoute.queryParams.takeUntil(this.onDestroy$).subscribe(p => {
      if (p.step) {
        this._step = p.step;
      }
      this._editMode = p.edit && p.edit === 'false' ? false : true;
    });
  }

  ngOnInit(): void {
    this.paramsSubscription = this._activeRoute.params.subscribe(params => {
      this.formType = params.form_id;
    });
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.queryParamsSubscription.unsubscribe();
    this.paramsSubscription.unsubscribe();
  }


  /**
   * Determines ability for a person to leave a page with a form on it.
   *
   * @return     {boolean}  True if able to deactivate, False otherwise.
   */
  public async canDeactivate(): Promise<boolean> {
    if (this._formsService.formHasUnsavedData(this.formType) && this._editMode) {
      let result: boolean = null;
      //console.log(' form not saved...');
      result = await this._dialogService.confirm('', ConfirmModalComponent).then(res => {
        let val: boolean = null;

        if (res === 'okay') {
          val = true;
        } else if (res === 'cancel') {
          val = false;
        }

        return val;
      });

      return result;
    } else if (this._formsService.checkCanDeactivate()) {
      let result: boolean = null;
      //console.log(' form not saved...');
      result = await this._dialogService
      .confirm(
        'FEC ID has not been generated yet. Please check the FEC ID under reports if you want to leave the page.',
        ConfirmModalComponent,
        'Warning',
        true,
        ModalHeaderClassEnum.warningHeader,
        null,
        'Leave page'
      ).then(res => {
        let val: boolean = null;

        if (res === 'okay') {
          val = false;
        } else if (res === 'cancel') {
          val = true;
        }

        return val;
      });

      return result;
    } else {
      //console.log('Not any unsaved data...');
      return true;
    }
  }

  public onNotify(e: any): void {
    // this.returnToGlobalAllTransaction = true;
    const formType = this.getFormType(e.form);
    if(e.transactionDetail.transactionModel.reportId){
      this.setReportSpecificMetaDataAndProceed(e.transactionDetail.transactionModel.reportId,e,formType);
    }
  }
  
  private navigateToReportSpecificAllTransactions(success: any, e: any, formType: string) {
    if (success) {
      this.jumpToTransaction = e;
      let queryParamsMap: any = {
        step: 'transactions',
        edit: true,
        transactionCategory: e.transactionCategory,
        allTransactions: false,
        reportId: e.transactionDetail.transactionModel.reportId
      };
      this._router.navigate([`/forms/form/${formType}`], {
        queryParams: queryParamsMap
      });
    }
    else {
      console.error('There was an issue setting coverage dates for this report');
    }
  }

  private setReportSpecificMetaDataAndProceed(reportId:string,e:any, formType:string) {
    const form_type = formType === '3X' ? 'F3X' : formType;
    this._reportsService.getReportInfo(form_type,reportId).subscribe(response => {
      if (response && response.length > 0){
        response = response[0];
        let reportTypeObj : any = localStorage.getItem(`form_${this.formType}_report_type`);
        if(!reportTypeObj){
          reportTypeObj = {};
        }
        localStorage.setItem('form_3X_details', JSON.stringify(response));
        localStorage.setItem(`form_3X_report_type`, JSON.stringify(response));
        /* reportTypeObj = localStorage.getItem(`form_${this.formType}_report_type`);
        reportTypeObj.cvgStartDate = this._utilService.formatDate(response.cvgstartdate);;
        reportTypeObj.cvgEndDate = this._utilService.formatDate(response.cvgenddate);
        localStorage.setItem(`form_${formType}_report_type`,JSON.stringify(reportTypeObj)); */
        this.navigateToReportSpecificAllTransactions(true, e, formType);
      }
    }),
    error =>{
      console.error('There was an issue retrieving coverage dates for this report. ', error);
      return of(false);
    };
    // return of(false);
  }


  /**
   * This method should return the form type (F3X, F99 etc.) based on the metadata
   * @param form 
   */
  private getFormType(form: any):string {
    
    //returning hardcoded F3X for now but logic should be added to this method later on.
    return "3X";
    
  }
}
