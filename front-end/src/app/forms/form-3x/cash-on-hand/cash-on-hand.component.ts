import { ReportsService } from 'src/app/reports/service/report.service';
import { DecimalPipe } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormGroup, FormBuilder, FormControl, Validators } from '@angular/forms';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { validateAmount } from '../../../shared/utils/forms/validation/amount.validator';
import { mustMatch } from '../../../shared/utils/forms/validation/must-match.validator';

@Component({
  selector: 'app-cash-on-hand',
  templateUrl: './cash-on-hand.component.html',
  styleUrls: ['./cash-on-hand.component.scss']
})
export class CashOnHandComponent implements OnInit {

  form: FormGroup;

  constructor(public activeModal: NgbActiveModal,
    private _fb: FormBuilder,
    private _decimalPipe: DecimalPipe, 
    private _reportService: ReportsService) { }

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
      }
    })
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

}
