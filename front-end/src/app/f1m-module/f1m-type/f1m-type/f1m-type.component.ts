import { Component, OnInit, Output, EventEmitter, ChangeDetectionStrategy } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-f1m-type',
  templateUrl: './f1m-type.component.html',
  styleUrls: ['./f1m-type.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class F1mTypeComponent implements OnInit {

  @Output() changeStep: EventEmitter<any> = new EventEmitter<any>();

  form: FormGroup;

  constructor(private _fb : FormBuilder) { }

  get committeeType() {
    if (this.form && this.form.get('committeeType')) {
      return this.form.get('committeeType').value;
    }
    return null;
  }

  ngOnInit() {
    this.initForm();
  }

  public next(type:string){
    if(type){
      this.changeStep.emit({step:'step_2', type, committeeType: this.committeeType});
    }
  }


  public initForm(){
    this.form = this._fb.group({
      committeeType: ['', Validators.required]
    });
  }

}
