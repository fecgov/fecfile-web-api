import { ActivatedRoute, Router } from '@angular/router';
import { ReportsService } from 'src/app/reports/service/report.service';
import { DecimalPipe } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder, FormControl, Validators } from '@angular/forms';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { validateAmount } from '../../../shared/utils/forms/validation/amount.validator';
import { mustMatch } from '../../../shared/utils/forms/validation/must-match.validator';
import { DialogService } from '../../../shared/services/DialogService/dialog.service';
import { ConfirmModalComponent, ModalHeaderClassEnum } from '../../../shared/partials/confirm-modal/confirm-modal.component';

@Component({
  selector: 'app-cash-on-hand',
  templateUrl: './cash-on-hand.component.html',
  styleUrls: ['./cash-on-hand.component.scss']
})
export class CashOnHandComponent implements OnInit {

  form: FormGroup;
  editMode :boolean = false;
  editWarningAlreadyShown: boolean = false;
  transactionalForms: string[] = ["3X", "24", '3L'];
  

  constructor(public activeModal: NgbActiveModal,
    private _fb: FormBuilder,
    private _decimalPipe: DecimalPipe, 
    private _activatedRoute: ActivatedRoute,
    private _router: Router,
    private _reportService: ReportsService, 
    private _dialogService: DialogService) { }

  ngOnInit() {
    this.initForm();
    this.populateForm();
  }
  

  private initForm() {
    this.form = this._fb.group({
      amount: new FormControl(null, [Validators.required, validateAmount()]),
      year: new FormControl(null, [Validators.required, Validators.min(1900), Validators.max(2099)])
    });
  }

  closeModal() {
    this.activeModal.dismiss();
  }

  save() {
    this._reportService.updateCashOnHand(this.form.value).subscribe(res=>{
      if(res){
        this.activeModal.close();
        this.navigateToTargetScreen();
      }
    })
  }


  private navigateToTargetScreen() {
    // const formType = this._activatedRoute.snapshot.paramMap.get('form_id');
    const reportId = this._activatedRoute.snapshot.queryParams.reportId;
    // if(reportId){
    //   this._router.navigate(['./'],{relativeTo: this._activatedRoute, queryParamsHandling:'preserve'});
    // }
    this._router.navigate(['/dashboard']);
  }

  populateForm() {
    this._reportService.getCurrentCashOnHand().subscribe(res => {
      if(res){
        if(res.amount){
          this.form.controls['amount'].patchValue(this._decimalPipe.transform(res.amount, '.2-2'));
        }
        if(res.year){
          this.form.controls['year'].patchValue(res.year);
        }

        if(res.amount || res.year){
          this.editMode = true;
        }
      }
    });
  }

  onAmountBlur(event: any){
    if(event && event.target && event.target.value){
      let amount = event.target.value;
      amount = amount.replace(/,/g, ``);
      this.form.controls['amount'].patchValue(this._decimalPipe.transform(amount, '.2-2'));
    }
  }

  showWarning(){
    const warningMessage = 'Editing the First Time Cash on Hand may impact reports that have already been filed or saved. If you edit the Cash on Hand it will automatically amend any filed reports.';
    if(this.editMode && !this.editWarningAlreadyShown){
      this._dialogService.confirm(warningMessage,ConfirmModalComponent,'Warning!', false,ModalHeaderClassEnum.warningHeader).then(res=>{
        //do nothing.
      });
      this.editWarningAlreadyShown = true;
    }
  }

}
