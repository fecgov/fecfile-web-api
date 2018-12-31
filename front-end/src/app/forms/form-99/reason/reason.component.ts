import { Component, EventEmitter, Input, OnInit, Output, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { QuillEditorComponent } from 'ngx-quill';
import { AngularEditorConfig } from '@kolkov/angular-editor';
import { environment } from '../../../../environments/environment';
import { htmlLength } from '../../../shared/utils/forms/html-length.validator';
import { form99 } from '../../../shared/interfaces/FormsService/FormsService';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { DialogService } from '../../../shared/services/DialogService/dialog.service';

@Component({
  selector: 'app-reason',
  templateUrl: './reason.component.html',
  styleUrls: ['./reason.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ReasonComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input('editor') editor: any;

  public frmReason: FormGroup;
  public reasonType: string = null;
  public reasonFailed: boolean = false;
  public typeSelected: string = null;
  public lengthError: boolean = false;
  public isValidReason: boolean = false;
  public reasonText: string = '';
  public isFiled: boolean = false;
  public characterCount: number = 0;
  public formSaved: boolean = false;
  public hideText: boolean = false;
  public showValidateBar: boolean = false;

  private _form_99_details: any = {}
  private _editorMax: number = 20000;
  private _form_type: string = '';
  private _form_saved: boolean = false;
  public file: any = null;
  private _form_submitted: boolean = false;
  public _not_valid_pdf: boolean = false;
  public _valid_file: boolean = true;
  public _show_file_delete_button: boolean=false;
  
  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _formsService: FormsService,
    private _messageService: MessageService,
    private _dialogService: DialogService
  ) {
    this._messageService.clearMessage();
  }

  ngOnInit(): void {
    this._form_type = this._activatedRoute.snapshot.paramMap.get('form_id');
    
    this._form_99_details = JSON.parse(localStorage.getItem(`form_${this._form_type}_details`));

    if(this._form_99_details) {  
      if(this._form_99_details.text) {

        if (this._form_99_details.reason){
           this.typeSelected=this._form_99_details.reason; 
        }

        this.frmReason = this._fb.group({
          reasonText: [this._form_99_details.text, [
            Validators.required,
            htmlLength(this._editorMax)
          ]],
          file: ['']
        });
       } else {
        this.frmReason = this._fb.group({
          reasonText: ['', [
            Validators.required,
            htmlLength(this._editorMax)
          ]],
          file: ['']
        });
       }
    } else {
      this.frmReason = this._fb.group({
        reasonText: ['', [
          Validators.required,
          htmlLength(this._editorMax)
        ]],
        file: ['']
      });
    }
  }

  ngDoCheck(): void {
    let form_99_details: any = {};

    if(localStorage.getItem('form_99_details') !== null) {
      form_99_details = JSON.parse(localStorage.getItem('form_99_details'));
    }

    if(form_99_details) {
      this.typeSelected = form_99_details.reason;
    }

    if (this.frmReason.get('reasonText').value.length >= 1) {
      let text: string = this.frmReason.get('reasonText').value;

      this.characterCount = text.length;
    } else if(this.frmReason.get('reasonText').value.length === 0) {
      let text: string = this.frmReason.get('reasonText').value;

      this.characterCount = text.length;
    }
  }

  /**
   * Sets the file.
   *
   * @param      {Object}  e The event object.
   */
  public setFile(e): void {
    if(e.target.files.length === 1) {
       this.file = e.target.files[0];
       if (this.file.name.includes('.pdf')){
         console.log("pdf uploaded");
         localStorage.setItem(`form_${this._form_type}_file`, this.file.name);
         this._not_valid_pdf=false;
         this._valid_file=true;
         this._show_file_delete_button=true;
      }
      else {
        this._not_valid_pdf=true;
        this._valid_file=false;
        this.file=null;
        this._show_file_delete_button=true;
      }


    } else {
      localStorage.setItem(`form_${this._form_type}_file`, '');
    }
    console.log ('_valid_file:',this._valid_file);
  }

  /**
   * Validates the reason form.
   *
   */
  public doValidateReason() {
    if (this.frmReason.get('reasonText').value.length >= 1) {
        let formSaved: any = {
          'form_saved': this.formSaved
        };
        this.reasonFailed = false;
        this.isValidReason = true;

        this._form_99_details = JSON.parse(localStorage.getItem(`form_${this._form_type}_details`));

        this.reasonText = this.frmReason.get('reasonText').value;
        this._form_99_details.text = this.frmReason.get('reasonText').value;

        if (this.frmReason.get('file').value){
          this._form_99_details.file=this.frmReason.get('file').value;  
        }

        setTimeout(() => {
          localStorage.setItem(`form_${this._form_type}_details`, JSON.stringify(this._form_99_details));

          localStorage.setItem(`form_${this._form_type}_saved`, JSON.stringify(formSaved));
        }, 100);
        
        this.saveForm();

        this.hideText = true;

        this.showValidateBar = false; 

        this.hideText = true;
        this.formSaved = false;        

        this._messageService
          .sendMessage({
            'validateMessage': {
              'validate': '',
              'showValidateBar': false                  
            }            
          });          

        this.status.emit({
          form: this.frmReason,
          direction: 'next',
          step: 'step_3',
          previousStep: 'step_2'
        });

        this._messageService.sendMessage({
          data: this._form_99_details,
          previousStep: 'step_3'
        });
    } else {
      this.reasonFailed = true;
      this.isValidReason = false;

      this.status.emit({
        form: this.frmReason,
        direction: 'next',
        step: 'step_2',
        previousStep: ''
      });
      return;
    }
  }

  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }      
  }  

  
  public removeFile(): void {
    this.file = null;
    this._not_valid_pdf=false;
  }

  /**
   * Goes to the previous step.
   */
  public previousStep(): void {
    this.hideText = true;
    this.formSaved = false;

    this.showValidateBar = false;

    this._messageService
      .sendMessage({
        'validateMessage': {
          'validate': {},
          'showValidateBar': false                  
        }            
      });    
    
    this.status.emit({
      form: {},
      direction: 'previous',
      step: 'step_1'
    });
  }

  /**
   * Saves the form when the save button is clicked.
   *
   */
  public saveForm () {
    console.log('saveForm: ');
    if(this.frmReason.valid) {
      if (this.frmReason.get('reasonText').value.length >= 1) {
        let formSaved: boolean = JSON.parse(localStorage.getItem('form_99_saved'));
        this._form_99_details = JSON.parse(localStorage.getItem('form_99_details'));

        this.reasonText = this.frmReason.get('reasonText').value;
        this._form_99_details.text = this.reasonText;

        this._form_99_details.file='';

        if (this.file !== null){
          this._form_99_details.file=this.file;
          this._form_99_details.filename=this.file.name;
        }
        localStorage.setItem('form_99_details', JSON.stringify(this._form_99_details));

        this.hideText = true;

        this.showValidateBar = false;
        console.log('this.file: ',this.file);
        
        if (this.file !== null){
          this._form_99_details.file=this.file;
          this._formsService
          .saveForm({}, this.file, this._form_type)
          .subscribe(res => {
            if(res) {
              console.log('res: ', res);

              this._form_99_details.id = res.id;

              localStorage.setItem('form_99_details', JSON.stringify(this._form_99_details));
              
              // success
              this.formSaved = true;

              let formSavedObj: any = {
                'saved': this.formSaved
              };
              localStorage.setItem('form_99_saved', JSON.stringify(formSavedObj));
            }
          },
          (error) => {
            console.log('error: ', error);
          });          
      }
      else {
        this._formsService
        .saveForm({}, {}, this._form_type)
        .subscribe(res => {
          if(res) {
            console.log('res: ', res);

            this._form_99_details.id = res.id;

            localStorage.setItem('form_99_details', JSON.stringify(this._form_99_details));
            
            // success
            this.formSaved = true;

            let formSavedObj: any = {
              'saved': this.formSaved
            };
            localStorage.setItem('form_99_saved', JSON.stringify(formSavedObj));
          }
        },
        (error) => {
          console.log('error: ', error);
        });         
      }
    }
  }
  }
  /**
   * Validates the entire form.
   */
  public validateForm(): void {
    let type: string = localStorage.getItem('form99-type');

    this._form_99_details = JSON.parse(localStorage.getItem('form_99_details'));

    this.reasonText = this.frmReason.get('reasonText').value;
    this._form_99_details.text = this.frmReason.get('reasonText').value;

    localStorage.setItem('form_99_details', JSON.stringify(this._form_99_details));

    this.showValidateBar = true;

    this._formsService
      .validateForm({}, this._form_type)
      .subscribe(res => {
        if(res) {
            this._messageService
              .sendMessage({
                'validateMessage': {
                  'validate': environment.validateSuccess,
                  'showValidateBar': true                  
                }
              });
        }
      },
      (error) => {
        this._messageService
          .sendMessage({
            'validateMessage': {
              'validate': error.error,
              'showValidateBar': true                  
            }            
          });
      });
  }

  /**
   * Hides the validate bar if the textarea changed.
   */
  public updateValidation(): void {
    this.showValidateBar = false;

    this.hideText = true;
    this.formSaved = false;      

    this._messageService
      .sendMessage({
        'validateMessage': {
          'validate': {},
          'showValidateBar': false                  
        }            
      });       
  }



  /*public printPreview(): void {
    this.status.emit({
      form: {},
      direction: 'next',
      step: 'step_3'
    });
  }*/

  /*public canDeactivate(): Observable<boolean> | boolean {
      if (!this.formSaved && this.frmReason.dirty) {

          return this._dialogService.confirm('Discard changes for this form?');
      }
      return true;
  }*/
  public printPreview () {
    console.log('Reason screen printPreview: ');
    if(this.frmReason.valid) {
      if (this.frmReason.get('reasonText').value.length >= 1) {
        let formSaved: boolean = JSON.parse(localStorage.getItem('form_99_saved'));
        this._form_99_details = JSON.parse(localStorage.getItem('form_99_details'));

        this.reasonText = this.frmReason.get('reasonText').value;
        this._form_99_details.text = this.reasonText;

        this._form_99_details.file='';

        if (this.file !== null){
          this._form_99_details.file=this.file;
          this._form_99_details.filename=this.file.name;
        }
        
        localStorage.setItem('form_99_details', JSON.stringify(this._form_99_details));

        this.hideText = true;

        this.showValidateBar = false;
        console.log('Reason screen printPreview: this.file: ',this.file);
        
        this._formsService
          .PreviewForm_ReasonScreen({}, this.file, this._form_type)
          .subscribe(res => {
            if(res) {
              console.log('Reason screen printPreview: res:=', res);

              this._form_99_details.id = res.id;

              localStorage.setItem('form_99_details', JSON.stringify(this._form_99_details));
              
              // success
              this.formSaved = true;

              let formSavedObj: any = {
                'saved': this.formSaved
              };
              localStorage.setItem('form_99_saved', JSON.stringify(formSavedObj));
            }
          },
          (error) => {
            console.log('error: ', error);
          });          
      }
    }
  }
}
