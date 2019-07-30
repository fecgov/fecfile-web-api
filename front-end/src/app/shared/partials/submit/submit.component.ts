import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, Router, NavigationEnd } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { MessageService } from '../../services/MessageService/message.service'
import { ReportTypeService } from '../../../forms/form-3x/report-type/report-type.service';
@Component({
  selector: 'app-submit',
  templateUrl: './submit.component.html',
  styleUrls: ['./submit.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class SubmitComponent implements OnInit {

  public form_type: string = '';
  public FEC_Id: string = '#####';
  constructor(
    private _activatedRoute: ActivatedRoute,
    private _router: Router,
    private _messageService: MessageService,
    private _reportTypeService: ReportTypeService,
  ) { }

  ngOnInit() {
    
    this.form_type = this._activatedRoute.snapshot.paramMap.get('form_id');
    console.log("form submitted ...", this.form_type);
    
    this._messageService
      .getMessage()
      .subscribe(res => {
        console.log("SubmitComponent res =", res);
        if(res.form_submitted) {
          if (this.form_type ==='99'){
            localStorage.removeItem(`form_${this.form_type}_details`);
          } else if (this.form_type ==='3X'){
            console.log("Accessing SubmitComponent F3x submit Data Receiver API ");
            this._reportTypeService.submitForm('3X', "Submit")
            .subscribe(res => {
              if(res) {
                    console.log("Accessing SubmitComponent F3x submit res ...",res);
                    if (res['status'] === 'Accepted') {
                      this.FEC_Id = res['submissionId'];
                    }
                  }
                },
                (error) => {
                  console.log('error: ', error);
                });/*  */

            localStorage.removeItem(`form_${this.form_type}_report_type_backup`);
            localStorage.removeItem(`form_${this.form_type}_report_type`);
            localStorage.removeItem('F3X_submit_backup');
          }

          localStorage.removeItem(`form_${this.form_type}_saved`);
        } else if (this.form_type ==='3X'){
          console.log(" SubmitComponent F3X res", res); 
          console.log("Accessing SubmitComponent F3x submit Data Receiver API ");
          this._reportTypeService.submitForm('3X', "Submit")
          .subscribe(res => {
            if(res) {
                  console.log("Accessing SubmitComponent F3x submit res ...",res);
                  if (res['status'] === 'Accepted') {
                    this.FEC_Id = res['submissionId'];
                  }
                }
              },
              (error) => {
                console.log('error: ', error);
              });/*  */

          localStorage.removeItem(`form_${this.form_type}_report_type_backup`);
          localStorage.removeItem(`form_${this.form_type}_report_type`);
          localStorage.removeItem('F3X_submit_backup');
        }

      });

    this._router
      .events
      .subscribe(val => {
        if(val) {
          if(val instanceof NavigationEnd) {
            console.log("val.url = ", val.url);
            if((val.url.indexOf('/forms/form/99') === -1) || (val.url.indexOf('/forms/form/3X') === -1) || (val.url.indexOf('/forms/form/3X') === -1)) {
              this._messageService
                .sendMessage({
                  'validateMessage': {
                    'validate': {},
                    'showValidateBar': false,                
                  }            
                });                 
            }
          }
        }
      });           
  }

  public goToDashboard(): void {
    this._router.navigateByUrl('dashboard');
  }

}
