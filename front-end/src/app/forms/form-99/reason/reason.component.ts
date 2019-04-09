import { Component, EventEmitter, ElementRef, Input, OnInit, Output, Renderer2, ViewEncapsulation, ViewChild } from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormGroup, FormControl, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { QuillEditorComponent } from 'ngx-quill';
import { environment } from '../../../../environments/environment';
import { htmlLength } from '../../../shared/utils/forms/html-length.validator';
import { form99 } from '../../../shared/interfaces/FormsService/FormsService';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { MessageService } from '../../../shared/services/MessageService/message.service';
import { DialogService } from '../../../shared/services/DialogService/dialog.service';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'f99-reason',
  templateUrl: './reason.component.html',
  styleUrls: ['./reason.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class ReasonComponent implements OnInit {

  @Output() status: EventEmitter<any> = new EventEmitter<any>();
  @Input('editor') editor: any;
  @ViewChild('fileInput') fileInput: ElementRef;

  public frmReason: FormGroup;
  public reasonType: string = null;
  public reasonFailed: boolean = false;
  public reasonHasInvalidHTML: boolean = false;
  public typeSelected: string = null;
  public lengthError: boolean = false;
  public isValidReason: boolean = false;
  public reasonText: string = '';
  public isFiled: boolean = false;
  public characterCount: number = 0;
  public formSaved: boolean = false;
  public hideText: boolean = false;
  public showValidateBar: boolean = false;
  public file: any = null;
  public notValidPdf: boolean = false;
  public validFile: boolean = true;
  public showFileDeleteButton: boolean=false;
  public notCorrectPdfSize: boolean=false;
  public closeResult: string = '';
  public PdfUploaded: boolean = false;
  public PdfDeleted: boolean = false;
  public editorMax: number = 20000;
  public reasonTextArea: string = ''; // text area html
  public reasonTextContent: string = ''; // text area text only 

  private _printPriviewPdfFileLink: string ='';

  private _form99Details: any = {}
  private _formType: string = '';
  private _formSaved: boolean = false;
  private _formSubmitted: boolean = false;

  constructor(
    private _fb: FormBuilder,
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _formsService: FormsService,
    private _renderer: Renderer2,
    private _messageService: MessageService,
    private _dialogService: DialogService,
    private _modalService: NgbModal
  ) {
    this._messageService.clearMessage();
  }

  ngOnInit(): void {
    this._formType = this._activatedRoute.snapshot.paramMap.get('form_id');

    this._form99Details = JSON.parse(localStorage.getItem(`form_${this._formType}_details`));

    if(this._form99Details) {
      if(this._form99Details.text) {

        if (this._form99Details.reason){
           this.typeSelected=this._form99Details.reason;
        }

        this.frmReason = this._fb.group({
          reasonText: [this._form99Details.text, [
            Validators.required,
            Validators.maxLength(this.editorMax)
          ]],
          file: ['']
        });
       } else {
        this.frmReason = this._fb.group({
          reasonText: ['', [
            Validators.required,
            Validators.maxLength(this.editorMax)
          ]],
          file: ['']
        });
       }
    } else {
      this.frmReason = this._fb.group({
        reasonText: ['', [
          Validators.required,
          Validators.maxLength(this.editorMax),
          Validators.pattern(/^$|\s+/)
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

      this.characterCount = this._countCharacters(text);
    } else if(this.frmReason.get('reasonText').value.length === 0) {
      let text: string = this.frmReason.get('reasonText').value;

      this.characterCount = this._countCharacters(text);
    }
  }

  public reasonTextEmpty(): boolean {
    if (!this.frmReason.controls.reasonText.value.replace(/(\s)/g, '').length) {
      return true;
    }
    return false;
  }


  public setFile(e): void {
    if(e.target.files.length === 1) {
       this.file = e.target.files[0];
       if (this.file.name.includes('.pdf')) {
         let fileNameObj: any = {
           'fileName': this.file.name
         };

         if (this.file.size > 33554432) {
          this.notCorrectPdfSize=true;
         } else {
          this.notCorrectPdfSize=false;
         }

         localStorage.setItem(`form_${this._formType}_file`, JSON.stringify(fileNameObj));
         this.notValidPdf=false;
         this.validFile=true;
         this.showFileDeleteButton=true;
         this._form99Details.filename = this.file.name;
         this.PdfUploaded=true;
         this.PdfDeleted=false;
      } else {
        this.notValidPdf=true;
        this.validFile=false;
        this.file=null;
        this.notCorrectPdfSize=false;
        this.PdfUploaded=false;
      }
    } else {
      let fileNameObj: any = {
       'fileName': ''
      };
      localStorage.setItem(`form_${this._formType}_file`, JSON.stringify(fileNameObj));
      this.notValidPdf=true;
      this.validFile=false;
      this.file=null;
      this.showFileDeleteButton=false;
      this.fileInput.nativeElement.value = '';
      this._form99Details.filename = '';
      this.PdfUploaded = false;
      localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));
    }
  }

  /**
   * Validates the reason form.
   *
   */
  public doValidateReason() {  
    if (this.reasonTextArea.length >= 1) {
      if (this._checkUnsupportedHTML(this.reasonTextArea)) {
        if (!this._validateForSpaces(this.reasonTextArea)) {
          let formSaved: any = {
            'form_saved': this.formSaved
          };
          this.reasonFailed = false;
          this.isValidReason = true;

          this._form99Details = JSON.parse(localStorage.getItem(`form_${this._formType}_details`)); 
          this._form99Details.text = this.reasonTextArea;

          setTimeout(() => {
            localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));

            localStorage.setItem(`form_${this._formType}_saved`, JSON.stringify(formSaved));
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
            data: this._form99Details,
            previousStep: 'step_3'
          });
        } else {
          this.frmReason.controls['reasonText'].setValue('');

          this.reasonFailed = true;

          window.scrollTo(0, 0);
        }
      } else {
        this.frmReason.controls['reasonText'].setValue('');

        this.reasonFailed = true;

        window.scrollTo(0, 0);        
      }
    } else {
      this.reasonFailed = true;
      this.isValidReason = false;

      this.status.emit({
        form: this.frmReason,
        direction: 'next',
        step: 'step_2',
        previousStep: ''
      });

      window.scrollTo(0, 0);
      return;
    }
  }

  /**
   * Executed when a user types in text into the editor area.
   *
   * @param      {Object}  e       The event object.
   */
  public editorChange(e): void {
    this.reasonText = e.target.textContent;

    if (this.reasonText.length >= 1) {

      this.reasonTextArea = e.target.innerText; 

      if (this._checkUnsupportedHTML(this.reasonTextArea)) {
        this.reasonHasInvalidHTML = true;

        this.frmReason.controls['reasonText'].setValue('');
      } else {
        this.reasonHasInvalidHTML = false;

        if (!this._validateForSpaces(this.reasonText)) {
          this.frmReason.controls['reasonText'].setValue(this.reasonTextArea);

          this.showValidateBar = false;
          this.reasonFailed = false;

          this.hideText = true;
          this.formSaved = false;

          this._messageService
            .sendMessage({
              'validateMessage': {
                'validate': {},
                'showValidateBar': false
              }
            });         
        } else {
          this.frmReason.controls['reasonText'].setValue('');

          this.reasonFailed = true;
        }
      }
    } else {
      this.reasonTextArea = e.target.textContent;

      this.frmReason.controls['reasonText'].setValue('');

      this.reasonHasInvalidHTML = false;

      this.reasonFailed = true;

      this._messageService
        .sendMessage({
          'validateMessage': {
            'validate': {},
            'showValidateBar': false
          }
        });       
    }
  }  

  /**
   * Inserts HTML for button clicked in the toolbar.
   *
   * @param      {Object}  e       The event object.
   */
  public insertHTML(e: any): void {
    if (typeof e === 'object') {
      try {
        const htmlTagType: string = e.currentTarget.getAttribute('data-command');

        window.document.execCommand(htmlTagType, true);    
      } catch(error) {
        console.log('There was an error.');
        console.log('error: ', error);
      }
    }
  } 

  /**
   * Removes any HTML from pasted content into editor.
   *
   * @param      {Object}  e       The event object.
   */
  public removeHTML(e: any): void {
    e.preventDefault();

    if (typeof e === 'object') {
      try {
        const plainText: string = e.clipboardData.getData('text/plain');

        window.document.execCommand('insertHTML', false, plainText); 
      } catch (error) {
        console.log('error: ', error);
      }
    }
  }

  /**
   * Counts the number of characters in the editor.
   *
   * @param      {string}  text    The text
   * @return     {number}  Number of characters.
   */
  private _countCharacters(text: string): number {
    const regex: any = /(<([^>]+)>)/ig;
    let characterCount: number = text.replace(regex, '').length || 0;

    return characterCount;
  }

  /**
   * Validates text area for just spaces or new line characters entered.
   *
   * @param      {string}   text    <ifrThe text.
   * @return     {boolean}  The result.
   */
  private _validateForSpaces(text: string): boolean {
    const regex: any = /^\s*$/;

    if (regex.test(text)) {
      return true;
    }

    return false;
  }

  /**
   * Checks for unsupported markup in reason text.
   *
   * @param      {string}   text    The text.
   * @return     {boolean}  Indicates if there is invalid markup or not.
   */
  private _checkUnsupportedHTML(text: string): boolean {
    const hasHTMLTags: any = /((<(\/?|\!?)\w+>)|(<\w+.*?\w="(.*?)")>|(<\w*.*\/>))/gm;

    if (hasHTMLTags.test(text)) {
      const htmlTagsWhiteList: any = /(<(\/?|\!?)(script|script.*?src="(.*?)"|iframe|iframe.*?src="(.*?)"|link|style|table|thead|tbody|th|tr|td|img|img.*?src="(.*?)"|fieldset|form|input|textarea|select|option|a|a.*?href="(.*?)"|progress|noscript|audio|video)(\s*\/*)>)/gm;

      if (htmlTagsWhiteList.test(text)) {
        return true;
      } else {
        return false;
      } 
    }

    return false;
  }

  /**
   * Toggles a tooltip.
   *
   * @param      {<type>}  tooltip  The tooltip
   */
  public toggleToolTip(tooltip): void {
    if (tooltip.isOpen()) {
      tooltip.close();
    } else {
      tooltip.open();
    }
  }


  public removeFile(modalId: string): void {
    this._modalService.open(modalId);
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
    if(this.frmReason.valid) {
      if (this.frmReason.get('reasonText').value.length >= 1) {
        let formSaved: boolean = JSON.parse(localStorage.getItem('form_99_saved'));
        this._form99Details = JSON.parse(localStorage.getItem('form_99_details'));

        this._form99Details.text = this.reasonTextArea;

        this._form99Details.file='';

        if (this.file !== null){
          this._form99Details.file=this.file;
          this._form99Details.filename=this.file.name;
        }
        localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));

        this.hideText = true;

        this.showValidateBar = false;

        if (this.file !== null){
          this._form99Details.file=this.file;
          this._formsService
          .saveForm({}, this.file, this._formType)
          .subscribe(res => {
            if(res) {
              this._form99Details.id = res.id;
              this._form99Details.org_fileurl = res.file;

              localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));

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
        console.log('if file === null');
        this._formsService
        .saveForm({}, {}, this._formType)
        .subscribe(res => {
          if(res) {

            this._form99Details.id = res.id;

            localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));

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

    this._form99Details = JSON.parse(localStorage.getItem('form_99_details'));

    this.reasonText = this.frmReason.get('reasonText').value;
    this._form99Details.text = this.frmReason.get('reasonText').value;

    localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));

    this.showValidateBar = true;

    this._formsService
      .validateForm({}, this._formType)
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

  public printPreview () {
    console.log('Reason screen printPreview: step-I ');
    if(this.frmReason.valid) {
       console.log('Reason screen printPreview: step -II');

      if (this.frmReason.get('reasonText').value.length >= 1) {
        let formSaved: boolean = JSON.parse(localStorage.getItem('form_99_saved'));
        this._form99Details = JSON.parse(localStorage.getItem('form_99_details'));

        this.reasonText = this.frmReason.get('reasonText').value;
        this._form99Details.text = this.reasonText;

        this._form99Details.file='';

        if (this.file !== null){
          this._form99Details.file=this.file;
          this._form99Details.filename=this.file.name;
        }

        localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));

        this.hideText = true;

        this.showValidateBar = false;


        if (this.file !== null){
          console.log('Reason screen printPreview: step -IV');
         this._formsService
          .PreviewForm_ReasonScreen({}, this.file, this._formType)
          .subscribe(res => {
            if(res) {
              console.log('Reason screen printPreview: res: ', res);
              this._form99Details.id = res.id;
              localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));
              // success
              this.formSaved = true;
              let formSavedObj: any = {
                'saved': this.formSaved
              };
              localStorage.setItem('form_99_saved', JSON.stringify(formSavedObj));
              window.open(localStorage.getItem('form_99_details.printpriview_fileurl'), '_blank');
            }
          },
          (error) => {
            console.log('error: ', error);
          });
        }
        else
        {
          console.log('Reason screen printPreview: step -V');
          this._formsService
          .PreviewForm_ReasonScreen({}, {}, this._formType)
          .subscribe(res => {
            if(res) {
              this._form99Details.id = res.id;
              localStorage.setItem('form_99_details', JSON.stringify(this._form99Details));
              // success
              this.formSaved = true;
              let formSavedObj: any = {
                'saved': this.formSaved
              };
              localStorage.setItem('form_99_saved', JSON.stringify(formSavedObj));
              window.open(localStorage.getItem('form_99_details.printpriview_fileurl'), '_blank');

            }
          },
          (error) => {
            console.log('error: ', error);
          });
        }

      }
    }
  }
  public deletePDF( message: string,  modalId:string): void {
    if (message==="Yes"){
      this.file = null;
      this.notValidPdf=false;

      this._form99Details.filename = '';
      localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));
    }
    //this._modalService.close(modalId);
 }

 public open(content): void{
  this._modalService
    .open(content, {ariaLabelledBy: 'modal-basic-title'})
    .result
    .then((result) => {
      this.closeResult = `Closed with: ${result}`;
  }, (reason) => {
    this.closeResult = `Dismissed ${this._getDismissReason(reason)}`;
  });
}

 private _getDismissReason(reason: any): string {
  if (reason === "Yes click") {
    this.PdfDeleted=true;
    this.file = null;
    this.notValidPdf=false;
    this.PdfUploaded = false;
    this._form99Details.filename = '';
    localStorage.setItem(`form_${this._formType}_details`, JSON.stringify(this._form99Details));
  }
  else if (reason === ModalDismissReasons.ESC) {
    return 'by pressing ESC';
  } else if (reason === ModalDismissReasons.BACKDROP_CLICK) {
    return 'by clicking on a backdrop';
  } else {
    return  `with: ${reason}`;
  }
 }
}
