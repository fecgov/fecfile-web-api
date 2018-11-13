import { Component, EventEmitter, OnInit, Output, Input } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { form99 } from '../../interfaces/FormsService/FormsService';
import { MessageService } from '../../services/MessageService/message.service';

@Component({
  selector: 'app-preview',
  templateUrl: './preview.component.html',
  styleUrls: ['./preview.component.scss']
})
export class PreviewComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public committee_details: any = {};
  public type_selected: string = '';
  public form_type: string = '';
  public date_stamp: Date = new Date();
  public form_details: form99;
  private _subscription: Subscription;

  private _step: string = '';

  constructor(
    private _activatedRoute: ActivatedRoute,
    private _messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.form_type = this._activatedRoute.snapshot.paramMap.get('form_id');

    this._subscription =
      this._messageService
        .getMessage()
        .subscribe(res => {
          this._step = res.step;

          this.form_details = res.data;

          this.committee_details = JSON.parse(localStorage.getItem('committee_details'));

          if(this.form_type === '99') {
            if(typeof this.form_details !== 'undefined') {
              if(typeof this.form_details.reason !== 'undefined') {
                this.type_selected = this.form_details.reason;
              }              
            }
          }
        });
  }

  ngDoCheck(): void {
    if(!this.form_details) {
      if(localStorage.getItem(`form_${this.form_type}_details`) !== null) {
        this.form_details = JSON.parse(localStorage.getItem(`form_${this.form_type}_details`));
        if(this.form_type === '99') {
          if(!this.type_selected) {
            this.type_selected = this.form_details.reason;
          } 
        }
      }
    }
  }

  public goToPreviousStep(): void {
      setTimeout(() => {
        localStorage.setItem(`form_${this.form_type}_details`, JSON.stringify(this.form_details));
      }, 100);
          
      this.status.emit({
        form: {},
        direction: 'previous',
        step: 'step_2',
        previousStep: this._step
      });
  }

  public goToNextStep(): void {
      setTimeout(() => {
        localStorage.setItem(`form_${this.form_type}_details`, JSON.stringify(this.form_details));
      }, 100);

      this.status.emit({
        form: 'preview',
        direction: 'next',
        step: 'step_4',
        previousStep: this._step
      });
  }

}
