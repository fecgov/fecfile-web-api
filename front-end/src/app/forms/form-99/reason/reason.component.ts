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
  public reasonType: string = '';
  public reasonFailed: boolean = false;
  public typeSelected: string = '';
  public lengthError: boolean = false;
  public isValidReason: boolean = false;
  public reasonText: string = '';
  public isFiled: boolean = false;
  public characterCount: number = 0;
  public formSaved: boolean = false;

  private _form_99_details: form99 = JSON.parse(localStorage.getItem('form_99_details'));
  private _editorMax: number = 20000;
  private _form_type: string = '';

  public editorConfig: AngularEditorConfig = {
    editable: true,
    spellcheck: true,
    height: '25rem',
    minHeight: '5rem',
    placeholder: 'Enter text here...',
    translate: 'no',
    uploadUrl: 'v1/images', // if needed
    customClasses: [ // optional
      {
        name: "quote",
        class: "quote",
      },
      {
        name: 'redText',
        class: 'redText'
      },
      {
        name: "titleText",
        class: "titleText",
        tag: "h1",
      },
    ]
  };


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

    if(this._form_99_details) {
      if(this._form_99_details.text) {
        this.typeSelected = this._form_99_details.reason;

        this.frmReason = this._fb.group({
          reasonText: [this._form_99_details.text, [
            Validators.required,
            htmlLength(this._editorMax)
          ]]
        });
       } else {
        this.frmReason = this._fb.group({
          reasonText: ['', [
            Validators.required,
            htmlLength(this._editorMax)
          ]]
        });
       }
    } else {
      this.frmReason = this._fb.group({
        reasonText: ['', [
          Validators.required,
          htmlLength(this._editorMax)
        ]]
      });
    }
  }

  ngDoCheck(): void {
    let form_99_details: any = JSON.parse(localStorage.getItem('form_99_details'));

    if(form_99_details) {
      this.typeSelected = form_99_details.reason;
    }

    if (this.frmReason.get('reasonText').value.length >= 1) {
      let text: string = this.frmReason.get('reasonText').value.replace(/<[^>]*>/g, '');
      text = text.replace(/(&nbsp;)/g, ' ');

      this.characterCount = text.length;
    } else if(this.frmReason.get('reasonText').value.length === 0) {
      let text: string = this.frmReason.get('reasonText').value.replace(/<[^>]*>/g, '');
      text = text.replace(/(&nbsp;)/g, ' ');

      this.characterCount = text.length;
    }
  }

  /**
   * Validates the reason form.
   *
   */
  public doValidateReason() {
    if (this.frmReason.get('reasonText').value.length >= 1) {
        this.reasonFailed = false;
        this.isValidReason = true;

        this._form_99_details = JSON.parse(localStorage.getItem('form_99_details'));

        this.reasonText = this.frmReason.get('reasonText').value;
        this._form_99_details.text = this.frmReason.get('reasonText').value;

        localStorage.setItem('form_99_details', JSON.stringify(this._form_99_details));

        this.status.emit({
          form: this.frmReason,
          direction: 'next',
          step: 'step_3',
          previousStep: 'step_2'
        });

        this._messageService.sendMessage({
          data: this.frmReason.get('reasonText').value,
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

  public previousStep(): void {
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
  public saveForm() {
    if(this.frmReason.valid) {
      if (this.frmReason.get('reasonText').value.length >= 1) {
        this._form_99_details = JSON.parse(localStorage.getItem('form_99_details'));

        this.reasonText = this.frmReason.get('reasonText').value;
        this._form_99_details.text = this.frmReason.get('reasonText').value;

        localStorage.setItem('form_99_details', JSON.stringify(this._form_99_details));

        this._formsService
          .saveForm({}, this._form_type)
          .subscribe(res => {
            if(res) {
              this.formSaved = true;
            }
          },
          (error) => {
            console.log('error: ', error);
          })
      }
    }
  }

  public validateForm(): void {
    let type: string = localStorage.getItem('form99-type');

    this._form_99_details = JSON.parse(localStorage.getItem('form_99_details'));

    this.reasonText = this.frmReason.get('reasonText').value;
    this._form_99_details.text = this.frmReason.get('reasonText').value;

    localStorage.setItem('form_99_details', JSON.stringify(this._form_99_details));

    this._formsService
      .validateForm({}, this._form_type)
      .subscribe(res => {
        if(res) {
            this._messageService
              .sendMessage({
                'validate': environment.validateSuccess
              });
        }
      },
      (error) => {
        this._messageService
          .sendMessage({
            'validate': error.error
          });
      });
  }

  public printPreview(): void {
    this.status.emit({
      form: {},
      direction: 'next',
      step: 'step_3'
    });
  }

  /*public canDeactivate(): Observable<boolean> | boolean {
      if (!this.formSaved && this.frmReason.dirty) {

          return this._dialogService.confirm('Discard changes for this form?');
      }
      return true;
  }*/
}
